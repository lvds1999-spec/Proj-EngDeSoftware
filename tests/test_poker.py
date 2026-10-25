import sqlite3

import pytest
from werkzeug.security import check_password_hash
from app.database import get_db, init_db

# ============================================================================
# TESTES DE CADASTRO (POST /poker/cadastro)
# ============================================================================

def test_cadastro_sucesso(client):
    """
    Testa o fluxo de sucesso no cadastro de um novo jogador.
    Deve retornar status HTTP 201 e o ID criado.
    """
    payload = {
        "nome": "Carlos Silva",
        "email": "carlos.silva@poker.com",
        "senha": "senhaSegura123"
    }
    response = client.post("/poker/cadastro", json=payload)
    assert response.status_code == 201

    dados = response.get_json()
    assert dados["sucesso"] is True
    assert "id" in dados
    assert isinstance(dados["id"], int)
    assert dados["dados"]["id"] == dados["id"]
    assert "Jogador cadastrado com sucesso" in dados["mensagem"]


def test_cadastro_protege_senha_com_hash(client, app):
    """
    Testa se a senha do jogador é gravada como hash e nunca em texto puro.
    """
    senha_original = "minhaSenhaUltraSecreta"
    payload = {
        "nome": "Ana Lima",
        "email": "ana.lima@poker.com",
        "senha": senha_original
    }
    response = client.post("/poker/cadastro", json=payload)
    assert response.status_code == 201

    jogador_id = response.get_json()["id"]

    with app.app_context():
        db = get_db()
        registro = db.execute("SELECT senha FROM jogadores WHERE id = ?", (jogador_id,)).fetchone()
        assert registro is not None
        senha_banco = registro["senha"]

        # Não deve ser igual ao texto puro
        assert senha_banco != senha_original
        # Deve ser um hash válido verificável
        assert check_password_hash(senha_banco, senha_original) is True


def test_cadastro_erro_corpo_invalido(client):
    """
    Testa envio de corpo de requisição vazio ou que não seja JSON.
    Deve retornar status HTTP 400.
    """
    response = client.post(
        "/poker/cadastro",
        data="não é um json",
        content_type="text/plain"
    )
    assert response.status_code == 400
    dados = response.get_json()
    assert dados["sucesso"] is False


@pytest.mark.parametrize("payload_invalido,campo_esperado", [
    ({"email": "teste@email.com", "senha": "123456"}, "nome"),
    ({"nome": "", "email": "teste@email.com", "senha": "123456"}, "nome"),
    ({"nome": "   ", "email": "teste@email.com", "senha": "123456"}, "nome"),
    ({"nome": "Carlos", "senha": "123456"}, "email"),
    ({"nome": "Carlos", "email": "", "senha": "123456"}, "email"),
    ({"nome": "Carlos", "email": "   ", "senha": "123456"}, "email"),
    ({"nome": "Carlos", "email": "teste@email.com"}, "senha"),
    ({"nome": "Carlos", "email": "teste@email.com", "senha": ""}, "senha"),
    ({"nome": "Carlos", "email": "teste@email.com", "senha": "   "}, "senha"),
])
def test_cadastro_erro_campos_obrigatorios(client, payload_invalido, campo_esperado):
    """
    Testa falta ou campos vazios/apenas espaços.
    Deve retornar status HTTP 400.
    """
    response = client.post("/poker/cadastro", json=payload_invalido)
    assert response.status_code == 400
    dados = response.get_json()
    assert dados["sucesso"] is False
    assert campo_esperado in dados["mensagem"].lower()


@pytest.mark.parametrize("email_invalido", [
    "email_sem_arroba",
    "email@",
    "@dominio.com",
    "email@dominio",
    "espaços no email@teste.com"
])
def test_cadastro_erro_email_invalido(client, email_invalido):
    """
    Testa formatos inválidos de e-mail.
    Deve retornar status HTTP 400.
    """
    payload = {
        "nome": "Jogador Teste",
        "email": email_invalido,
        "senha": "123456"
    }
    response = client.post("/poker/cadastro", json=payload)
    assert response.status_code == 400
    dados = response.get_json()
    assert dados["sucesso"] is False
    assert "formato inválido" in dados["mensagem"].lower()


def test_cadastro_erro_senha_curta(client):
    """
    Testa senha com menos de 6 caracteres.
    Deve retornar status HTTP 400.
    """
    payload = {
        "nome": "Jogador Teste",
        "email": "jogador.teste@email.com",
        "senha": "12345"  # 5 caracteres
    }
    response = client.post("/poker/cadastro", json=payload)
    assert response.status_code == 400
    dados = response.get_json()
    assert dados["sucesso"] is False
    assert "mínimo 6 caracteres" in dados["mensagem"].lower()


def test_cadastro_erro_email_duplicado(client):
    """
    Testa a tentativa de cadastrar o mesmo e-mail duas vezes.
    Deve retornar status HTTP 409 (Conflict).
    """
    payload = {
        "nome": "Primeiro Jogador",
        "email": "duplicado@poker.com",
        "senha": "senha123456"
    }
    # Primeiro cadastro: Sucesso
    r1 = client.post("/poker/cadastro", json=payload)
    assert r1.status_code == 201

    # Segundo cadastro com o mesmo e-mail (inclusive com variação de maiúsculas): Erro 409
    payload_duplicado = {
        "nome": "Segundo Jogador",
        "email": "DUPLICADO@poker.com",
        "senha": "outraSenha123"
    }
    r2 = client.post("/poker/cadastro", json=payload_duplicado)
    assert r2.status_code == 409
    dados = r2.get_json()
    assert dados["sucesso"] is False
    assert "já cadastrado" in dados["mensagem"].lower()


# ============================================================================
# TESTES DE CONSULTA DE PARTIDAS (GET /poker/partidasAbertas)
# ============================================================================

def test_consulta_partidas_abertas_vazio(client):
    """
    Testa a consulta quando não há nenhuma partida cadastrada.
    Deve retornar HTTP 200 e uma lista vazia.
    """
    response = client.get("/poker/partidasAbertas")
    assert response.status_code == 200
    dados = response.get_json()
    assert dados["sucesso"] is True
    assert dados["dados"] == []
    assert dados["partidas"] == []


def test_partidas_de_exemplo_sao_carregadas_idempotentemente(app):
    app.config["SEED_SAMPLE_DATA"] = True

    init_db(app)
    init_db(app)

    with app.app_context():
        partidas = get_db().execute(
            "SELECT nome, participantes, capacidade, status FROM partidas ORDER BY id"
        ).fetchall()

    assert len(partidas) == 5
    assert [partida["nome"] for partida in partidas] == [
        "Mesa Iniciante",
        "Mesa Intermediária",
        "Mesa Lotada",
        "Mesa em Andamento",
        "Mesa Finalizada",
    ]


def test_consulta_partidas_abertas_sucesso(client, app):
    """
    Testa a listagem de partidas abertas com mesas disponíveis no banco.
    Deve retornar ID, participantes e capacidade das mesas.
    """
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO partidas (nome, participantes, capacidade, status) VALUES (?, ?, ?, ?)",
            ("Mesa dos Campeões", 3, 6, "aberta")
        )
        db.execute(
            "INSERT INTO partidas (nome, participantes, capacidade, status) VALUES (?, ?, ?, ?)",
            ("Mesa High Stakes", 1, 8, "aberta")
        )
        db.commit()

    response = client.get("/poker/partidasAbertas")
    assert response.status_code == 200

    dados = response.get_json()
    assert dados["sucesso"] is True
    partidas = dados["dados"]
    assert len(partidas) == 2

    for mesa in partidas:
        assert "id" in mesa
        assert "nome" in mesa
        assert "participantes" in mesa
        assert "capacidade" in mesa
        assert isinstance(mesa["id"], int)
        assert isinstance(mesa["participantes"], int)
        assert isinstance(mesa["capacidade"], int)
        assert mesa["participantes"] < mesa["capacidade"]


def test_consulta_partidas_filtra_mesas_cheias_e_fechadas(client, app):
    """
    Testa se a consulta filtra corretamente:
    - Mesas cheias (participantes == capacidade) não devem aparecer.
    - Mesas com status diferente de 'aberta' (ex: 'em_andamento') não devem aparecer.
    """
    with app.app_context():
        db = get_db()
        # 1. Aberta com vagas (DEVE APARECER)
        db.execute(
            "INSERT INTO partidas (nome, participantes, capacidade, status) VALUES (?, ?, ?, ?)",
            ("Mesa Aberta Com Vagas", 2, 6, "aberta")
        )
        # 2. Aberta porém cheia/lotada (NÃO DEVE APARECER)
        db.execute(
            "INSERT INTO partidas (nome, participantes, capacidade, status) VALUES (?, ?, ?, ?)",
            ("Mesa Lotada", 6, 6, "aberta")
        )
        # 3. Em andamento (NÃO DEVE APARECER)
        db.execute(
            "INSERT INTO partidas (nome, participantes, capacidade, status) VALUES (?, ?, ?, ?)",
            ("Mesa Em Jogo", 4, 6, "em_andamento")
        )
        # 4. Finalizada (NÃO DEVE APARECER)
        db.execute(
            "INSERT INTO partidas (nome, participantes, capacidade, status) VALUES (?, ?, ?, ?)",
            ("Mesa Encerrada", 0, 6, "finalizada")
        )
        db.commit()

    response = client.get("/poker/partidasAbertas")
    assert response.status_code == 200

    dados = response.get_json()
    partidas = dados["dados"]
    assert len(partidas) == 1
    assert partidas[0]["nome"] == "Mesa Aberta Com Vagas"


def test_tabela_participantes_relaciona_jogadores_e_partidas(app):
    """A tabela associativa deve exigir registros válidos e impedir duplicatas."""
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO jogadores (nome, email, senha) VALUES (?, ?, ?)",
            ("Jogador Teste", "jogador@poker.com", "hash")
        )
        jogador_id = db.execute(
            "SELECT id FROM jogadores WHERE email = ?",
            ("jogador@poker.com",)
        ).fetchone()["id"]
        db.execute(
            "INSERT INTO partidas (nome) VALUES (?)",
            ("Mesa Teste",)
        )
        partida_id = db.execute(
            "SELECT id FROM partidas WHERE nome = ?",
            ("Mesa Teste",)
        ).fetchone()["id"]

        db.execute(
            "INSERT INTO participantes (partida_id, jogador_id) VALUES (?, ?)",
            (partida_id, jogador_id)
        )
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO participantes (partida_id, jogador_id) VALUES (?, ?)",
                (partida_id, jogador_id)
            )

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO participantes (partida_id, jogador_id) VALUES (?, ?)",
                (partida_id, jogador_id + 1000)
            )

        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO participantes (partida_id, jogador_id) VALUES (?, ?)",
                (partida_id + 1000, jogador_id)
            )

        registro = db.execute(
            "SELECT partida_id, jogador_id FROM participantes"
        ).fetchone()
        assert registro["partida_id"] == partida_id
        assert registro["jogador_id"] == jogador_id


# ============================================================================
# TESTES DE PADRONIZAÇÃO DE RESPOSTAS E TRATAMENTO DE ERROS (Issue #1)
# ============================================================================

def test_padronizacao_endpoint_status(client):
    """
    Valida endpoint de status com retorno JSON padronizado.
    """
    response = client.get("/poker/status")
    assert response.status_code == 200
    dados = response.get_json()
    assert dados["sucesso"] is True
    assert "dados" in dados
    assert dados["dados"]["status"] == "online"


def test_padronizacao_erro_404(client):
    """
    Valida que requisições para rotas inexistentes retornam JSON padronizado com 404.
    """
    response = client.get("/rota-totalmente-inexistente")
    assert response.status_code == 404
    dados = response.get_json()
    assert dados["sucesso"] is False
    assert "erro" in dados or "mensagem" in dados


def test_padronizacao_erro_405_metodo_nao_permitido(client):
    """
    Valida que método HTTP incorreto em rota existente retorna JSON padronizado com 405.
    """
    # /poker/cadastro só aceita POST
    response = client.get("/poker/cadastro")
    assert response.status_code == 405
    dados = response.get_json()
    assert dados["sucesso"] is False
    assert "erro" in dados or "mensagem" in dados
