import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA & ESTILIZAÇÃO CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Sistema de Gestão de Projetos e Processos",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# Estilização CSS Personalizada
st.markdown("""
    <style>
        .stApp {
            background-color: #f8fafc;
        }
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border-left: 5px solid #2563eb;
            padding: 16px;
            border-radius: 8px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        section[data-testid="stSidebar"] {
            background-color: #0f172a;
        }
        section[data-testid="stSidebar"] * {
            color: #f8fafc !important;
        }
        div.stButton > button:first-child {
            background-color: #2563eb;
            color: white;
            font-weight: 600;
            border-radius: 6px;
            border: none;
            padding: 8px 16px;
            transition: all 0.3s ease;
        }
        div.stButton > button:first-child:hover {
            background-color: #1d4ed8;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CONEXÃO COM O SUPABASE
# -----------------------------------------------------------------------------
SUPABASE_URL = "https://sldhiftwxqynjcnpaysl.supabase.co"
SUPABASE_KEY = "sb_publishable_m9NM4QJ433cSXQLvM-4PRw_NMEKEorT"


@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


try:
    supabase = init_supabase()
except Exception as e:
    st.error("❌ Erro ao conectar ao Supabase. Verifique suas credenciais em .streamlit/secrets.toml")
    st.stop()


# Funções auxiliares com busca segura
def get_projetos() -> pd.DataFrame:
    try:
        res = supabase.table("projetos").select("*").execute()
        if res.data:
            return pd.DataFrame(res.data)
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def get_processos(codigo_projeto=None) -> pd.DataFrame:
    try:
        query = supabase.table("processos").select("*")
        if codigo_projeto:
            query = query.eq("codigo_projeto", codigo_projeto)
        res = query.order("ordem").execute()
        if res.data:
            return pd.DataFrame(res.data)
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


# -----------------------------------------------------------------------------
# MENU LATERAL
# -----------------------------------------------------------------------------
st.sidebar.title("🚀 Painel de Controle")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navegação",
    [
        "Dashboard Principal",
        "Cadastro de Projetos",
        "Cadastro de Processos",
        "Gantt & Reagendamento Cascata",
        "Relatório por Departamento"
    ]
)

# -----------------------------------------------------------------------------
# 1. DASHBOARD PRINCIPAL
# -----------------------------------------------------------------------------
if menu == "Dashboard Principal":
    st.title("📊 Visão Geral de Projetos e Metas")
    st.markdown("Acompanhamento executivo de demandas, processos e indicadores de desempenho.")

    df_proj = get_projetos()
    df_proc = get_processos()

    if df_proj.empty:
        st.warning(
            "⚠️️ Nenhuma informação encontrada. Se você ainda não criou as tabelas no Supabase, execute o código SQL disponibilizado.")
    else:
        # Métricas defensivas no topo
        m1, m2, m3, m4, m5 = st.columns(5)

        total_proj = df_proj.shape[0]
        ativos_proj = df_proj[df_proj['status_projeto'] == 'Em Andamento'].shape[0] if 'status_projeto' in df_proj.columns else 0

        m1.metric("Projetos Totais", total_proj)
        m2.metric("Projetos Ativos", ativos_proj)

        if not df_proc.empty and 'status' in df_proc.columns:
            m_cumprida = df_proc[df_proc['status'] == 'Cumprida'].shape[0]
            m_atraso = df_proc[df_proc['status'] == 'Cumprida em Atraso'].shape[0]
            m_pendente = df_proc[df_proc['status'] == 'Pendente'].shape[0]
            m_nao_cumprida = df_proc[df_proc['status'] == 'Não Cumprida'].shape[0]

            m3.metric("Metas Cumpridas", m_cumprida)
            m4.metric("Cumpridas em Atraso", m_atraso)
            m5.metric("Pendentes / Atrasadas", f"{m_pendente} / {m_nao_cumprida}")
        else:
            m3.metric("Metas Cumpridas", 0)
            m4.metric("Cumpridas em Atraso", 0)
            m5.metric("Pendentes / Atrasadas", "0 / 0")

        st.markdown("---")

        # Gráficos em Dashboard
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("Projetos por Departamento")
            if 'departamento' in df_proj.columns:
                dep_counts = df_proj['departamento'].value_counts().reset_index()
                dep_counts.columns = ['Departamento', 'Quantidade']
                fig_dep = px.bar(
                    dep_counts, x='Departamento', y='Quantidade',
                    text='Quantidade',
                    color_discrete_sequence=['#2563eb']
                )
                fig_dep.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_dep, use_container_width=True)

        with col_g2:
            st.subheader("Distribuição de Status das Metas")
            if not df_proc.empty and 'status' in df_proc.columns:
                st_counts = df_proc['status'].value_counts().reset_index()
                st_counts.columns = ['Status', 'Quantidade']
                fig_status = px.pie(
                    st_counts, names='Status', values='Quantidade', hole=0.4,
                    color='Status',
                    color_discrete_map={
                        'Cumprida': '#22c55e',
                        'Cumprida em Atraso': '#eab308',
                        'Pendente': '#3b82f6',
                        'Não Cumprida': '#ef4444'
                    }
                )
                fig_status.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_status, use_container_width=True)
            else:
                st.info("Nenhum processo/meta cadastrado.")

# -----------------------------------------------------------------------------
# 2. CADASTRO DE PROJETOS
# -----------------------------------------------------------------------------
elif menu == "Cadastro de Projetos":
    st.title("📁 Cadastro de Projetos")
    st.markdown("Preencha as informações para registrar um novo projeto no sistema.")

    with st.form("form_projeto", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        codigo = c1.text_input("Código do Projeto*")
        nome = c2.text_input("Nome do Projeto*")
        departamento = c3.text_input("Departamento")

        c4, c5, c6 = st.columns(3)
        setor = c4.text_input("Setor")
        responsavel = c5.text_input("Responsável")
        doc_demanda = c6.text_input("Doc. Demanda")

        c7, c8, c9 = st.columns(3)
        data_receb_demanda = c7.date_input("Data Rec. Demanda")
        data_inicio = c8.date_input("Data Início")
        data_fim_prevista = c9.date_input("Data Fim Prevista")

        status_projeto = st.selectbox("Status do Projeto", ["Em Andamento", "Pendente", "Concluído", "Cancelado"])
        justificativa = st.text_area("Justificativa")
        obs = st.text_area("Observações")

        salvar = st.form_submit_button("💾 Salvar Projeto")

        if salvar:
            if not codigo or not nome:
                st.error("Os campos Código e Nome do Projeto são obrigatórios!")
            else:
                try:
                    payload = {
                        "codigo": codigo,
                        "nome": nome,
                        "departamento": departamento,
                        "setor": setor,
                        "responsavel": responsavel,
                        "data_inicio": str(data_inicio),
                        "data_fim_prevista": str(data_fim_prevista),
                        "data_receb_demanda": str(data_receb_demanda),
                        "doc_demanda": doc_demanda,
                        "status_projeto": status_projeto,
                        "justificativa": justificativa,
                        "obs": obs
                    }
                    supabase.table("projetos").insert(payload).execute()
                    st.success("Projeto cadastrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar projeto: {e}")

    st.markdown("---")
    st.subheader("📋 Projetos Cadastrados")
    df_p = get_projetos()
    if not df_p.empty:
        st.dataframe(df_p, use_container_width=True)

# -----------------------------------------------------------------------------
# 3. CADASTRO DE PROCESSOS
# -----------------------------------------------------------------------------
elif menu == "Cadastro de Processos":
    st.title("⚙️ Cadastro de Processos/Etapas")

    df_proj = get_projetos()
    if df_proj.empty or 'codigo' not in df_proj.columns:
        st.warning("Cadastre pelo menos um projeto antes de adicionar processos.")
    else:
        with st.form("form_processo", clear_on_submit=True):
            c1, c2 = st.columns(2)
            codigo_proj = c1.selectbox("Selecione o Projeto Vinculado*", df_proj["codigo"].tolist())
            codigo_proc = c2.text_input("Código do Processo*")

            c3, c4 = st.columns(2)
            nome_proc = c3.text_input("Nome do Processo / Meta*")
            ordem = c4.number_input("Ordem de Execução (Sequência)", min_value=1, value=1)

            c5, c6, c7 = st.columns(3)
            data_inicial = c5.date_input("Data Inicial")
            data_final = c6.date_input("Data Final")
            status = c7.selectbox("Status da Meta", ["Pendente", "Cumprida", "Cumprida em Atraso", "Não Cumprida"])

            justificativa = st.text_area("Justificativa (Se houver alteração/atraso)")
            obs = st.text_area("Observações")

            salvar_proc = st.form_submit_button("💾 Salvar Processo")

            if salvar_proc:
                if not codigo_proc or not nome_proc:
                    st.error("Código e Nome do Processo são obrigatórios!")
                else:
                    try:
                        payload = {
                            "codigo": codigo_proc,
                            "codigo_projeto": codigo_proj,
                            "nome_processo": nome_proc,
                            "ordem": int(ordem),
                            "data_inicial": str(data_inicial),
                            "data_final": str(data_final),
                            "status": status,
                            "justificativa": justificativa,
                            "obs": obs
                        }
                        supabase.table("processos").insert(payload).execute()
                        st.success("Processo cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar processo: {e}")

        st.markdown("---")
        st.subheader("📋 Lista de Processos")
        st.dataframe(get_processos(), use_container_width=True)

# -----------------------------------------------------------------------------
# 4. GANTT & REAGENDAMENTO EM CASCATA
# -----------------------------------------------------------------------------
elif menu == "Gantt & Reagendamento Cascata":
    st.title("📅 Cronograma de Processos (Gantt) & Prorrogação em Cascata")
    st.markdown("Altere a data final de um processo para **empurrar automaticamente** os processos seguintes na sequência de datas.")

    df_proj = get_projetos()
    if not df_proj.empty and 'codigo' in df_proj.columns:
        proj_sel = st.selectbox("Selecione um Projeto", df_proj["codigo"].tolist())
        df_proc = get_processos(proj_sel)

        if not df_proc.empty and 'ordem' in df_proc.columns:
            df_proc['data_inicial'] = pd.to_datetime(df_proc['data_inicial'])
            df_proc['data_final'] = pd.to_datetime(df_proc['data_final'])
            df_proc = df_proc.sort_values("ordem")

            # Visualização do Cronograma Gantt
            fig_gantt = px.timeline(
                df_proc,
                x_start="data_inicial",
                x_end="data_final",
                y="nome_processo",
                color="status",
                title=f"Linha do Tempo de Execução - Projeto {proj_sel}",
                labels={"nome_processo": "Processo / Etapa"},
                color_discrete_map={
                    'Cumprida': '#22c55e',
                    'Cumprida em Atraso': '#eab308',
                    'Pendente': '#3b82f6',
                    'Não Cumprida': '#ef4444'
                }
            )
            fig_gantt.update_yaxes(autorange="reversed")
            fig_gantt.update_layout(template="plotly_white")
            st.plotly_chart(fig_gantt, use_container_width=True)

            st.markdown("---")
            st.subheader("⏩ Prorrogar Processo e Ajustar Datas Sequenciais")

            with st.form("form_prorrogacao"):
                proc_sel = st.selectbox("Selecione o Processo para Prorrogar", df_proc["codigo"].tolist())
                dias_adiar = st.number_input("Adicionar Quantos Dias de Prorrogação?", min_value=1, value=1)
                justificativa = st.text_area("Justificativa para Prorrogação*")

                btn_prorrogar = st.form_submit_button("⚡ Aplicar Prorrogação em Cascata")

                if btn_prorrogar:
                    if not justificativa:
                        st.error("Informe obrigatoriamente a justificativa para a prorrogação.")
                    else:
                        try:
                            row_proc = df_proc[df_proc['codigo'] == proc_sel].iloc[0]
                            ordem_alvo = row_proc['ordem']

                            for _, r in df_proc.iterrows():
                                if r['ordem'] >= ordem_alvo:
                                    n_ini = r['data_inicial'] + timedelta(days=int(dias_adiar))
                                    n_fim = r['data_final'] + timedelta(days=int(dias_adiar))

                                    payload = {
                                        "data_inicial": n_ini.strftime('%Y-%m-%d'),
                                        "data_final": n_fim.strftime('%Y-%m-%d')
                                    }

                                    if r['codigo'] == proc_sel:
                                        payload["data_prorrogacao"] = n_fim.strftime('%Y-%m-%d')
                                        payload["justificativa"] = justificativa

                                    supabase.table("processos").update(payload).eq("codigo", r['codigo']).execute()

                            st.success("Cronograma recalculado e datas atualizadas em cascata!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao processar reagendamento: {e}")
        else:
            st.info("Nenhum processo vinculado a este projeto.")
    else:
        st.info("Nenhum projeto cadastrado.")

# -----------------------------------------------------------------------------
# 5. RELATÓRIO POR DEPARTAMENTO
# -----------------------------------------------------------------------------
elif menu == "Relatório por Departamento":
    st.title("📄 Relatórios por Departamento")

    df_proj = get_projetos()
    df_proc = get_processos()

    if not df_proj.empty and 'departamento' in df_proj.columns:
        lista_deps = ["Todos"] + list(df_proj['departamento'].dropna().unique())
        dep_filtro = st.selectbox("Filtrar por Departamento", lista_deps)

        if dep_filtro != "Todos":
            df_proj = df_proj[df_proj['departamento'] == dep_filtro]

        for _, proj in df_proj.iterrows():
            with st.expander(f"📁 Projeto: {proj['nome']} | Código: {proj['codigo']} | Status: {proj.get('status_projeto', 'N/A')}"):
                col1, col2, col3 = st.columns(3)
                col1.write(f"**Departamento:** {proj.get('departamento', 'N/A')}")
                col1.write(f"**Setor:** {proj.get('setor', 'N/A')}")
                col2.write(f"**Responsável:** {proj.get('responsavel', 'N/A')}")
                col2.write(f"**Data Início:** {proj.get('data_inicio', 'N/A')}")
                col3.write(f"**Fim Previsto:** {proj.get('data_fim_prevista', 'N/A')}")
                col3.write(f"**Doc. Demanda:** {proj.get('doc_demanda', 'N/A')}")

                if not df_proc.empty and 'codigo_projeto' in df_proc.columns:
                    procs_p = df_proc[df_proc['codigo_projeto'] == proj['codigo']]
                    st.markdown("#### ⚙️ Processos / Metas Associadas:")
                    if not procs_p.empty:
                        cols_exibir = [c for c in
                                       ['ordem', 'codigo', 'nome_processo', 'data_inicial', 'data_final', 'data_prorrogacao', 'status',
                                        'justificativa'] if c in procs_p.columns]
                        st.dataframe(procs_p[cols_exibir], use_container_width=True)
                    else:
                        st.info("Nenhum processo associado a este projeto.")