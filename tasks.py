from celery import Celery
import smtplib
import requests

celery_app = Celery('tasks', broker='redis://localhost:6379/0')

# Tarefa para coletar dados dos ônibus
@celery_app.task
def fetch_bus_positions(bus_id: str):
    url = f'https://dados.mobilidade.rio/gps/sppo?dataInicial=2024-01-29+15:40:00&dataFinal=2024-01-29+15:43:00{bus_id}'
    response = requests.get(url)
    return response.json()

@celery_app.task
def collect_bus_positions():
    # Lógica para pegar dados da API de mobilidade e salvar no banco de dados
    pass

# Função para enviar notificação por e-mail
@celery_app.task
def send_email_notification(email: str, bus_data: dict):
    message = f"O ônibus {bus_data['line']} está a 10 minutos do seu ponto."

    with smtplib.SMTP('smtp.example.com') as server:
        server.login("you@example.com", "password")
        server.sendmail("you@example.com", email, message)
    print(f"Enviando e-mail para {email}: {message}")
    return {"message": f"Notificação enviada para {email}"}