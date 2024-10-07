# WebApp de Mobilidade do Rio de Janeiro - Desafio MARAVI

Baseado nos requisitos solicitados no Desafio Técnico

## Instruções de instalação

Projeto descrito em Python 3.12.7. Abaixo, link com instruções de instalação:

https://www.python.org/downloads/

Banco de dados em MySQL 8.0.39. Abaixo, link com instruções de instalação:

https://dev.mysql.com/downloads/installer/

## Bibliotecas

`FastApi`

`uvicorn`

`celery`

`pydantic`

`requests`

`redis`

`typing`

`googlemaps`

`datetime`

`schedule`

`mysql-connector-python`

# Arquivos importantes

`main.py`: Arquivo principal do backend. Nele estão contidas os métodos para execução e conexão com a API de mobilidade e do Google Maps.

`tasks.py`: Configura o celery para enfileirar o envio de e-mails.

`bancodedados.py`: Cria o banco de dados localmente. Deve ser executado uma única vez após instalação do MySQL.

`interfaces.py`: Organiza as funcionalidades que os outros arquivos herdam para validação de dados.

## Configurações

O envio de e-mails de notificações de proximidado do ônibus deve ser configurado, fornecendo um endereço de remetente e senha válida, criando um arquivo `.env`. A autenticação via Gmail requer a configuração de uma "senha de aplicativos" nas configurações do seu provedor.
Também é necessário a obtenção de uma chave de API do Google Maps.

Em `config.py`, altere as seguintes linhas com suas informações de remetente:

`KEY_MAPS = "suaChaveApi"`
`PASSWORD = "suaSenhaDeAplicativo"`
`MY_EMAIL = "seuEmail@gmail.com"`

Para criar uma tabela no banco de dados deve-se executar o arquivo `bancodedados.py`.

## Iniciar a aplicação

Para obter acesso a API de mobilidade no backend, está setado a biblioteca `uvicorn`, executando o comando `uvicorn main:app --reload`