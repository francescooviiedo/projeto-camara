import os
import time
import requests
from database import get_gasto_mensal, save_gasto_mensal

BASE_URL = "https://api.portaldatransparencia.gov.br/api-de-dados"

def extrair_valor(valor_str):
    if not valor_str:
        return 0.0
    if isinstance(valor_str, (int, float)):
        return float(valor_str)
    try:
        val = str(valor_str).replace('.', '').replace(',', '.')
        return float(val)
    except:
        return 0.0

def fetch_gasto_mes_api(mes_ano, chave_api):
    headers = {"chave-api-dados": chave_api}
    params = {
        "mesExtratoInicio": mes_ano,
        "mesExtratoFim": mes_ano,
        "codigoOrgao": "20101",
        "pagina": 1
    }
    
    valor_total = 0.0
    valor_sigiloso = 0.0
    
    while True:
        try:
            response = requests.get(f"{BASE_URL}/cartoes", headers=headers, params=params, timeout=15)
            if response.status_code != 200:
                break
                
            dados = response.json()
            if not dados:
                break
                
            for item in dados:
                valor_transacao = item.get("valorTransacao", "0")
                val = extrair_valor(valor_transacao)
                valor_total += val
                
                # Checa se é sigiloso
                favorecido = item.get("estabelecimento", {})
                nome_favorecido = (favorecido.get("nomeEstabelecimento") or "").upper()
                if "SIGILOSO" in nome_favorecido:
                    valor_sigiloso += val
                else:
                    portador = item.get("portador", {})
                    nome_portador = (portador.get("nome") or "").upper()
                    if "SIGILOSO" in nome_portador:
                        valor_sigiloso += val
            
            params["pagina"] += 1
            time.sleep(0.2)  # Rate limit minimal
        except Exception as e:
            print(f"Erro ao buscar dados do mes {mes_ano}: {e}")
            break
            
    return valor_total, valor_sigiloso


def get_gastos_mandato(ano_inicio, ano_fim, chave_api, update_callback=None):
    """
    Retorna uma lista de dados mensais para o mandato especificado.
    Usa cache no banco de dados para meses já consultados.
    """
    resultados = []
    total_meses = (ano_fim - ano_inicio + 1) * 12
    meses_processados = 0
    
    for ano in range(ano_inicio, ano_fim + 1):
        for mes in range(1, 13):
            mes_ano = f"{mes:02d}/{ano}"
            
            # Verifica cache
            cached = get_gasto_mensal(mes_ano)
            if cached is not None and cached["total"] is not None:
                resultados.append({
                    "mes_ano": mes_ano,
                    "total": cached["total"],
                    "sigiloso": cached["sigiloso"]
                })
            else:
                # Busca na API
                if chave_api:
                    if update_callback:
                        update_callback(mes_ano, meses_processados, total_meses)
                    total, sigiloso = fetch_gasto_mes_api(mes_ano, chave_api)
                    save_gasto_mensal(mes_ano, total, sigiloso)
                    resultados.append({
                        "mes_ano": mes_ano,
                        "total": total,
                        "sigiloso": sigiloso
                    })
                else:
                    # Se não houver chave, retorna zero (mas não cacha para poder buscar depois)
                    resultados.append({
                        "mes_ano": mes_ano,
                        "total": 0.0,
                        "sigiloso": 0.0
                    })
            
            meses_processados += 1
            
    return resultados
