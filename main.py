import os
import time
from fastapi import FastAPI
import smtplib
import schedule
from interfaces import BusRequest, StopTimeRequest, Cliente, Datas, DistanceMatrix
from pydantic import BaseModel
from tasks import fetch_bus_positions, send_email_notification
from typing import List
import requests
import mysql.connector
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from functools import reduce

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


# Define a conexão com o banco MySQL
def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost", user="user", password="password", database="banco"
    )
    return connection


# Manda o email
def mandar_notificacao(reciver):
    print(reciver)
    sender_email = os.environ['MY_EMAIL']
    password = os.environ["PASSWORD"]

    with smtplib.SMTP("smtp.gmail.com", 587) as connection:
        connection.starttls()
        connection.login(user=sender_email, password=password)
        connection.sendmail(
            from_addr=sender_email,
            to_addrs=reciver,
            msg="Subject:Informacoes sobre sua linha!\n\nO onibus esta a 10 minutos do seu ponto.",
        )

        schedule.every(1).minutes.do(mandar_notificacao)


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

    # print(params)

    url = f"https://dados.mobilidade.rio/gps/sppo{params}"
    # print(url)
    response = requests.get(url)
    if response.status_code == 200:
        bus_positions = (
            response.json()
        )  # Atualiza a lista global com os dados de ônibus
        return bus_positions
    else:
        return {"error": "Não foi possível obter os dados dos ônibus"}


def loop():
    print("###")
    banco = getbanco()

    pontos = set()
    linhas = set()
    for sub_array in banco:
        linhas.add(sub_array[2])
        pontos.add(sub_array[3])

    print(linhas)
    print(pontos)

    pontosInfo = []  # informalção de todos os pontos
    for id in pontos:
        pontoRequest = StopTimeRequest(ponto=id, linha="")
        ponto = get_stops(pontoRequest)
        pontosInfo.append(ponto[0])

    print(pontosInfo)
    print(len(pontosInfo))

    todosOnibus = get_bus_data()
    onibusFiltrados = []
    for onibus in todosOnibus:
        if onibus["linha"] in linhas:
            onibusFiltrados.append(onibus)

    # print(onibusFiltrados)
    # print(len(onibusFiltrados))

    onibusUnicos = get_latest_items(onibusFiltrados)
    print(onibusUnicos)
    print(len(onibusUnicos))
    onibusUnicos = onibusUnicos[:10]
    print(onibusUnicos)
    print(len(onibusUnicos))
    
    for user in banco:
        print(user)

        origins = ""
        for index, element in enumerate(onibusUnicos):
            lat = element["latitude"].replace(",", ".")
            long = element["longitude"].replace(",", ".")
            if index > 0:
                origins += "|"
            origins += f"{lat},{long}"

        destinations = f"{pontosInfo[0]['stop_lat']},{pontosInfo[0]['stop_lon']}"

        print("$$$")
        print(origins)
        print(destinations)

        distanceMatrixRequest = DistanceMatrix(destinations=destinations, origins=origins)
        responseDistance = get_distance(distanceMatrixRequest)
        print(responseDistance)
        print(responseDistance["rows"])

        # verifica se está a menos de 600s (10 min)
        exceeds_600 = any(
            item["elements"][0]["duration"]["value"] < 600
            for item in responseDistance["rows"]
        )

        print(exceeds_600)

        if exceeds_600:
            mandar_notificacao("email")

    return {"banco": "sucesso"}


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


# consulta a API do Google pra saber o tempo que o onibus vai demorar pra chegar
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


# Agendar o método para ser executado a cada 1 minuto
# loop()
# schedule.every(60).seconds.do(loop)

# # Loop para manter o agendamento rodando
# while True:
#     schedule.run_pending()  # Executa qualquer tarefa agendada
#     time.sleep(1)  # Aguarda 1 segundo para checar novamente
