import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'banco.db')

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Cria a tabela de resumos se não existir."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resumos (
            id_proposicao INTEGER PRIMARY KEY,
            resumo TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gastos_presidencia (
            mes_ano TEXT PRIMARY KEY,
            valor_total REAL,
            valor_sigiloso REAL
        )
    ''')
    conn.commit()
    conn.close()

def get_gasto_mensal(mes_ano: str):
    """Retorna os gastos mensais da presidencia cacheados, se existirem."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT valor_total, valor_sigiloso FROM gastos_presidencia WHERE mes_ano = ?', (mes_ano,))
    row = cursor.fetchone()
    conn.close()
    return {"total": row[0], "sigiloso": row[1]} if row else None

def save_gasto_mensal(mes_ano: str, valor_total: float, valor_sigiloso: float):
    """Salva um novo registro mensal de gasto."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO gastos_presidencia (mes_ano, valor_total, valor_sigiloso)
        VALUES (?, ?, ?)
    ''', (mes_ano, valor_total, valor_sigiloso))
    conn.commit()
    conn.close()

def get_resumo(id_proposicao: int):
    """Retorna o resumo do banco de dados, se existir."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT resumo FROM resumos WHERE id_proposicao = ?', (id_proposicao,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def save_resumo(id_proposicao: int, resumo: str):
    """Salva um novo resumo no banco de dados."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO resumos (id_proposicao, resumo)
        VALUES (?, ?)
    ''', (id_proposicao, resumo))
    conn.commit()
    conn.close()

# Inicializa o banco de dados na primeira importação
init_db()
