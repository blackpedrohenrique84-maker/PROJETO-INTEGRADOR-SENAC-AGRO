import sqlite3

banco = sqlite3.connect("valores.db")
cursor = banco.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS valores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    valor REAL NOT NULL,
    tipo  TEXT NOT NULL
)

""")


cursor.executemany(
    "INSERT INTO valores (nome, valor, tipo) VALUES (?, ?, ?)",
    [
        ("Uva", 10.50, "Vitoria"),
        ("Uva", 20.00, "Branca"),
        ("Banana", 15.75, "Nanica")
    ]
)


banco.commit()
banco.close()