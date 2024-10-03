from pydantic import BaseModel


class BusRequest(BaseModel):
    id_linha: str
    ponto_not: str
    janela_horario: list
    email: str


class StopTimeRequest(BaseModel):
    ponto: str
    linha: str


class Cliente(BaseModel):
    email: str
    linha_BD: str
    ponto_BD: str
    janela1: str
    janela2: str


class Datas(BaseModel):
    dataInicio: str
    dataFim: str


class DistanceMatrix(BaseModel):
    destinations: str
    origins: str
