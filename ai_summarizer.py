import io
import requests
import pdfplumber
import google.generativeai as genai
import os


def configurar_gemini():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("A variável de ambiente GEMINI_API_KEY não foi configurada. Configure no arquivo app.py ou via terminal.")
    genai.configure(api_key=api_key)

def extract_text_from_url(url: str) -> str:
    """Baixa o arquivo da Câmara (geralmente PDF) e extrai o texto."""
    # A API da câmara pode redirecionar para um PDF ou retornar HTML.
    # Adicionamos um cabeçalho simples.
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers, stream=True)
    response.raise_for_status()
    
    # Se o Content-Type não for pdf, talvez seja um documento html (ocorre em alguns formatos antigos)
    if 'application/pdf' not in response.headers.get('Content-Type', '').lower():
        # Vamos assumir que é um PDF mesmo assim, o link da Câmara costuma devolver binário em prop_mostrarintegra
        pass
        
    text_content = ""
    try:
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            if len(pdf.pages) > 10:
                raise Exception(f"Trava de segurança ativada: O documento tem {len(pdf.pages)} páginas. O limite atual é de 10 páginas para evitar alto custo e lentidão na API.")
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"
    except Exception as e:
        raise Exception(f"Falha ao ler o PDF ou excedeu limite: {e}")
                
    return text_content

def summarize_proposicao(url_inteiro_teor: str) -> str:
    """Extrai texto da proposição, valida o tamanho e envia pro Gemini resumir."""
    try:
        texto = extract_text_from_url(url_inteiro_teor)
    except Exception as e:
        return str(e)
        
    if not texto.strip():
        return "O documento não contém texto extraível ou é uma imagem escaneada."
                
    try:
        configurar_gemini()
        # Utilizando o modelo mais rápido e barato disponível
        model = genai.GenerativeModel('gemini-3.5-flash')
        
        prompt = (
            "Você é um assistente que ajuda cidadãos a entender projetos de lei. "
            "Eu vou te enviar o texto de um projeto de lei da Câmara dos Deputados do Brasil. "
            "Sua tarefa é ler o texto (focando principalmente na parte da 'Justificativa', se existir), "
            "e escrever um resumo muito simples, didático e direto (em até 2 parágrafos) sobre "
            "o que esse projeto propõe mudar na sociedade e o porquê.\n\n"
            f"TEXTO DO PROJETO:\n{texto}"
        )
        
        response = model.generate_content(prompt)
        return response.text
        
    except ValueError as ve:
        return str(ve)
    except Exception as e:
        return f"Erro na API da IA (Gemini): {str(e)}"
