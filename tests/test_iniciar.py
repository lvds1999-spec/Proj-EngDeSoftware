from app.database import get_db


def _criar_jogador(db, indice):
    return db.execute(
        "INSERT INTO jogadores (nome, email, senha) VALUES (?, ?, ?)",
        (f"Jogador {indice}", f"iniciar{indice}@poker.com", "hash")
    ).lastrowid


def _criar_partida(db, nome, status="aberta"):
    return db.execute(
        "INSERT INTO partidas (nome, status) VALUES (?, ?)",
        (nome, status)
    ).lastrowid


def _adicionar_participante(db, partida_id, jogador_id):
    db.execute(
        "INSERT INTO participantes (partida_id, jogador_id) VALUES (?, ?)",
        (partida_id, jogador_id)
    )


def test_iniciar_distribui_duas_cartas_sem_repeticao_e_nao_as_expoe(client, app):
    with app.app_context():
        db = get_db()
        jogadores = [_criar_jogador(db, indice) for indice in range(2)]
        partida_id = _criar_partida(db, "Mesa para iniciar")
        for jogador_id in jogadores:
            _adicionar_participante(db, partida_id, jogador_id)
        db.execute(
            "UPDATE partidas SET responsavel_id = ? WHERE id = ?",
            (jogadores[0], partida_id)
        )
        db.commit()

    response = client.post(
        f"/poker/{partida_id}/iniciar?idJogador={jogadores[0]}"
    )

    assert response.status_code == 200
    dados = response.get_json()["dados"]
    assert dados == {
        "idPartida": partida_id,
        "status": "em_andamento",
        "participantes": 2,
        "cartasPorJogador": 2
    }
    resposta_json = response.get_json()
    assert "cartas" not in resposta_json
    assert "valor" not in resposta_json
    assert "naipe" not in resposta_json

    with app.app_context():
        db = get_db()
        partida = db.execute(
            "SELECT status FROM partidas WHERE id = ?",
            (partida_id,)
        ).fetchone()
        cartas = db.execute(
            """
            SELECT jogador_id, valor, naipe
            FROM cartas
            WHERE partida_id = ?
            ORDER BY jogador_id
            """,
            (partida_id,)
        ).fetchall()

    assert partida["status"] == "em_andamento"
    assert len(cartas) == 2 * len(jogadores)
    assert {carta["jogador_id"] for carta in cartas} == set(jogadores)
    assert all(
        sum(carta["jogador_id"] == jogador_id for carta in cartas) == 2
        for jogador_id in jogadores
    )
    assert len({(carta["valor"], carta["naipe"]) for carta in cartas}) == len(cartas)


def test_iniciar_partida_inexistente_retorna_404(client, app):
    with app.app_context():
        db = get_db()
        jogador_id = _criar_jogador(db, 1)
        db.commit()

    response = client.post(
        f"/poker/999/iniciar?idJogador={jogador_id}"
    )

    assert response.status_code == 404


def test_iniciar_jogador_inexistente_retorna_404(client, app):
    with app.app_context():
        db = get_db()
        responsavel_id = _criar_jogador(db, 1)
        partida_id = _criar_partida(db, "Mesa para jogador inexistente")
        _adicionar_participante(db, partida_id, responsavel_id)
        db.execute(
            "UPDATE partidas SET responsavel_id = ? WHERE id = ?",
            (responsavel_id, partida_id)
        )
        db.commit()

    response = client.post(
        f"/poker/{partida_id}/iniciar?idJogador=999"
    )

    assert response.status_code == 404


def test_iniciar_solicitante_que_nao_e_responsavel_retorna_403(client, app):
    with app.app_context():
        db = get_db()
        responsavel_id = _criar_jogador(db, 1)
        solicitante_id = _criar_jogador(db, 2)
        partida_id = _criar_partida(db, "Mesa com responsável")
        _adicionar_participante(db, partida_id, responsavel_id)
        _adicionar_participante(db, partida_id, solicitante_id)
        db.execute(
            "UPDATE partidas SET responsavel_id = ? WHERE id = ?",
            (responsavel_id, partida_id)
        )
        db.commit()

    response = client.post(
        f"/poker/{partida_id}/iniciar?idJogador={solicitante_id}"
    )

    assert response.status_code == 403


def test_iniciar_com_menos_de_dois_participantes_retorna_409(client, app):
    with app.app_context():
        db = get_db()
        responsavel_id = _criar_jogador(db, 1)
        partida_id = _criar_partida(db, "Mesa incompleta")
        _adicionar_participante(db, partida_id, responsavel_id)
        db.execute(
            "UPDATE partidas SET responsavel_id = ? WHERE id = ?",
            (responsavel_id, partida_id)
        )
        db.commit()

    response = client.post(
        f"/poker/{partida_id}/iniciar?idJogador={responsavel_id}"
    )

    assert response.status_code == 409


def test_iniciar_partida_ja_iniciada_retorna_409(client, app):
    with app.app_context():
        db = get_db()
        jogadores = [_criar_jogador(db, indice) for indice in range(2)]
        partida_id = _criar_partida(
            db, "Mesa já iniciada", status="em_andamento"
        )
        for jogador_id in jogadores:
            _adicionar_participante(db, partida_id, jogador_id)
        db.execute(
            "UPDATE partidas SET responsavel_id = ? WHERE id = ?",
            (jogadores[0], partida_id)
        )
        db.commit()

    response = client.post(
        f"/poker/{partida_id}/iniciar?idJogador={jogadores[0]}"
    )

    assert response.status_code == 409
