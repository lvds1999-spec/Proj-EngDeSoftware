# API LoveLetter/Poker

API HTTP desenvolvida em Flask para cadastro de jogadores, consulta de partidas
disponíveis e entrada de jogadores em partidas. O projeto usa SQLite para
armazenar os dados e retorna respostas em JSON.

> Este repositório contém uma API, não uma interface web. Ao abrir `/` no
> navegador, é esperado receber uma resposta JSON informando que a API está em
> execução.

## Requisitos

- Python 3.11 ou compatível
- Dependências listadas em `requirements.txt`

## Executar localmente

No terminal, a partir da raiz do projeto:

```powershell
python -m pip install -r requirements.txt
python run.py
```

Por padrão, o servidor de desenvolvimento fica disponível em
`http://localhost:5000`. A configuração padrão é `development`; nesse ambiente,
o banco SQLite `poker.db` é criado na raiz do projeto e recebe partidas de
exemplo na inicialização.

Para selecionar uma configuração, defina `FLASK_ENV` antes de iniciar:

```powershell
$env:FLASK_ENV = "development"
python run.py
```

As configurações `development`, `testing` e `default` são definidas em
`app/config.py`. O ambiente `testing` usa um banco temporário e não carrega as
partidas de exemplo automaticamente.

## Funcionalidades atuais

- Respostas JSON padronizadas para sucesso e erro.
- Endpoint raiz e endpoint de status da API.
- Cadastro de jogadores com validação de campos e formato do e-mail.
- Verificação de e-mails duplicados sem diferenciar maiúsculas de minúsculas.
- Armazenamento de senha usando hash; a senha original não é gravada.
- Consulta de partidas abertas que ainda têm vagas.
- Entrada de jogador em partida aberta, validando existência de jogador e
  partida, disponibilidade de vagas, estado da partida e participação duplicada.
- Registro da associação jogador-partida e atualização do contador de
  participantes na mesma transação.
- Criação automática das tabelas SQLite de jogadores, partidas e participantes.
- Carga idempotente de partidas de exemplo em desenvolvimento.
- Testes automatizados com pytest.

## Endpoints

Todas as respostas usam JSON. Em geral, o corpo contém `sucesso` e `mensagem`;
operações com dados também podem incluir `dados`. Respostas de erro incluem
`erro`.

### `GET /`

Verifica se a aplicação está respondendo.

Exemplo:

```json
{
  "mensagem": "API LoveLetter/Poker em execução.",
  "sucesso": true
}
```

### `GET /poker/status`

Retorna o estado da API e a versão informada pelo serviço.

Resposta de exemplo:

```json
{
  "sucesso": true,
  "mensagem": "API do Poker operando normalmente.",
  "dados": {
    "status": "online",
    "versao": "1.0.0"
  }
}
```

### `POST /poker/cadastro`

Cadastra um jogador. Envie `nome`, `email` e `senha` em um corpo JSON:

```json
{
  "nome": "Ana Lima",
  "email": "ana@example.com",
  "senha": "senha123"
}
```

O nome, e-mail e senha são obrigatórios; o e-mail deve ter formato válido e a
senha deve ter pelo menos seis caracteres. Em caso de sucesso, retorna HTTP
`201` e o identificador do jogador. E-mail já cadastrado retorna `409`;
conteúdo ou campos inválidos retornam `400`.

### `GET /poker/partidasAbertas`

Lista as partidas com status `aberta` e participantes abaixo da capacidade.
Cada item inclui `id`, `nome`, `participantes` e `capacidade`. A lista é
ordenada pelo identificador da partida.

### `POST /poker/{idPartida}/entrar?idJogador={idJogador}`

Solicita a entrada do jogador informado na partida do caminho. Exemplo:

```text
POST /poker/1/entrar?idJogador=2
```

Quando a entrada é aceita, a API cria o vínculo em `participantes`, incrementa
o contador da partida e retorna HTTP `201`. O endpoint rejeita:

- `idJogador` ausente, inválido ou não positivo (`400`);
- jogador ou partida inexistentes (`404`);
- jogador que já participa da partida (`409`);
- partida lotada ou que não esteja aberta (`409`).

## Partidas de exemplo

Em desenvolvimento, são inseridas partidas com estes nomes e estados:

| Nome | Participantes | Capacidade | Estado |
| --- | ---: | ---: | --- |
| Mesa Iniciante | 1 | 6 | aberta |
| Mesa Intermediária | 3 | 6 | aberta |
| Mesa Lotada | 6 | 6 | aberta |
| Mesa em Andamento | 4 | 6 | em_andamento |
| Mesa Finalizada | 0 | 6 | finalizada |

A carga evita inserir novamente uma partida se já existir outra com o mesmo
nome.

## Banco de dados

O SQLite cria as tabelas automaticamente:

- `jogadores`: cadastro, e-mail único e hash de senha.
- `partidas`: nome, quantidade de participantes, capacidade e estado.
- `participantes`: tabela de associação entre jogador e partida. A chave
  primária composta (`partida_id`, `jogador_id`) impede vínculos duplicados; as
  chaves estrangeiras removem os vínculos quando o jogador ou a partida são
  excluídos.

O arquivo padrão de banco é `poker.db`, ignorado pelo Git.

## Executar os testes

Instale as dependências e execute:

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
```

Os testes cobrem cadastro e validações, hash de senha, consulta de partidas,
integridade dos vínculos, entrada de múltiplos jogadores, consistência entre o
contador da partida e suas participações registradas, e respostas de erro.

## Atualização desta documentação

Ao implementar uma funcionalidade ou alterar um comportamento da API, atualize
este README na mesma mudança: revise a lista de funcionalidades, a documentação
dos endpoints e exemplos, as regras de validação e, quando aplicável, o modelo
de dados, a execução e os testes. Documente somente o comportamento que já
estiver implementado.
