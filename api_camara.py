import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Optional
import streamlit as st

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"

# Configura uma sessão com retentativas automáticas para lidar com instabilidades (504, 502, 500)
session = requests.Session()
retries = Retry(
    total=4,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retries)
session.mount('http://', adapter)
session.mount('https://', adapter)

def get_partidos(id_legislatura: int = 57) -> List[Dict]:
    """Busca a lista de partidos com mandato na legislatura especificada."""
    url = f"{BASE_URL}/partidos"
    params = {
        "idLegislatura": id_legislatura,
        "itens": 100,
        "ordem": "ASC",
        "ordenarPor": "sigla"
    }
    response = session.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json().get("dados", [])

def get_deputados_por_partido(sigla_partido: str, id_legislatura: int = 57) -> List[Dict]:
    """Busca deputados ativos filtrando pela sigla do partido, lidando com paginação."""
    url = f"{BASE_URL}/deputados"
    params = {
        "siglaPartido": sigla_partido,
        "idLegislatura": id_legislatura,
        "itens": 100,
        "ordem": "ASC",
        "ordenarPor": "nome"
    }
    deputados = []
    
    # Primeira requisição
    response = session.get(url, params=params, timeout=15)
    response.raise_for_status()
    payload = response.json()
    deputados.extend(payload.get("dados", []))
    
    # Paginação segura usando o link 'next' oficial
    while True:
        links = payload.get("links", [])
        next_url = next((link["href"] for link in links if link["rel"] == "next"), None)
        
        if not next_url:
            break
            
        response = session.get(next_url, timeout=15)
        response.raise_for_status()
        payload = response.json()
        deputados.extend(payload.get("dados", []))
        
    return deputados

def get_proposicoes_por_deputado(id_autor: int, ano: Optional[int] = None, cod_situacao: Optional[int] = None, pagina: int = 1, itens: int = 10) -> Dict:
    """Busca projetos de lei propostos pelo deputado, com suporte a filtros e paginação local."""
    url = f"{BASE_URL}/proposicoes"
    params = {
        "idDeputadoAutor": id_autor,
        "ordem": "DESC",
        "ordenarPor": "id",
        "itens": 100
    }
    if ano:
        params["ano"] = ano
        
    todas = []
    try:
        response = session.get(url, params=params, timeout=15)
        response.raise_for_status()
        payload = response.json()
        todas.extend(payload.get("dados", []))
        
        while True:
            links = payload.get("links", [])
            next_url = next((l["href"] for l in links if l["rel"] == "next"), None)
            if not next_url: break
            r = session.get(next_url, timeout=15)
            payload = r.json()
            todas.extend(payload.get("dados", []))
    except Exception:
        pass
        
    if not todas:
        return {"dados": [], "has_next": False, "total_count": 0}
        
    from database import get_proposicoes_info, save_many_proposicoes_info
    import concurrent.futures
    
    ids = [str(p['id']) for p in todas]
    db_info = get_proposicoes_info(ids)
    
    missing = [p for p in todas if str(p['id']) not in db_info]
    
    if missing:
        def get_detail_sync(id_prop, p_ano):
            try:
                r = session.get(f"{BASE_URL}/proposicoes/{id_prop}", timeout=10)
                if r.status_code == 200:
                    status = r.json().get("dados", {}).get("statusProposicao", {})
                    if status:
                        return (id_prop, status.get("codSituacao"), p_ano)
            except:
                pass
            return (id_prop, None, p_ano)
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(get_detail_sync, p['id'], p['ano']) for p in missing]
            new_data = [f.result() for f in concurrent.futures.as_completed(futures)]
            
        to_save = [d for d in new_data if d[1] is not None]
        if to_save:
            save_many_proposicoes_info(to_save)
            
        for d in new_data:
            db_info[str(d[0])] = {"cod_situacao": d[1], "ano": d[2]}
            
    filtradas = []
    contagem_situacoes = {}
    
    for p in todas:
        info = db_info.get(str(p['id']), {})
        sit = info.get("cod_situacao")
        
        if sit is not None:
            contagem_situacoes[sit] = contagem_situacoes.get(sit, 0) + 1
            
        if cod_situacao and sit != int(cod_situacao):
            continue
        filtradas.append(p)
        
    total_count = len(filtradas)
    
    inicio = (pagina - 1) * itens
    fim = inicio + itens
    pagina_dados = filtradas[inicio:fim]
    has_next = fim < total_count
    
    return {
        "dados": pagina_dados,
        "has_next": has_next,
        "total_count": total_count,
        "contagem_situacoes": contagem_situacoes
    }

@st.cache_data(ttl=86400)
def get_situacoes_proposicao() -> List[Dict]:
    """Retorna as situações possíveis de uma proposição para filtro."""
    url = f"{BASE_URL}/referencias/proposicoes/codSituacao"
    response = session.get(url, timeout=15)
    if response.status_code == 200:
        return response.json().get("dados", [])
    return []

@st.cache_data(ttl=3600)
def get_proposicao_detalhes(id_proposicao: int) -> Optional[Dict]:
    """Obtém detalhes de uma proposição específica, focando na urlInteiroTeor."""
    url = f"{BASE_URL}/proposicoes/{id_proposicao}"
    response = session.get(url, timeout=15)
    if response.status_code == 200:
        return response.json().get("dados", {})
    return None

@st.cache_data(ttl=3600)
def get_ultimas_votacoes_nominais(limite: int = 5) -> List[Dict]:
    """Busca as últimas votações nominais da Câmara (cacheado para todos os deputados)."""
    url_votacoes = f"{BASE_URL}/votacoes"
    params = {
        "ordem": "DESC",
        "ordenarPor": "dataHoraRegistro",
        "itens": 100
    }
    
    try:
        response = session.get(url_votacoes, params=params, timeout=15)
        response.raise_for_status()
        votacoes = response.json().get("dados", [])
    except Exception:
        return []
        
    nominais = []
    for votacao in votacoes:
        if len(nominais) >= limite:
            break
            
        url_votos = f"{BASE_URL}/votacoes/{votacao['id']}/votos"
        try:
            resp_votos = session.get(url_votos, timeout=15)
            if resp_votos.status_code == 200:
                votos = resp_votos.json().get("dados", [])
                if votos:
                    # Salva a lista de votos dentro da votacao
                    votacao["votos_detalhados"] = votos
                    nominais.append(votacao)
        except Exception:
            continue
            
    return nominais

def get_votos_deputado(id_deputado: int) -> List[Dict]:
    """Busca como o deputado votou nas últimas votações nominais."""
    nominais = get_ultimas_votacoes_nominais()
    
    resultados = []
    for votacao in nominais:
        votos = votacao.get("votos_detalhados", [])
        voto_deputado = next((v for v in votos if v.get("deputado_", {}).get("id") == id_deputado), None)
        
        resultados.append({
            "id": votacao["id"],
            "data": votacao.get("dataHoraRegistro", votacao.get("data", "")),
            "descricao": votacao.get("descricao", "Sem descrição"),
            "voto": voto_deputado.get("tipoVoto") if voto_deputado else "Ausente / Não votou"
        })
        
    return resultados
