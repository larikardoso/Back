import os
import time
from fastapi import FastAPI
import smtplib
import schedule
from interfaces import BusRequest, StopTimeRequest, Cliente, Datas, DistanceMatrix
from typing import List
import requests
import mysql.connector
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from functools import reduce
from tasks import send_one_email
import threading

app = FastAPI()

origins = [
    "http://localhost:3000",  # URL do frontend
]

# Adicionar o middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos os headers
)

taskEmail = "Erro ao colocar a task na fila"


# Define a conexão com o banco MySQL
def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost", user="user", password="password", database="banco"
    )
    return connection


# Retorna as informações de um ponto de ônibus
@app.post("/stops")
def get_stops(data: StopTimeRequest):
    url = f"https://api.mobilidade.rio/gtfs/stops/?stop_id={data.ponto}"
    response = requests.get(url, timeout=30)
    if response.status_code == 200:
        bus_positions = response.json()
        return bus_positions["results"]
    else:
        return {"error": "Não foi possível obter os dados dos ônibus"}


# Posição dos ônibus do Rio de Janeiro
@app.get("/bus_data")
def get_bus_data(data: Datas = None):
    params = ""
    if data is not None:
        params = f"?dataInicial={data.dataInicio}&dataFinal={data.dataFim}"
    else:
        data_atual = datetime.now()
        data_fim = data_atual.strftime("%Y-%m-%d+%H:%M:%S")

        data_menos_um_minuto = data_atual - timedelta(minutes=30)
        data_inicio = data_menos_um_minuto.strftime("%Y-%m-%d+%H:%M:%S")

        params = f"?dataInicial={data_inicio}&dataFinal={data_fim}"

    url = f"https://dados.mobilidade.rio/gps/sppo{params}"
    response = requests.get(url)
    if response.status_code == 200:
        bus_positions = (
            response.json()
        )  # Atualiza a lista global com os dados de ônibus
        return bus_positions
    else:
        return {"error": "Não foi possível obter os dados dos ônibus"}


def loop():
    banco = getbanco()

    # cria um set de pontos para consultar apenas uma vez cada ponto
    pontos = set()
    for sub_array in banco:
        pontos.add(sub_array[3])

    pontosInfo = []  # informalção de todos os pontos
    for id in pontos:
        pontoRequest = StopTimeRequest(ponto=id, linha="")
        ponto = get_stops(pontoRequest)
        pontosInfo.append(ponto[0])

    for user in banco:
        todosOnibus = []

        data = Datas(dataInicio=user[4], dataFim=user[5])
        todosOnibus = get_bus_data(data)
        onibusFiltrados = []
        for onibus in todosOnibus:
            if onibus["linha"] == user[2]:
                onibusFiltrados.append(onibus)

        onibusUnicos = []
        onibusUnicos = get_latest_items(onibusFiltrados)
        # limita a 25 ônibus, devido ao limite da API do Google
        onibusUnicos = onibusUnicos[:25]

        origins = ""
        for index, element in enumerate(onibusUnicos):
            lat = element["latitude"].replace(",", ".")
            long = element["longitude"].replace(",", ".")
            if index > 0:
                origins += "|"
            origins += f"{lat},{long}"

        # seleciona apenas o ponto referente ao usuário dentro do set de pontos
        pontoAtual = next(
            (item for item in pontosInfo if item["stop_id"] == user[3]), None
        )

        destinations = f"{pontoAtual['stop_lat']},{pontoAtual['stop_lon']}"

        distanceMatrixRequest = DistanceMatrix(
            destinations=destinations, origins=origins
        )
        responseDistance = get_distance(distanceMatrixRequest)

        # verifica se está a menos de 600s (10 min)
        exceeds_600 = any(
            item["elements"][0]["duration"]["value"] < 600
            for item in responseDistance["rows"]
        )

        if exceeds_600:
            enqueue_email_task(user[1])

    return {"banco": "sucesso"}


# adiciona uma task de email a fila
def enqueue_email_task(email):
    global taskEmail
    taskEmail = send_one_email.delay(email)  # Coloca a tarefa na fila
    print(taskEmail)
    return {"task_id": taskEmail.id}


# retorna apenas a informação mais recente de GPS de cada carro
def get_latest_items(lista):
    return list(
        reduce(
            lambda acc, item: {**acc, item["ordem"]: item}
            if item["ordem"] not in acc
            or acc[item["ordem"]]["datahora"] < item["datahora"]
            else acc,
            lista,
            {},
        ).values()
    )


# recupera todas as informações do banco MySQL
def getbanco():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM clientes")
    resultados = cursor.fetchall()

    connection.commit()
    cursor.close()
    connection.close()
    return resultados


# consulta a API do Google para saber o tempo que o ônibus vai demorar pra chegar
@app.post("/distance")
def get_distance(data: DistanceMatrix):
    key = os.environ["KEY_MAPS"]
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?destinations={data.destinations}&origins={data.origins}&key={key}&mode=transit&transit_mode=bus&language=pt_br"

    response = requests.get(url)
    if response.status_code == 200:
        responseJson = response.json()
        return responseJson
    else:
        return {"error": "Não foi possível obter os dados de distância"}


# inclui um cliente no banco (tela de cadastro)
@app.post("/clientes")
def create_cliente(cliente: Cliente):
    connection = get_db_connection()
    cursor = connection.cursor()

    (
        cursor.execute(
            "INSERT INTO clientes (email, linha, ponto, janela1, janela2) VALUES (%s, %s, %s, %s, %s)",
            (
                cliente.email,
                cliente.linha_BD,
                cliente.ponto_BD,
                cliente.janela1,
                cliente.janela2,
            ),
        ),
    )

    connection.commit()  # Confirmar a transação
    cursor.close()
    connection.close()
    return {
        "message": "Cliente inserido com sucesso! Você será notificado por e-mail quando o ônibus estiver a 10 minutos de distância"
    }


# Função para rodar o schedule em uma thread separada
def rodar_agendamento():
    while True:
        schedule.run_pending()
        time.sleep(1)  # Delay para evitar o uso excessivo da CPU


# Agende a tarefa para rodar a cada 1 minuto
# schedule.every(1).minutes.do(loop)
schedule.every(20).seconds.do(loop)

# Inicie o agendamento em uma thread separada
agendamento_thread = threading.Thread(target=rodar_agendamento)
agendamento_thread.daemon = (
    True  # Define como daemon para fechar quando o programa principal encerrar
)
agendamento_thread.start()
