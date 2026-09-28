import streamlit as st
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do .env
load_dotenv()

from api_camara import get_partidos, get_deputados_por_partido, get_proposicoes_por_deputado, get_proposicao_detalhes
from database import get_resumo, save_resumo
from ai_summarizer import summarize_proposicao
from api_transparencia import get_gastos_mandato

st.set_page_config(page_title="Transparência Legislativa", layout="wide")

# Sidebar para Configurações
with st.sidebar:
    st.header("⚙️ Configurações")
    
    chave_atual = os.environ.get("GEMINI_API_KEY", "")
    api_key = st.text_input("Gemini API Key", value=chave_atual, type="password", help="Pegue sua chave gratuita no Google AI Studio")
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key
        
    chave_transparencia_atual = os.environ.get("TRANSPARENCIA_API_KEY", "")
    api_key_gov = st.text_input("Portal da Transparência API Key", value=chave_transparencia_atual, type="password", help="Pegue sua chave no portal da transparência")
    if api_key_gov:
        os.environ["TRANSPARENCIA_API_KEY"] = api_key_gov
    
    if chave_atual and chave_transparencia_atual:
        st.success("✅ Chaves configuradas!")
    else:
        st.markdown("Insira suas chaves de API para habilitar todos os recursos.")
    
    st.divider()
    pagina = st.radio("Módulo", ["Projetos de Deputados", "Comparativo Presidencial"])
    st.divider()
    st.markdown("Desenvolvido para análise de Dados Abertos.")

if pagina == "Comparativo Presidencial":
    st.title("🏛️ Comparativo de Gastos Presidenciais (Cartão Corporativo)")
    st.markdown("Comparação de gastos utilizando dados do Portal da Transparência.")
    
    col1, col2 = st.columns(2)
    
    mandatos = {
        "Lula (2023-Atual)": (2023, 2026),
        "Bolsonaro (2019-2022)": (2019, 2022),
        "Temer (2016-2018)": (2016, 2018),
        "Dilma (2011-2016)": (2011, 2016),
        "Lula (2003-2010)": (2003, 2010)
    }
    
    with col1:
        st.subheader("Mandato A")
        mandato_a = st.selectbox("Selecione o Mandato A", list(mandatos.keys()), index=1)
    
    with col2:
        st.subheader("Mandato B")
        mandato_b = st.selectbox("Selecione o Mandato B", list(mandatos.keys()), index=0)
        
    st.divider()
    
    if st.button("Buscar Comparativo"):
        chave = os.environ.get("TRANSPARENCIA_API_KEY")
        if not chave:
            st.error("⚠️ Configure a chave da API do Portal da Transparência na barra lateral.")
            st.stop()
            
        ano_inicio_a, ano_fim_a = mandatos[mandato_a]
        ano_inicio_b, ano_fim_b = mandatos[mandato_b]
        
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown(f"### {mandato_a}")
            progress_a = st.progress(0)
            status_a = st.empty()
            
            def update_a(mes, processed, total):
                if total > 0:
                    progress_a.progress(processed / total)
                status_a.text(f"Buscando {mes}...")
                
            dados_a = get_gastos_mandato(ano_inicio_a, ano_fim_a, chave, update_callback=update_a)
            progress_a.empty()
            status_a.empty()
            
            total_a = sum(d["total"] for d in dados_a)
            sigilo_a = sum(d["sigiloso"] for d in dados_a)
            
            st.metric("Total Gasto", f"R$ {total_a:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.metric("Gasto Sigiloso", f"R$ {sigilo_a:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            chart_data_a = {d["mes_ano"]: d["total"] for d in dados_a}
            st.bar_chart(chart_data_a)
            
        with c2:
            st.markdown(f"### {mandato_b}")
            progress_b = st.progress(0)
            status_b = st.empty()
            
            def update_b(mes, processed, total):
                if total > 0:
                    progress_b.progress(processed / total)
                status_b.text(f"Buscando {mes}...")
                
            dados_b = get_gastos_mandato(ano_inicio_b, ano_fim_b, chave, update_callback=update_b)
            progress_b.empty()
            status_b.empty()
            
            total_b = sum(d["total"] for d in dados_b)
            sigilo_b = sum(d["sigiloso"] for d in dados_b)
            
            st.metric("Total Gasto", f"R$ {total_b:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.metric("Gasto Sigiloso", f"R$ {sigilo_b:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            chart_data_b = {d["mes_ano"]: d["total"] for d in dados_b}
            st.bar_chart(chart_data_b)

    st.stop()

st.title("🔎 Explorador de Projetos de Lei com IA")
st.markdown("Navegue pelos Partidos, escolha um Deputado e veja os resumos dos seus projetos de lei recentes gerados via IA e guardados localmente no banco.")

# 1. Selecionar Partido
st.subheader("1. Selecione um Partido")
partidos = get_partidos()
opcoes_partidos = {p['sigla']: p for p in partidos}
partido_selecionado = st.selectbox("Partido", [""] + list(opcoes_partidos.keys()), format_func=lambda x: x if x else "Selecione...")

if partido_selecionado:
    # 2. Selecionar Deputado
    st.subheader(f"2. Deputados do {partido_selecionado}")
    with st.spinner("Buscando deputados..."):
        deputados = get_deputados_por_partido(partido_selecionado)
        
    opcoes_deputados = {d['nome']: d for d in deputados}
    deputado_nome = st.selectbox("Deputado", [""] + list(opcoes_deputados.keys()), format_func=lambda x: x if x else "Selecione...")
    
    if deputado_nome:
        deputado = opcoes_deputados[deputado_nome]
        
        # Header do Deputado
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(deputado.get('urlFoto'), width=100)
        with col2:
            st.write(f"**Nome:** {deputado['nome']}")
            st.write(f"**Estado:** {deputado['siglaUf']}")
            
        st.divider()
        
        # 3. Lista de Proposições com Filtro e Paginação
        st.subheader("3. Projetos Propostos")
        
        with st.expander("📖 Dicionário: Entenda a 'Situação Atual' de um Projeto"):
            st.markdown("""
            O caminho de um projeto de lei na Câmara pode ser complexo. Aqui estão os principais status que você vai encontrar:
            
            * **Apresentação de Proposição:** O deputado acabou de submeter o projeto. A jornada dele mal começou.
            * **Aguardando Designação de Relator:** O projeto está em uma comissão aguardando que um deputado seja escolhido para ler e dar o seu parecer (opinião oficial).
            * **Apensado (Apensação):** Já existia um projeto mais antigo falando da mesma coisa. Esse projeto foi "anexado" ao mais velho para serem julgados juntos.
            * **Pronto para Pauta / Incluído na Ordem do Dia:** Já passou pelos relatores e está na fila para ser votado (na comissão ou no plenário principal).
            * **Aprovado:** Passou pela votação da Câmara. (Geralmente vai para o Senado depois).
            * **Arquivado:** O projeto "morreu". Pode ter sido rejeitado, retirado pelo autor, ou a legislatura acabou sem ele ser votado.
            * **Transformado em Norma Jurídica:** Sucesso total. Passou pela Câmara, pelo Senado e foi sancionado pelo Presidente. Virou Lei.
            """)
        
        col_ano, col_empty = st.columns([1, 3])
        with col_ano:
            ano_opcao = st.selectbox("Filtrar por Ano", ["Todos", 2026, 2025, 2024, 2023, 2022, 2021, 2020])
            ano_filtro = None if ano_opcao == "Todos" else ano_opcao
            
        # Estado de paginação baseado no deputado e no filtro de ano
        state_key = f"pagina_{deputado['id']}_{ano_filtro}"
        if state_key not in st.session_state:
            st.session_state[state_key] = 1
            
        pagina_atual = st.session_state[state_key]

        with st.spinner("Buscando projetos de lei..."):
            resultado = get_proposicoes_por_deputado(deputado['id'], ano=ano_filtro, pagina=pagina_atual)
            proposicoes = resultado["dados"]
            has_next = resultado["has_next"]
            
        if not proposicoes:
            st.info("Nenhuma proposição encontrada com estes filtros.")
        else:
            for prop in proposicoes:
                ementa_curta = prop.get('ementa', 'Sem ementa')
                titulo_expander = f"{prop['siglaTipo']} {prop['numero']}/{prop['ano']} - {ementa_curta[:100]}{'...' if len(ementa_curta) > 100 else ''}"
                
                with st.expander(titulo_expander):
                    id_prop = prop['id']
                    
                    # Busca os detalhes extras na hora para pegar status e o PDF
                    detalhes = get_proposicao_detalhes(id_prop) or {}
                    status_prop = detalhes.get("statusProposicao", {})
                    url_doc = detalhes.get("urlInteiroTeor")
                    
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.write(f"**Data de Apresentação:** {prop.get('dataApresentacao', '')[:10]}")
                    with col_info2:
                        situacao = status_prop.get('descricaoTramitacao') or "Em tramitação"
                        st.write(f"**Situação Atual:** {situacao}")
                        
                    if url_doc:
                        st.markdown(f"[🔗 **Ler Documento Oficial (PDF) Completo**]({url_doc})")
                    else:
                        st.write("*(Documento oficial não disponível no momento)*")

                    st.markdown("#### Resumo Oficial da Câmara")
                    st.write(prop.get('ementa', 'Resumo não disponível.'))
                    
                    st.divider()
                    st.markdown("#### Tradutor IA")
                    
                    if st.button(f"✨ Explicar com IA (Simplificar)", key=f"btn_{id_prop}"):
                        if not os.environ.get("GEMINI_API_KEY"):
                            st.warning("⚠️ Você precisa configurar a Gemini API Key na barra lateral esquerda primeiro!")
                        else:
                            resumo_cache = get_resumo(id_prop)
                            if resumo_cache:
                                st.success("⚡ Resumo recuperado instantaneamente do banco de dados (Cache):")
                                st.write(resumo_cache)
                            else:
                                with st.spinner("Processando... Baixando PDF original e acionando o Gemini (isso pode levar alguns segundos)..."):
                                    if not url_doc:
                                        st.error("Não foi possível encontrar o documento oficial para este projeto.")
                                    else:
                                        resumo_novo = summarize_proposicao(url_doc)
                                        if not str(resumo_novo).startswith("Erro") and "Trava de segurança" not in str(resumo_novo):
                                            save_resumo(id_prop, resumo_novo)
                                        st.info("🤖 Explicação gerada pela IA:")
                                        st.write(resumo_novo)
            
            # Controles de Paginação UI
            st.markdown("<br>", unsafe_allow_html=True)
            col_prev, col_page, col_next = st.columns([1, 2, 1])
            with col_prev:
                if pagina_atual > 1:
                    if st.button("⬅️ Anterior"):
                        st.session_state[state_key] -= 1
                        st.rerun()
            with col_page:
                st.markdown(f"<div style='text-align: center;'>Página {pagina_atual}</div>", unsafe_allow_html=True)
            with col_next:
                if has_next:
                    if st.button("Próxima ➡️"):
                        st.session_state[state_key] += 1
                        st.rerun()
