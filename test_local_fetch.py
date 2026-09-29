import requests
import concurrent.futures
from database import get_proposicoes_info, save_many_proposicoes_info

session = requests.Session()
BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"

def get_detail_sync(id_prop, ano):
    try:
        r = session.get(f"{BASE_URL}/proposicoes/{id_prop}", timeout=10)
        if r.status_code == 200:
            detalhe = r.json().get("dados", {})
            status = detalhe.get("statusProposicao", {})
            cod_sit = status.get("codSituacao")
            return (id_prop, cod_sit, ano)
    except:
        pass
    return (id_prop, None, ano)

def fetch_and_filter(id_deputado, ano_filtro, cod_situacao_filtro):
    # Fetch all propositions from API
    url = f"{BASE_URL}/proposicoes"
    params = {"idDeputadoAutor": id_deputado, "ordem": "DESC", "ordenarPor": "id", "itens": 100}
    if ano_filtro: params["ano"] = ano_filtro
    
    todas = []
    r = session.get(url, params=params)
    payload = r.json()
    todas.extend(payload.get("dados", []))
    
    while True:
        links = payload.get("links", [])
        next_url = next((l["href"] for l in links if l["rel"] == "next"), None)
        if not next_url: break
        r = session.get(next_url)
        payload = r.json()
        todas.extend(payload.get("dados", []))
        
    # Check DB
    ids = [p['id'] for p in todas]
    db_info = get_proposicoes_info(ids)
    
    missing = [p for p in todas if p['id'] not in db_info]
    
    if missing:
        print(f"Fetching details for {len(missing)} items...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(get_detail_sync, p['id'], p['ano']) for p in missing]
            new_data = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        save_many_proposicoes_info([d for d in new_data if d[1] is not None])
        db_info.update({d[0]: {"cod_situacao": d[1], "ano": d[2]} for d in new_data})
        
    # Filter
    filtradas = []
    for p in todas:
        info = db_info.get(p['id'], {})
        sit = info.get("cod_situacao")
        if cod_situacao_filtro and sit != cod_situacao_filtro:
            continue
        filtradas.append(p)
        
    return filtradas

print(len(fetch_and_filter(204534, 2026, 1140)))
