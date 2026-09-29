import sqlite3
conn = sqlite3.connect('banco.db')
cursor = conn.cursor()
cursor.execute("SELECT cod_situacao, count(*) FROM proposicoes GROUP BY cod_situacao")
print("All DB stats:", cursor.fetchall())
