from flask import jsonify

def json_response(sucesso: bool, dados=None, mensagem: str = None, erro: str = None, status_code: int = 200, **kwargs):
    """
    Padronização global de respostas JSON da API.
    """
    payload = {
        "sucesso": sucesso
    }
    
    if mensagem is not None:
        payload["mensagem"] = mensagem
        
    if dados is not None:
        payload["dados"] = dados
        
    if erro is not None:
        payload["erro"] = erro

    # Adiciona campos extras se fornecidos (como 'id' ou listas para facilidade de consumo)
    for k, v in kwargs.items():
        if v is not None:
            payload[k] = v

    return jsonify(payload), status_code


def success_response(dados=None, mensagem: str = "Operação realizada com sucesso", status_code: int = 200, **kwargs):
    return json_response(sucesso=True, dados=dados, mensagem=mensagem, status_code=status_code, **kwargs)


def error_response(mensagem: str = "Ocorreu um erro na requisição", status_code: int = 400, erro: str = None, **kwargs):
    return json_response(sucesso=False, erro=erro or mensagem, mensagem=mensagem, status_code=status_code, **kwargs)
