from celery import Celery
import smtplib
import os

celery = Celery(
    "tasks", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0"
)


# tarefa para enviar o email de notificação
@celery.task
def send_one_email(email):
    sender_email = os.environ["MY_EMAIL"]
    password = os.environ["PASSWORD"]

    with smtplib.SMTP("smtp.gmail.com", 587) as connection:
        connection.starttls()
        connection.login(user=sender_email, password=password)
        connection.sendmail(
            from_addr=sender_email,
            to_addrs=email,
            msg="Subject:Informacoes sobre sua linha!\n\nO onibus esta a 10 minutos do seu ponto.",
        )

    return f"Email enviado para {email}!"
