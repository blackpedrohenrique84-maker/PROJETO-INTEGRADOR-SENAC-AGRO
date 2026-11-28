import sqlite3 #Importa o banco de dados sqlite3

banco = sqlite3.connect("valores.db") #ultiliza a biblioteca para criar o sqlite3 para criar uma conexao com banco de dados chamado valores.db
cursor = banco.cursor() #cria um cursor para executar comandos sql dentro do banco de dados sql
cursor.execute(""" 
CREATE TABLE IF NOT EXISTS valores ( 
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    valor REAL NOT NULL,
    tipo  TEXT NOT NULL 
) 

""") #esse código prepara o banco de dados para armazenar informações financeiras, organizando-as em uma tabela com quatro colunas.


cursor.executemany( # é um método utilizado para inserir vários registros de uma só vez no banco de dados, executando o mesmo comando SQL para cada conjunto de informações.
    "INSERT INTO valores (nome, valor, tipo) VALUES (?, ?, ?)", # indica onde e em quais colunas os dados serão armazenados no banco de dados.






    [
        ("Uva", 10.50, "Vitoria"), #cadastra nome,valor do produto, tipo ou variedade no banco de dados.
        ("Uva", 20.00, "Branca"),
        ("Banana", 15.75, "Nanica")
    ]
) 


banco.commit() #salva os dados inseridos, atualizados ou excluídos no banco de dados, garantindo que as alterações sejam registradas.
banco.close() #fecha o banco de dados após terminar as operações, liberando os recursos utilizados pelo programa.
