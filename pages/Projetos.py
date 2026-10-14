import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime, timedelta, date

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA & ESTILIZAÇÃO CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Gestão de Projetos, Processos e Metas",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

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
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
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
# CONEXÃO COM O SUPABASE (Via Secrets)
# -----------------------------------------------------------------------------
@st.cache_resource
def init_supabase() -> Client:
    SUPABASE_URL = "https://sldhiftwxqynjcnpaysl.supabase.co"
    SUPABASE_KEY = "sb_publishable_m9NM4QJ433cSXQLvM-4PRw_NMEKEorT"
    return create_client(SUPABASE_URL, SUPABASE_KEY)


try:
    supabase = init_supabase()
except Exception as e:
    st.error("❌ Erro ao conectar ao Supabase. Verifique suas credenciais.")
    st.stop()


# -----------------------------------------------------------------------------
# FUNÇÕES DE BUSCA E GERAÇÃO DE CÓDIGOS
# -----------------------------------------------------------------------------
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
        # Mantendo ordenação por data inicial ou ordem caso exista na tabela
        if 'ordem' in supabase.table("processos").select("ordem").limit(1).execute().data[0] if supabase.table("processos").select(
                "ordem").limit(1).execute().data else False:
            res = query.order("ordem").execute()
        else:
            res = query.execute()

        if res.data:
            df = pd.DataFrame(res.data)
            hoje = date.today()
            if 'data_final' in df.columns and 'status' in df.columns:
                for idx, row in df.iterrows():
                    if row['status'] == 'Pendente' and pd.notnull(row['data_final']):
                        dt_fim = pd.to_datetime(row['data_final']).date()
                        if dt_fim < hoje:
                            df.at[idx, 'status'] = 'Atrasado'
            return df
        return pd.DataFrame()
    except Exception:
        # Fallback se a coluna ordem não existir mais na query
        try:
            query = supabase.table("processos").select("*")
            if codigo_projeto:
                query = query.eq("codigo_projeto", codigo_projeto)
            res = query.execute()
            if res.data:
                return pd.DataFrame(res.data)
        except:
            pass
        return pd.DataFrame()


def gerar_codigo_projeto() -> str:
    """Gera um código de projeto automático."""
    try:
        df = get_projetos()
        count = len(df) + 1
        ano_atual = datetime.now().strftime("%Y")
        return f"PRJ-{ano_atual}-{count:03d}"
    except Exception:
        return f"PRJ-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def gerar_codigo_processo() -> str:
    """Gera um código de processo/meta automático."""
    try:
        df = get_processos()
        count = len(df) + 1 if not df.empty else 1
        ano_atual = datetime.now().strftime("%Y")
        return f"PRC-{ano_atual}-{count:03d}"
    except Exception:
        return f"PRC-{datetime.now().strftime('%Y%m%d%H%M%S')}"


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
        "Cadastro de Processos / Metas",
        "Gantt & Reagendamento Cascata",
        "Gestão e Atualização de Metas",
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
        st.warning("⚠️ Nenhum projeto encontrado no banco de dados.")
    else:
        m1, m2, m3, m4, m5 = st.columns(5)

        total_proj = df_proj.shape[0]
        ativos_proj = df_proj[df_proj['status_projeto'] == 'Em Andamento'].shape[0] if 'status_projeto' in df_proj.columns else 0

        m1.metric("Projetos Totais", total_proj)
        m2.metric("Projetos Ativos", ativos_proj)

        if not df_proc.empty and 'status' in df_proc.columns:
            m_cumprida = df_proc[df_proc['status'] == 'Cumprida'].shape[0]
            m_atraso_cumprida = df_proc[df_proc['status'] == 'Cumprida em Atraso'].shape[0]
            m_pendente = df_proc[df_proc['status'] == 'Pendente'].shape[0]
            m_atrasadas = df_proc[df_proc['status'] == 'Atrasado'].shape[0] + df_proc[df_proc['status'] == 'Não Cumprida'].shape[0]

            m3.metric("Metas Cumpridas", m_cumprida)
            m4.metric("Cumpridas em Atraso", m_atraso_cumprida)
            m5.metric("Pendentes / Atrasadas", f"{m_pendente} / {m_atrasadas}")
        else:
            m3.metric("Metas Cumpridas", 0)
            m4.metric("Cumpridas em Atraso", 0)
            m5.metric("Pendentes / Atrasadas", "0 / 0")

        st.markdown("---")

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
                        'Atrasado': '#ef4444',
                        'Não Cumprida': '#991b1b'
                    }
                )
                fig_status.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_status, use_container_width=True)

# -----------------------------------------------------------------------------
# 2. CADASTRO DE PROJETOS
# -----------------------------------------------------------------------------
elif menu == "Cadastro de Projetos":
    st.title("📁 Cadastro de Projetos")

    df_p = get_projetos()
    modo_edicao = False
    projeto_selecionado = None

    if not df_p.empty:
        st.markdown("💡 *Selecione um projeto abaixo caso queira carregar os dados para edição ou cadastre um novo.*")
        lista_opcoes = ["-- Cadastrar Novo Projeto --"] + [f"{row['codigo']} - {row['nome']}" for _, row in df_p.iterrows()]
        escolha = st.selectbox("Ação / Selecionar Projeto", lista_opcoes)

        if escolha != "-- Cadastrar Novo Projeto --":
            codigo_escolhido = escolha.split(" - ")[0]
            projeto_selecionado = df_p[df_p['codigo'] == codigo_escolhido].iloc[0]
            modo_edicao = True

    if modo_edicao and projeto_selecionado is not None:
        st.info(f"✏️ Editando o projeto: **{projeto_selecionado['codigo']}**")
        def_codigo = projeto_selecionado['codigo']
        def_nome = projeto_selecionado.get('nome', '')
        def_departamento = projeto_selecionado.get('departamento', '')
        def_setor = projeto_selecionado.get('setor', '')
        def_responsavel = projeto_selecionado.get('responsavel', '')
        def_doc = projeto_selecionado.get('doc_demanda', '')

        try:
            def_dt_rec = pd.to_datetime(projeto_selecionado.get('data_receb_demanda', date.today())).date()
        except:
            def_dt_rec = date.today()
        try:
            def_dt_ini = pd.to_datetime(projeto_selecionado.get('data_inicio', date.today())).date()
        except:
            def_dt_ini = date.today()
        try:
            def_dt_fim = pd.to_datetime(projeto_selecionado.get('data_fim_prevista', date.today())).date()
        except:
            def_dt_fim = date.today()

        status_list = ["Em Andamento", "Pendente", "Concluído", "Cancelado"]
        current_status = projeto_selecionado.get('status_projeto', 'Em Andamento')
        def_status_idx = status_list.index(current_status) if current_status in status_list else 0
        def_justificativa = projeto_selecionado.get('justificativa', '')
        def_obs = projeto_selecionado.get('obs', '')
    else:
        def_codigo = gerar_codigo_projeto()
        def_nome = ""
        def_departamento = ""
        def_setor = ""
        def_responsavel = ""
        def_doc = ""
        def_dt_rec = date.today()
        def_dt_ini = date.today()
        def_dt_fim = date.today()
        def_status_idx = 0
        def_justificativa = ""
        def_obs = ""

    with st.form("form_projeto"):
        c1, c2, c3 = st.columns(3)
        codigo = c1.text_input("Código do Projeto (Gerado Automaticamente)", value=def_codigo, disabled=True)
        nome = c2.text_input("Nome do Projeto*", value=def_nome)
        departamento = c3.text_input("Departamento", value=def_departamento)

        c4, c5, c6 = st.columns(3)
        setor = c4.text_input("Setor", value=def_setor)
        responsavel = c5.text_input("Responsável", value=def_responsavel)
        doc_demanda = c6.text_input("Doc. Demanda", value=def_doc)

        c7, c8, c9 = st.columns(3)
        data_receb_demanda = c7.date_input("Data Rec. Demanda", value=def_dt_rec)
        data_inicio = c8.date_input("Data Início", value=def_dt_ini)
        data_fim_prevista = c9.date_input("Data Fim Prevista", value=def_dt_fim)

        status_projeto = st.selectbox("Status do Projeto", ["Em Andamento", "Pendente", "Concluído", "Cancelado"], index=def_status_idx)
        justificativa = st.text_area("Justificativa", value=def_justificativa)
        obs = st.text_area("Observações", value=def_obs)

        texto_botao = "💾 Atualizar Projeto" if modo_edicao else "💾 Salvar Novo Projeto"
        salvar = st.form_submit_button(texto_botao)

        if salvar:
            if not nome:
                st.error("O campo Nome do Projeto é obrigatório!")
            else:
                try:
                    payload = {
                        "codigo": def_codigo,
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
                    if modo_edicao:
                        supabase.table("projetos").update(payload).eq("codigo", def_codigo).execute()
                        st.success("Projeto atualizado com sucesso!")
                    else:
                        supabase.table("projetos").insert(payload).execute()
                        st.success("Projeto cadastrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar projeto: {e}")

    st.markdown("---")
    st.subheader("📋 Projetos Cadastrados")
    df_p_atualizado = get_projetos()
    if not df_p_atualizado.empty:
        st.dataframe(df_p_atualizado, use_container_width=True)

# -----------------------------------------------------------------------------
# 3. CADASTRO DE PROCESSOS / METAS
# -----------------------------------------------------------------------------
elif menu == "Cadastro de Processos / Metas":
    st.title("⚙️ Cadastro e Edição de Processos e Metas")

    df_proj = get_projetos()
    df_proc_all = get_processos()

    if df_proj.empty or 'codigo' not in df_proj.columns:
        st.warning("Cadastre pelo menos um projeto antes de adicionar processos/metas.")
    else:
        # Seção de seleção para edição ou novo cadastro
        modo_edicao_proc = False
        processo_selecionado = None

        if not df_proc_all.empty:
            st.markdown("💡 *Selecione um processo existente para editá-lo ou escolha cadastrar um novo.*")
            lista_opcoes_proc = ["-- Cadastrar Novo Processo/Meta --"] + [f"{r['codigo']} - {r['nome_processo']}" for _, r in
                                                                          df_proc_all.iterrows()]
            escolha_proc = st.selectbox("Ação / Selecionar Processo ou Meta", lista_opcoes_proc)

            if escolha_proc != "-- Cadastrar Novo Processo/Meta --":
                cod_proc_escolhido = escolha_proc.split(" - ")[0]
                processo_selecionado = df_proc_all[df_proc_all['codigo'] == cod_proc_escolhido].iloc[0]
                modo_edicao_proc = True

        # Atribuição de valores iniciais (Edição vs Novo)
        # Mapeando lista de projetos formatada para exibir Código + Nome na pesquisa
        mapa_projetos = {}
        for _, row_p in df_proj.iterrows():
            rotulo_proj = f"{row_p['codigo']} - {row_p['nome']}"
            mapa_projetos[rotulo_proj] = row_p['codigo']

        lista_opcoes_projetos_formatada = list(mapa_projetos.keys())

        if modo_edicao_proc and processo_selecionado is not None:
            st.info(f"✏️ Editando o processo: **{processo_selecionado['codigo']}**")
            def_cod_proc = processo_selecionado['codigo']

            # Index do projeto vinculado formatado
            atual_proj_codigo = processo_selecionado.get('codigo_projeto')
            def_proj_idx = 0
            for idx_p, (rot, cod_p) in enumerate(mapa_projetos.items()):
                if cod_p == atual_proj_codigo:
                    def_proj_idx = idx_p
                    break

            def_nome_proc = processo_selecionado.get('nome_processo', '')

            try:
                def_dt_ini_proc = pd.to_datetime(processo_selecionado.get('data_inicial', date.today())).date()
            except:
                def_dt_ini_proc = date.today()
            try:
                def_dt_fim_proc = pd.to_datetime(processo_selecionado.get('data_final', date.today())).date()
            except:
                def_dt_fim_proc = date.today()

            status_meta_list = ["Pendente", "Cumprida", "Cumprida em Atraso", "Não Cumprida", "Atrasado"]
            cur_status_meta = processo_selecionado.get('status', 'Pendente')
            def_status_meta_idx = status_meta_list.index(cur_status_meta) if cur_status_meta in status_meta_list else 0

            def_just_proc = processo_selecionado.get('justificativa', '')
            def_obs_proc = processo_selecionado.get('obs', '')
        else:
            def_cod_proc = gerar_codigo_processo()
            def_proj_idx = 0
            def_nome_proc = ""
            def_dt_ini_proc = date.today()
            def_dt_fim_proc = date.today()
            def_status_meta_idx = 0
            def_just_proc = ""
            def_obs_proc = ""

        with st.form("form_processo"):
            c1, c2 = st.columns(2)
            projeto_selecionado_rotulo = c1.selectbox("Selecione o Projeto Vinculado*", lista_opcoes_projetos_formatada, index=def_proj_idx)
            codigo_proj = mapa_projetos[projeto_selecionado_rotulo]

            # Campo de código automático e desativado para garantir que não seja acessado/modificado manualmente
            codigo_proc = c2.text_input("Código do Processo/Meta (Automático)*", value=def_cod_proc, disabled=True)

            nome_proc = st.text_input("Nome do Processo / Meta*", value=def_nome_proc)

            c5, c6, c7 = st.columns(3)
            data_inicial = c5.date_input("Data Inicial", value=def_dt_ini_proc)
            data_final = c6.date_input("Data Final (Prazo da Meta)", value=def_dt_fim_proc)
            status = c7.selectbox("Status da Meta", ["Pendente", "Cumprida", "Cumprida em Atraso", "Não Cumprida"],
                                  index=def_status_meta_idx if def_status_meta_idx < 4 else 0)

            justificativa = st.text_area("Justificativa (Se houver alteração/atraso)", value=def_just_proc)
            obs = st.text_area("Observações", value=def_obs_proc)

            texto_botao_proc = "💾 Atualizar Processo/Meta" if modo_edicao_proc else "💾 Salvar Novo Processo/Meta"
            salvar_proc = st.form_submit_button(texto_botao_proc)

            if salvar_proc:
                if not nome_proc:
                    st.error("O Nome do Processo é obrigatório!")
                else:
                    try:
                        payload = {
                            "codigo": def_cod_proc,
                            "codigo_projeto": codigo_proj,
                            "nome_processo": nome_proc,
                            "data_inicial": str(data_inicial),
                            "data_final": str(data_final),
                            "status": status,
                            "justificativa": justificativa,
                            "obs": obs
                        }
                        if modo_edicao_proc:
                            supabase.table("processos").update(payload).eq("codigo", def_cod_proc).execute()
                            st.success("Processo/Meta atualizado com sucesso!")
                        else:
                            supabase.table("processos").insert(payload).execute()
                            st.success("Processo/Meta cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar processo: {e}")

        st.markdown("---")
        st.subheader("📋 Lista Geral de Processos e Metas")
        st.dataframe(get_processos(), use_container_width=True)

# -----------------------------------------------------------------------------
# 4. GANTT & REAGENDAMENTO CASCATA
# -----------------------------------------------------------------------------
elif menu == "Gantt & Reagendamento Cascata":
    st.title("📅 Cronograma (Gantt) & Prorrogação Cascata")

    df_proj = get_projetos()
    if not df_proj.empty and 'codigo' in df_proj.columns:
        # Criando dicionário para exibir Nome do Projeto na seleção do Gantt também
        mapa_proj_gantt = {}
        for _, row_p in df_proj.iterrows():
            mapa_proj_gantt[f"{row_p['codigo']} - {row_p['nome']}"] = row_p['codigo']

        proj_sel_rotulo = st.selectbox("Selecione um Projeto", list(mapa_proj_gantt.keys()))
        proj_sel = mapa_proj_gantt[proj_sel_rotulo]

        df_proc = get_processos(proj_sel)

        if not df_proc.empty:
            df_proc['data_inicial'] = pd.to_datetime(df_proc['data_inicial'])
            df_proc['data_final'] = pd.to_datetime(df_proc['data_final'])

            # Ordenação por data inicial caso a coluna ordem tenha sido removida do banco
            if 'ordem' in df_proc.columns:
                df_proc = df_proc.sort_values("ordem")
            else:
                df_proc = df_proc.sort_values("data_inicial")

            fig_gantt = px.timeline(
                df_proc,
                x_start="data_inicial",
                x_end="data_final",
                y="nome_processo",
                color="status",
                title=f"Linha do Tempo - Projeto {proj_sel}",
                labels={"nome_processo": "Processo / Meta"},
                color_discrete_map={
                    'Cumprida': '#22c55e',
                    'Cumprida em Atraso': '#eab308',
                    'Pendente': '#3b82f6',
                    'Atrasado': '#ef4444',
                    'Não Cumprida': '#991b1b'
                }
            )
            fig_gantt.update_yaxes(autorange="reversed")
            fig_gantt.update_layout(template="plotly_white")
            st.plotly_chart(fig_gantt, use_container_width=True)

            st.markdown("---")
            st.subheader("⏩ Prorrogagão em Cascata")

            with st.form("form_prorrogacao"):
                proc_sel = st.selectbox("Selecione o Processo para Prorrogar", df_proc["codigo"].tolist())
                dias_adiar = st.number_input("Adicionar Quantos Dias?", min_value=1, value=1)
                justificativa = st.text_area("Justificativa da Prorrogação*")

                btn_prorrogar = st.form_submit_button("⚡ Aplicar em Cascata")

                if btn_prorrogar:
                    if not justificativa:
                        st.error("Informe a justificativa!")
                    else:
                        try:
                            row_proc = df_proc[df_proc['codigo'] == proc_sel].iloc[0]

                            # Baseando a cascata na data inicial ou ordem se existir
                            if 'ordem' in df_proc.columns and pd.notnull(row_proc.get('ordem')):
                                ordem_alvo = row_proc['ordem']
                                for _, r in df_proc.iterrows():
                                    if r.get('ordem', 0) >= ordem_alvo:
                                        n_ini = r['data_inicial'] + timedelta(days=int(dias_adiar))
                                        n_fim = r['data_final'] + timedelta(days=int(dias_adiar))

                                        payload = {
                                            "data_inicial": n_ini.strftime('%Y-%m-%d'),
                                            "data_final": n_fim.strftime('%Y-%m-%d')
                                        }

                                        if r['codigo'] == proc_sel:
                                            payload["justificativa"] = justificativa

                                        supabase.table("processos").update(payload).eq("codigo", r['codigo']).execute()
                            else:
                                # Caso não use ordem numérica, prorroga apenas o selecionado e posteriores por data
                                dt_alvo_ini = row_proc['data_inicial']
                                for _, r in df_proc.iterrows():
                                    if r['data_inicial'] >= dt_alvo_ini:
                                        n_ini = r['data_inicial'] + timedelta(days=int(dias_adiar))
                                        n_fim = r['data_final'] + timedelta(days=int(dias_adiar))

                                        payload = {
                                            "data_inicial": n_ini.strftime('%Y-%m-%d'),
                                            "data_final": n_fim.strftime('%Y-%m-%d')
                                        }

                                        if r['codigo'] == proc_sel:
                                            payload["justificativa"] = justificativa

                                        supabase.table("processos").update(payload).eq("codigo", r['codigo']).execute()

                            st.success("Reagendamento executado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao prorrogar: {e}")
        else:
            st.info("Nenhum processo vinculado a este projeto.")

# -----------------------------------------------------------------------------
# 5. GESTÃO E ATUALIZAÇÃO DE METAS
# -----------------------------------------------------------------------------
elif menu == "Gestão e Atualização de Metas":
    st.title("🎯 Gestão Direta de Metas e Entregas")
    st.markdown("Atualize o status da meta de cada processo conforme as entregas forem realizadas.")

    df_proj = get_projetos()
    if not df_proj.empty:
        # Mapeando projetos para mostrar o nome do projeto na pesquisa
        mapa_proj_gestao = {}
        for _, row_p in df_proj.iterrows():
            rotulo = f"{row_p['codigo']} - {row_p['nome']}"
            mapa_proj_gestao[rotulo] = row_p['codigo']

        proj_sel_rotulo = st.selectbox("Selecione o Projeto para Gerenciar Metas", list(mapa_proj_gestao.keys()))
        proj_sel = mapa_proj_gestao[proj_sel_rotulo]

        df_proc = get_processos(proj_sel)

        if not df_proc.empty:
            for idx, row in df_proc.iterrows():
                with st.expander(f"Meta: {row['nome_processo']} | Status Atual: {row['status']}"):
                    with st.form(f"form_update_{row['codigo']}"):
                        novo_status = st.selectbox(
                            "Novo Status da Meta",
                            ["Pendente", "Cumprida", "Cumprida em Atraso", "Não Cumprida"],
                            index=["Pendente", "Cumprida", "Cumprida em Atraso", "Não Cumprida"].index(
                                row['status'] if row['status'] in ["Pendente", "Cumprida", "Cumprida em Atraso",
                                                                   "Não Cumprida"] else "Pendente"
                            )
                        )
                        nova_just = st.text_area("Justificativa / Observações da Entrega", value=row.get('justificativa', ''))

                        b_salvar = st.form_submit_button("Atualizar Meta")
                        if b_salvar:
                            try:
                                supabase.table("processos").update({
                                    "status": novo_status,
                                    "justificativa": nova_just
                                }).eq("codigo", row['codigo']).execute()
                                st.success("Meta atualizada!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao atualizar: {e}")
        else:
            st.info("Nenhum processo cadastrado para este projeto.")

# -----------------------------------------------------------------------------
# 6. RELATÓRIO POR DEPARTAMENTO
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
            procs_p = df_proc[df_proc['codigo_projeto'] == proj['codigo']] if not df_proc.empty else pd.DataFrame()
            pct_concluido = 0
            if not procs_p.empty:
                cumpridas = procs_p[procs_p['status'].isin(['Cumprida', 'Cumprida em Atraso'])].shape[0]
                pct_concluido = int((cumpridas / procs_p.shape[0]) * 100)

            with st.expander(
                    f"📁 {proj['nome']} ({proj['codigo']}) — Progresso: {pct_concluido}% | Status: {proj.get('status_projeto', 'N/A')}"):
                st.progress(pct_concluido / 100)
                col1, col2, col3 = st.columns(3)
                col1.write(f"**Departamento:** {proj.get('departamento', 'N/A')}")
                col1.write(f"**Setor:** {proj.get('setor', 'N/A')}")
                col2.write(f"**Responsável:** {proj.get('responsavel', 'N/A')}")
                col2.write(f"**Data Início:** {proj.get('data_inicio', 'N/A')}")
                col3.write(f"**Fim Previsto:** {proj.get('data_fim_prevista', 'N/A')}")
                col3.write(f"**Doc. Demanda:** {proj.get('doc_demanda', 'N/A')}")

                st.markdown("#### ⚙️ Processos e Metas Associadas:")
                if not procs_p.empty:
                    # Removida a coluna 'ordem' da exibição se não existir ou se preferir omitir
                    cols_exibir = [c for c in
                                   ['codigo', 'nome_processo', 'data_inicial', 'data_final', 'status', 'justificativa']
                                   if c in procs_p.columns]
                    st.dataframe(procs_p[cols_exibir], use_container_width=True)
                else:
                    st.info("Nenhum processo associado a este projeto.")