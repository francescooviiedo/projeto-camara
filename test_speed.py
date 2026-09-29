import requests
import concurrent.futures
import time

session = requests.Session()

def get_detail(id_prop):
    try:
        r = session.get(f'https://dadosabertos.camara.leg.br/api/v2/proposicoes/{id_prop}')
        if r.status_code == 200:
            return r.json()['dados']
    except:
        pass
    return None

props = requests.get('https://dadosabertos.camara.leg.br/api/v2/proposicoes', params={'idDeputadoAutor': 204534, 'itens': 100}).json()['dados']
ids = [p['id'] for p in props]

t0 = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    results = list(executor.map(get_detail, ids))
t1 = time.time()

print(f"Fetched 100 details in {t1-t0:.2f}s")
