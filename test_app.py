import json
situacoes = [
    {'cod': '1140', 'nome': 'Transformado em Norma Jurídica'},
    {'cod': '', 'nome': 'Aguardando Recebimento'}
]
opcoes_situacoes = {s['nome']: s['cod'] for s in situacoes if s.get('nome')}
print(opcoes_situacoes)
