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

def get_proposicoes_por_deputado(id_autor: int, ano: Optional[int] = None, pagina: int = 1, itens: int = 10) -> Dict:
    """Busca projetos de lei propostos pelo deputado, com suporte a filtro de ano e paginação."""
    url = f"{BASE_URL}/proposicoes"
    params = {
        "idDeputadoAutor": id_autor,
        "ordem": "DESC",
        "ordenarPor": "id",
        "itens": itens,
        "pagina": pagina
    }
    
    if ano:
        params["ano"] = ano
        
    response = session.get(url, params=params, timeout=15)
    response.raise_for_status()
    payload = response.json()
    
    links = payload.get("links", [])
    has_next = any(link["rel"] == "next" for link in links)
    
    return {
        "dados": payload.get("dados", []),
        "has_next": has_next
    }

@st.cache_data(ttl=3600)
def get_proposicao_detalhes(id_proposicao: int) -> Optional[Dict]:
    """Obtém detalhes de uma proposição específica, focando na urlInteiroTeor."""
    url = f"{BASE_URL}/proposicoes/{id_proposicao}"
    response = session.get(url, timeout=15)
    if response.status_code == 200:
        return response.json().get("dados", {})
    return None
