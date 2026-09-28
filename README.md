# Transparência Legislativa (Projeto Câmara)

Este projeto é uma aplicação construída com [Streamlit](https://streamlit.io/) para analisar, resumir e trazer transparência aos dados do Legislativo (deputados, proposições, gastos de mandato, etc), integrando com APIs públicas da Câmara e do Portal da Transparência, e utilizando IA (Google Gemini) para gerar resumos automáticos das proposições.

## Como executar o projeto localmente

### 1. Pré-requisitos
Certifique-se de ter o Python instalado em sua máquina.

### 2. Clonar o repositório
Caso não tenha clonado ainda:
```bash
git clone git@github.com:francescooviiedo/projeto-camara.git
cd projeto-camara
```

### 3. Criar e ativar o ambiente virtual
É altamente recomendável utilizar um ambiente virtual (`venv`) para evitar conflitos de pacotes.
```bash
python -m venv venv
source venv/bin/activate  # No Windows, utilize: venv\Scripts\activate
```

### 4. Instalar as dependências
Com o ambiente ativado, instale as bibliotecas necessárias:
```bash
pip install -r requirements.txt
```

### 5. Configurar as variáveis de ambiente (Chaves de API)
O projeto consome APIs externas e necessita de chaves de acesso. **Nunca faça o commit de suas chaves reais no GitHub!** (Os arquivos de ambiente já estão ignorados pelo `.gitignore`).

Crie os arquivos `.env` e `.env.local` na raiz do projeto e preencha com suas chaves.

**Exemplo de conteúdo para o arquivo `.env`:**
```env
# Chave de API para gerar os resumos com IA
GEMINI_API_KEY=sua_chave_gemini_aqui

# Chave de API para o Portal da Transparência
TRANSPARENCIA_API_KEY=sua_chave_transparencia_aqui
```

**Exemplo de conteúdo para o arquivo `.env.local`:**
```env
# Token de integração para acesso ao Notion (exemplo: Board de desenvolvimento)
NOTION_TOKEN=seu_token_notion_aqui
```

### 6. Executar a aplicação
Após configurar as chaves, inicie o servidor do Streamlit:
```bash
streamlit run app.py
```
O seu navegador padrão deverá abrir automaticamente a aplicação (normalmente em `http://localhost:8501`).
