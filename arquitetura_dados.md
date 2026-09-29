# Arquitetura de Dados e Cache Local

Este documento descreve a estrutura do banco de dados local (`banco.db`) da aplicação **Transparência Legislativa** e como o fluxo de informações é orquestrado para exibir os dados aos usuários de forma otimizada.

## 1. O Banco de Dados (SQLite)

O sistema utiliza o **SQLite** como motor de banco de dados embutido, gerenciado pelo arquivo `database.py`. O objetivo principal deste banco é atuar como uma camada de **Cache Local**, evitando consultas desnecessárias a APIs externas (Câmara dos Deputados e Google Gemini) que poderiam gerar lentidão e custos adicionais.

O esquema do banco de dados é composto atualmente por duas tabelas principais:

### Tabela `resumos`
Responsável por armazenar os resumos explicativos gerados pela Inteligência Artificial.

* **`id_proposicao` (INTEGER PRIMARY KEY):** O ID único do projeto de lei na Câmara.
* **`resumo` (TEXT NOT NULL):** O texto explicativo simplificado gerado pelo modelo do Google Gemini.

**Por que ela existe?** Extrair o texto de um PDF e enviá-lo ao Gemini pode demorar vários segundos e possui limite de cotas. Quando um usuário pede para explicar um projeto, o sistema primeiro consulta esta tabela. Se o resumo já existir, a exibição é instantânea.

### Tabela `proposicoes`
Responsável por armazenar os metadados de situação de cada projeto de lei.

* **`id_proposicao` (INTEGER PRIMARY KEY):** O ID único do projeto.
* **`cod_situacao` (INTEGER):** Código numérico da Câmara que representa a situação atual do projeto (ex: Transformado em Norma Jurídica, Arquivada, etc.).
* **`ano` (INTEGER):** Ano do projeto, para agilizar os filtros.

**Por que ela existe?** A API da Câmara dos Deputados possui um *bug conhecido* onde não é possível filtrar nativamente projetos de um autor por sua "situação". Para que a UI consiga mostrar esses filtros e a contagem exata, nós salvamos o status detalhado das proposições localmente, viabilizando o filtro pelo lado do servidor da aplicação (client-side na perspectiva da API da Câmara).

---

## 2. Como as Informações chegam ao Usuário

O fluxo de exibição de dados para o usuário foi planejado para maximizar a performance e entregar informações consistentes. Ele se divide nas seguintes etapas:

### Passo A: Busca Inicial (Apenas Listagem)
Quando o usuário seleciona um Deputado, a aplicação faz uma requisição para a API da Câmara para obter a lista básica de todos os projetos de lei criados por aquele parlamentar. Esta lista inicial é rápida, mas carece dos detalhes aprofundados sobre a tramitação (situação atual).

### Passo B: Sincronização Local (Multi-threading)
Após pegar a lista de proposições:
1. O sistema verifica, de forma massiva (`IN`), quais projetos da lista **já estão cacheados** na tabela `proposicoes` do nosso banco local.
2. Identifica os projetos ausentes e faz requisições simultâneas e paralelas (usando `ThreadPoolExecutor` com 20 workers) aos detalhes de cada projeto ausente.
3. Isso reduz o tempo de sincronização de minutos para cerca de 2 a 5 segundos.
4. Os dados recém-buscados são armazenados na tabela `proposicoes`.

### Passo C: Filtragem e Paginação Locais
Como agora temos o status de todos os projetos em memória (e no banco local), o sistema aplica as regras de filtro definidas pelo usuário no Streamlit (ex: exibir apenas projetos "Aprovados" de "2023"). O número **Total de Projetos Encontrados** é calculado sobre o resultado exato dessa filtragem. Em seguida, a lista filtrada é fatiada para exibir apenas 10 itens por vez (Paginação Local), impedindo travamentos na tela.

### Passo D: Componentes UI e Inteligência Artificial
A tela é montada utilizando os `st.expander` do Streamlit:
* **Votações Recentes:** Os últimos votos são exibidos via cache para garantir resposta imediata.
* **Detalhes do Projeto:** Incluem o link para o documento original (PDF).
* **Botão "Explicar com IA":** Este botão tem carregamento preguiçoso (*lazy load*). Apenas quando clicado, ele busca na tabela `resumos`. Caso seja a primeira vez que alguém pede explicação, a aplicação baixa o PDF, extrai os textos, aciona o LLM (Gemini 3.5 Flash), salva na tabela `resumos` e depois o exibe na tela.

Este conjunto de soluções – Cache de LLM, Processamento Paralelo de Detalhes, Paginação em Memória – faz da aplicação uma plataforma extremamente ágil e resiliente à instabilidade dos dados abertos governamentais.
