import requests

def test():
    url = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"
    # test 1
    r1 = requests.get(url, params={'idDeputadoAutor': 204534, 'itens': 1})
    print("Just autor:", r1.headers.get('x-total-count'))
    
    # test 2
    r2 = requests.get(url, params={'idDeputadoAutor': 204534, 'codSituacao': [1140], 'itens': 1})
    print("autor + codSituacao (list):", r2.headers.get('x-total-count'))
    
    # test 3
    r3 = requests.get(url, params={'idDeputadoAutor': 204534, 'codSituacao': '1140', 'itens': 1})
    print("autor + codSituacao (str):", r3.headers.get('x-total-count'))

test()
