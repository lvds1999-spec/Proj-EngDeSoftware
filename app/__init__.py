from flask import Flask
from app.config import config_by_name
from app.database import close_db, init_db
from app.routes.poker import poker_bp
from app.utils.responses import error_response

def create_app(config_name="default"):
    app = Flask(__name__)
    
    # Configurações da aplicação
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Fechamento automático de conexões de banco de dados
    app.teardown_appcontext(close_db)

    # Inicialização das tabelas do banco
    init_db(app)

    # Registro de Blueprints
    app.register_blueprint(poker_bp)

    # Padronização de respostas JSON para erros HTTP
    @app.errorhandler(400)
    def bad_request(error):
        return error_response(mensagem=getattr(error, 'description', 'Requisição inválida.'), status_code=400)

    @app.errorhandler(404)
    def not_found(error):
        return error_response(mensagem="Recurso ou rota não encontrada.", status_code=404)

    @app.errorhandler(405)
    def method_not_allowed(error):
        return error_response(mensagem="Método HTTP não permitido para esta rota.", status_code=405)

    @app.errorhandler(500)
    def internal_error(error):
        return error_response(mensagem="Erro interno do servidor.", status_code=500)

    @app.route("/")
    def index():
        from app.utils.responses import success_response
        return success_response(mensagem="API LoveLetter/Poker em execução.")

    return app
