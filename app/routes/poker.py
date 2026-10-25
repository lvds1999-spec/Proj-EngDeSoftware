import re
from flask import Blueprint, request
from werkzeug.security import generate_password_hash
from app.database import get_db
from app.utils.responses import success_response, error_response

poker_bp = Blueprint("poker", __name__, url_prefix="/poker")

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

@poker_bp.route("/status", methods=["GET"])
def status():
    """
    Endpoint de status/healthcheck da API do Poker.
    """
    return success_response(
        dados={"status": "online", "versao": "1.0.0"},
        mensagem="API do Poker operando normalmente."
    )

@poker_bp.route("/cadastro", methods=["POST"])
def cadastro():
    """
    US01 - Cadastro de jogadores (#2 e #3)
    Valida os dados de entrada, impede e-mails duplicados, protege a senha com hash seguro
    e cadastra o jogador, retornando o identificador (id) criado.
    """
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return error_response("Corpo da requisição deve ser um JSON válido.", status_code=400)

    nome = dados.get("nome")
    email = dados.get("email")
    senha = dados.get("senha")

    # 1. Validação de campos obrigatórios
    if not nome or not isinstance(nome, str) or not nome.strip():
        return error_response("O campo 'nome' é obrigatório e não pode ser vazio.", status_code=400)

    if not email or not isinstance(email, str) or not email.strip():
        return error_response("O campo 'email' é obrigatório e não pode ser vazio.", status_code=400)

    if not senha or not isinstance(senha, str) or not senha.strip():
        return error_response("O campo 'senha' é obrigatório e não pode ser vazio.", status_code=400)

    nome = nome.strip()
    email = email.strip()

    # 2. Validação de formato de e-mail
    if not EMAIL_REGEX.match(email):
        return error_response("O e-mail informado possui formato inválido.", status_code=400)

    # 3. Validação do tamanho mínimo da senha
    if len(senha) < 6:
        return error_response("A senha deve conter no mínimo 6 caracteres.", status_code=400)

    db = get_db()
    cursor = db.cursor()

    # 4. Verificação de e-mail duplicado
    cursor.execute("SELECT id FROM jogadores WHERE LOWER(email) = LOWER(?)", (email,))
    usuario_existente = cursor.fetchone()
    if usuario_existente:
        return error_response("E-mail já cadastrado.", status_code=409)

    # 5. Proteção da senha com hash seguro
    senha_hash = generate_password_hash(senha)

    # Inserção no banco de dados com a senha protegida por hash
    cursor.execute(
        "INSERT INTO jogadores (nome, email, senha) VALUES (?, ?, ?)",
        (nome, email, senha_hash)
    )
    db.commit()

    novo_id = cursor.lastrowid

    return success_response(
        dados={"id": novo_id},
        id=novo_id,
        mensagem="Jogador cadastrado com sucesso.",
        status_code=201
    )

@poker_bp.route("/partidasAbertas", methods=["GET"])
def partidas_abertas():
    """
    US09 - Consulta de partidas disponíveis (#4)
    Retorna a lista de partidas/mesas de pôquer abertas para entrada,
    mostrando id, participantes e capacidade das mesas disponíveis.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, nome, participantes, capacidade, status
        FROM partidas
        WHERE status = 'aberta' AND participantes < capacidade
        ORDER BY id ASC
    """)
    linhas = cursor.fetchall()

    resultado = [
        {
            "id": linha["id"],
            "nome": linha["nome"],
            "participantes": linha["participantes"],
            "capacidade": linha["capacidade"]
        }
        for linha in linhas
    ]

    return success_response(
        dados=resultado,
        partidas=resultado,
        mensagem="Partidas abertas recuperadas com sucesso.",
        status_code=200
    )

@poker_bp.route("/<int:id_partida>/entrar", methods=["POST"])
def entrar_partida(id_partida):
    """
    Adiciona um jogador a uma partida aberta que ainda tenha vagas.
    """
    id_jogador_param = request.args.get("idJogador")
    if not id_jogador_param or not re.fullmatch(r"[0-9]+", id_jogador_param):
        return error_response(
            "O parâmetro de consulta 'idJogador' é obrigatório e deve ser um inteiro positivo.",
            status_code=400
        )

    id_jogador = int(id_jogador_param)
    if id_jogador <= 0:
        return error_response(
            "O parâmetro de consulta 'idJogador' deve ser um inteiro positivo.",
            status_code=400
        )

    db = get_db()
    db.execute("BEGIN IMMEDIATE")

    partida = db.execute(
        "SELECT id, participantes, capacidade, status FROM partidas WHERE id = ?",
        (id_partida,)
    ).fetchone()
    if partida is None:
        db.rollback()
        return error_response("Partida não encontrada.", status_code=404)

    jogador = db.execute(
        "SELECT id FROM jogadores WHERE id = ?",
        (id_jogador,)
    ).fetchone()
    if jogador is None:
        db.rollback()
        return error_response("Jogador não encontrado.", status_code=404)

    participacao = db.execute(
        "SELECT 1 FROM participantes WHERE partida_id = ? AND jogador_id = ?",
        (id_partida, id_jogador)
    ).fetchone()
    if participacao is not None:
        db.rollback()
        return error_response("Jogador já participa desta partida.", status_code=409)

    if partida["status"] != "aberta":
        db.rollback()
        return error_response("Não é possível entrar em uma partida que não está aberta.", status_code=409)

    if partida["participantes"] >= partida["capacidade"]:
        db.rollback()
        return error_response("A partida está lotada.", status_code=409)

    db.execute(
        "INSERT INTO participantes (partida_id, jogador_id) VALUES (?, ?)",
        (id_partida, id_jogador)
    )
    db.execute(
        """
        UPDATE partidas
        SET participantes = participantes + 1
        WHERE id = ? AND status = 'aberta' AND participantes < capacidade
        """,
        (id_partida,)
    )
    db.commit()

    return success_response(
        dados={
            "idPartida": id_partida,
            "idJogador": id_jogador,
            "participantes": partida["participantes"] + 1
        },
        mensagem="Jogador entrou na partida com sucesso.",
        status_code=201
    )
