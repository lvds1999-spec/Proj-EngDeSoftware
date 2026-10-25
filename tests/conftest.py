import os
import tempfile
import pytest
from app import create_app
from app.database import get_db

@pytest.fixture
def app():
    """
    Cria e configura uma instância limpa da aplicação para os testes,
    utilizando um banco de dados temporário isolado.
    """
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    application = create_app("testing")
    application.config["DATABASE_PATH"] = db_path

    # Garante inicialização das tabelas no banco temporário
    with application.app_context():
        db = get_db()
        db.execute("DELETE FROM jogadores")
        db.execute("DELETE FROM partidas")
        db.commit()

    yield application

    # Limpeza do arquivo de banco de dados após a execução do teste
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass

@pytest.fixture
def client(app):
    """
    Retorna o cliente de teste HTTP do Flask.
    """
    return app.test_client()
