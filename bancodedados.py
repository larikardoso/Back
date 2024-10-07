import mysql.connector

mydb = mysql.connector.connect(
  host="localhost",
  user="user",
  password="password",
  database="banco"
)

cursor = mydb.cursor()

cursor.execute("""
    CREATE TABLE clientes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(255),
        linha VARCHAR(255),
        ponto VARCHAR(255),
        janela1 VARCHAR(255),
        janela2 VARCHAR(255)
    )
""")

# Fechar a conexão
cursor.close()
mydb.close()