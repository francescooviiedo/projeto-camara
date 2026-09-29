import requests

def get_situacoes():
    url = "https://dadosabertos.camara.leg.br/api/v2/referencias/situacoesProposicao"
    response = requests.get(url, timeout=15)
    return response.json().get("dados", [])

print(len(get_situacoes()))
