from app.database import get_db


def test_fluxo_completo_de_partida(client, app):
    with app.app_context():
        db = get_db()
        partida_id = db.execute(
            "INSERT INTO partidas (nome, capacidade) VALUES (?, ?)",
            ("Mesa do fluxo completo", 6)
        ).lastrowid
        db.commit()

    jogadores = []
    for indice in range(3):
        response = client.post(
            "/poker/cadastro",
            json={
                "nome": f"Jogador do fluxo {indice + 1}",
                "email": f"fluxo{indice + 1}@poker.com",
                "senha": "senha-segura"
            }
        )
        assert response.status_code == 201
        jogadores.append(response.get_json()["dados"]["id"])

    partidas_abertas = client.get("/poker/partidasAbertas")
    assert partidas_abertas.status_code == 200
    mesas = partidas_abertas.get_json()["dados"]
    mesa = next(partida for partida in mesas if partida["id"] == partida_id)
    assert mesa["participantes"] == 0

    for quantidade_esperada, jogador_id in enumerate(jogadores, start=1):
        entrada = client.post(
            f"/poker/{mesa['id']}/entrar?idJogador={jogador_id}"
        )
        assert entrada.status_code == 201
        assert entrada.get_json()["dados"]["participantes"] == quantidade_esperada

        partidas_atualizadas = client.get("/poker/partidasAbertas")
        assert partidas_atualizadas.status_code == 200
        mesa_atualizada = next(
            partida
            for partida in partidas_atualizadas.get_json()["dados"]
            if partida["id"] == mesa["id"]
        )
        assert mesa_atualizada["participantes"] == quantidade_esperada

    inicio = client.post(
        f"/poker/{mesa['id']}/iniciar?idJogador={jogadores[0]}"
    )
    assert inicio.status_code == 200
    assert inicio.get_json()["dados"]["status"] == "em_andamento"

    with app.app_context():
        db = get_db()
        partida = db.execute(
            "SELECT status, participantes FROM partidas WHERE id = ?",
            (mesa["id"],)
        ).fetchone()
        cartas = db.execute(
            """
            SELECT jogador_id, valor, naipe
            FROM cartas
            WHERE partida_id = ?
            ORDER BY jogador_id
            """,
            (mesa["id"],)
        ).fetchall()

    assert partida["status"] == "em_andamento"
    assert partida["participantes"] == len(jogadores)
    assert len(cartas) == 2 * len(jogadores)
    assert {carta["jogador_id"] for carta in cartas} == set(jogadores)
    assert all(
        sum(carta["jogador_id"] == jogador_id for carta in cartas) == 2
        for jogador_id in jogadores
    )
    assert len({(carta["valor"], carta["naipe"]) for carta in cartas}) == len(cartas)

    partidas_apos_inicio = client.get("/poker/partidasAbertas")
    assert partidas_apos_inicio.status_code == 200
    assert all(
        partida_aberta["id"] != mesa["id"]
        for partida_aberta in partidas_apos_inicio.get_json()["dados"]
    )
