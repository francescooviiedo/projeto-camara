import requests

session = requests.Session()
BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"

def test(id_deputado):
    url_votacoes = f"{BASE_URL}/votacoes"
    params = {
        "ordem": "DESC",
        "ordenarPor": "dataHoraRegistro",
        "itens": 30
    }
    response = session.get(url_votacoes, params=params)
    votacoes = response.json().get("dados", [])
    print(f"Total votacoes: {len(votacoes)}")
    
    resultados = []
    for votacao in votacoes:
        resp_votos = session.get(f"{BASE_URL}/votacoes/{votacao['id']}/votos")
        if resp_votos.status_code == 200:
            votos = resp_votos.json().get("dados", [])
            print(f"Votacao {votacao['id']} - votos: {len(votos)}")
            if not votos: continue
            
            voto_deputado = next((v for v in votos if v.get("deputado_", {}).get("id") == id_deputado), None)
            if voto_deputado:
                resultados.append({"voto": voto_deputado.get("tipoVoto")})
            else:
                resultados.append({"voto": "Ausente"})
    return len(resultados)

print("Resultados nominais:", test(204534))
