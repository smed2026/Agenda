import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from supabase import create_client, Client

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA E ESTILIZAÇÃO VISUAL MODERNA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Sistema de Agenda Eletrônica",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Customizado para Design Premium
st.markdown("""
<style>
    .stApp {
        background-color: #f8f9fa;
    }
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 {
        color: white !important;
        margin: 0;
        font-weight: 700;
    }
    .main-header p {
        color: #e0e0e0;
        margin-top: 5px;
        margin-bottom: 0;
    }
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
    .event-card {
        background-color: white;
        border-left: 5px solid #2a5298;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
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
    st.error("Erro ao conectar ao Supabase. Verifique suas credenciais e URL.")
    st.stop()

# -----------------------------------------------------------------------------
# BARRA LATERAL - NAVEGAÇÃO
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/isometric-folders/100/calendar.png", width=70)
    st.title("Agenda Eletrônica")
    st.markdown("---")

    menu = st.radio(
        "Navegação do Sistema",
        [
            "📅 Calendário de Eventos",
            "🏢 Secretarias",
            "🏛️ Departamentos",
            "🏫 Escolas",
            "📝 Gestão de Eventos",
            "📊 Relatórios"
        ]
    )
    st.markdown("---")
    st.caption("Desenvolvido com Streamlit & Supabase")

st.markdown(f"""
<div class="main-header">
    <h1>{menu}</h1>
    <p>Painel de controle corporativo e gestão institucional</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 1. TELA: SECRETARIAS (CRUD)
# -----------------------------------------------------------------------------
if menu == "🏢 Secretarias":
    col1, col2 = st.columns([1, 1.5], gap="large")

    with col1:
        st.subheader("Cadastrar / Editar Secretaria")
        sec_resp = supabase.table("secretaria").select("*").execute()
        sec_df = pd.DataFrame(sec_resp.data) if sec_resp.data else pd.DataFrame(columns=["codigo", "nome"])

        opcao_sec = st.selectbox("Ação", ["Nova Secretaria"] + [f"{row['codigo']} - {row['nome']}" for _, row in sec_df.iterrows()])

        codigo_edit = None
        nome_default = ""

        if opcao_sec != "Nova Secretaria":
            codigo_edit = int(opcao_sec.split(" - ")[0])
            registro = sec_df[sec_df["codigo"] == codigo_edit].iloc[0]
            nome_default = registro["nome"]

        with st.form("form_secretaria", clear_on_submit=True):
            nome = st.text_input("Nome da Secretaria", value=nome_default)
            btn_salvar = st.form_submit_button("💾 Salvar Registro")

            if btn_salvar:
                if nome.strip():
                    if codigo_edit:
                        supabase.table("secretaria").update({"nome": nome}).eq("codigo", codigo_edit).execute()
                        st.success("Secretaria atualizada com sucesso!")
                    else:
                        supabase.table("secretaria").insert({"nome": nome}).execute()
                        st.success("Secretaria cadastrada com sucesso!")
                    st.rerun()
                else:
                    st.warning("O nome da secretaria é obrigatório.")

        if codigo_edit:
            if st.button("🗑️ Excluir Secretaria", type="primary"):
                supabase.table("secretaria").delete().eq("codigo", codigo_edit).execute()
                st.success("Registro excluído com sucesso!")
                st.rerun()

    with col2:
        st.subheader("Secretarias Cadastradas")
        if not sec_df.empty:
            st.dataframe(sec_df.rename(columns={"codigo": "Código", "nome": "Nome da Secretaria"}), use_container_width=True)
        else:
            st.info("Nenhuma secretaria cadastrada.")

# -----------------------------------------------------------------------------
# 2. TELA: DEPARTAMENTOS (CRUD)
# -----------------------------------------------------------------------------
elif menu == "🏛️ Departamentos":
    sec_resp = supabase.table("secretaria").select("*").execute()
    sec_list = sec_resp.data if sec_resp.data else []

    if not sec_list:
        st.warning("Cadastre ao menos uma Secretaria antes de adicionar Departamentos.")
    else:
        col1, col2 = st.columns([1, 1.5], gap="large")

        dep_resp = supabase.table("departamentos").select("*").execute()
        dep_df = pd.DataFrame(dep_resp.data) if dep_resp.data else pd.DataFrame(
            columns=["codigo", "codsecretaria", "departamento", "responsavel"])

        with col1:
            st.subheader("Cadastrar / Editar Departamento")
            opcao_dep = st.selectbox("Ação",
                                     ["Novo Departamento"] + [f"{row['codigo']} - {row['departamento']}" for _, row in dep_df.iterrows()])

            codigo_edit = None
            dep_default = ""
            resp_default = ""
            sec_idx = 0

            sec_dict = {f"{s['codigo']} - {s['nome']}": s['codigo'] for s in sec_list}
            sec_options = list(sec_dict.keys())

            if opcao_dep != "Novo Departamento":
                codigo_edit = int(opcao_dep.split(" - ")[0])
                registro = dep_df[dep_df["codigo"] == codigo_edit].iloc[0]
                dep_default = registro["departamento"]
                resp_default = registro["responsavel"]
                for idx, (k, v) in enumerate(sec_dict.items()):
                    if v == registro["codsecretaria"]:
                        sec_idx = idx

            with st.form("form_departamento"):
                sec_selecionada = st.selectbox("Secretaria Vinculada", sec_options, index=sec_idx)
                departamento = st.text_input("Nome do Departamento", value=dep_default)
                responsavel = st.text_input("Responsável", value=resp_default)

                btn_salvar = st.form_submit_button("💾 Salvar Registro")

                if btn_salvar:
                    if departamento.strip() and responsavel.strip():
                        payload = {
                            "codsecretaria": sec_dict[sec_selecionada],
                            "departamento": departamento,
                            "responsavel": responsavel
                        }
                        if codigo_edit:
                            supabase.table("departamentos").update(payload).eq("codigo", codigo_edit).execute()
                            st.success("Departamento atualizado!")
                        else:
                            supabase.table("departamentos").insert(payload).execute()
                            st.success("Departamento cadastrado!")
                        st.rerun()
                    else:
                        st.warning("Preencha todos os campos obrigatórios.")

            if codigo_edit:
                if st.button("🗑️ Excluir Departamento", type="primary"):
                    supabase.table("departamentos").delete().eq("codigo", codigo_edit).execute()
                    st.success("Departamento excluído!")
                    st.rerun()

        with col2:
            st.subheader("Departamentos Cadastrados")
            if not dep_df.empty:
                st.dataframe(
                    dep_df.rename(columns={
                        "codigo": "Código",
                        "codsecretaria": "Cód. Secretaria",
                        "departamento": "Departamento",
                        "responsavel": "Responsável"
                    }),
                    use_container_width=True
                )
            else:
                st.info("Nenhum departamento cadastrado.")

# -----------------------------------------------------------------------------
# 3. TELA: ESCOLAS (CRUD)
# -----------------------------------------------------------------------------
elif menu == "🏫 Escolas":
    col1, col2 = st.columns([1, 1.5], gap="large")

    esc_resp = supabase.table("escolas").select("*").execute()
    esc_df = pd.DataFrame(esc_resp.data) if esc_resp.data else pd.DataFrame(columns=["codigo", "escola", "diretora"])

    with col1:
        st.subheader("Cadastrar / Editar Escola")
        opcao_esc = st.selectbox("Ação", ["Nova Escola"] + [f"{row['codigo']} - {row['escola']}" for _, row in esc_df.iterrows()])

        codigo_edit = None
        escola_default = ""
        diretora_default = ""

        if opcao_esc != "Nova Escola":
            codigo_edit = int(opcao_esc.split(" - ")[0])
            registro = esc_df[esc_df["codigo"] == codigo_edit].iloc[0]
            escola_default = registro["escola"]
            diretora_default = registro["diretora"]

        with st.form("form_escola"):
            escola = st.text_input("Nome da Escola", value=escola_default)
            diretora = st.text_input("Diretora / Responsável", value=diretora_default)

            btn_salvar = st.form_submit_button("💾 Salvar Registro")

            if btn_salvar:
                if escola.strip() and diretora.strip():
                    payload = {"escola": escola, "diretora": diretora}
                    if codigo_edit:
                        supabase.table("escolas").update(payload).eq("codigo", codigo_edit).execute()
                        st.success("Escola atualizada!")
                    else:
                        supabase.table("escolas").insert(payload).execute()
                        st.success("Escola cadastrada!")
                    st.rerun()
                else:
                    st.warning("Preencha todos os campos.")

        if codigo_edit:
            if st.button("🗑️ Excluir Escola", type="primary"):
                supabase.table("escolas").delete().eq("codigo", codigo_edit).execute()
                st.success("Escola excluída!")
                st.rerun()

    with col2:
        st.subheader("Escolas Cadastradas")
        if not esc_df.empty:
            st.dataframe(
                esc_df.rename(columns={"codigo": "Código", "escola": "Escola", "diretora": "Diretora"}),
                use_container_width=True
            )
        else:
            st.info("Nenhuma escola cadastrada.")

# -----------------------------------------------------------------------------
# 4. TELA: GESTÃO DE EVENTOS
# -----------------------------------------------------------------------------
elif menu == "📝 Gestão de Eventos":
    tab1, tab2 = st.tabs(["📌 Cadastro e Edição", "🔗 Departamentos Envolvidos"])

    events_resp = supabase.table("eventos").select("*").execute()
    events_df = pd.DataFrame(events_resp.data) if events_resp.data else pd.DataFrame()

    with tab1:
        col1, col2 = st.columns([1.2, 1.8], gap="large")

        with col1:
            st.subheader("Dados do Evento")

            opcao_ev = st.selectbox("Ação", ["Novo Evento"] + (
                [f"{row['codigo']} - {row['evento']}" for _, row in events_df.iterrows()] if not events_df.empty else []))

            codigo_edit = None
            ev_nome, ev_local, ev_resp, ev_obs = "", "", "", ""
            ev_status = "aberto"
            ev_responsabilidade = "Secretaria"
            ev_data = date.today()
            ev_hora = time(9, 0)
            ev_escoladpto_val = ""

            if opcao_ev != "Novo Evento":
                codigo_edit = int(opcao_ev.split(" - ")[0])
                reg = events_df[events_df["codigo"] == codigo_edit].iloc[0]
                ev_nome = reg["evento"]
                ev_status = reg["status"]
                ev_responsabilidade = reg["responsabilidade"]
                ev_data = datetime.strptime(str(reg["dataevento"]), "%Y-%m-%d").date()
                ev_hora = datetime.strptime(str(reg["horaevento"]), "%H:%M:%S").time() if len(str(reg["horaevento"])) == 8 else time(9, 0)
                ev_local = reg["local"]
                ev_escoladpto_val = reg["escoladpto"]
                ev_resp = reg["responsavel"]
                ev_obs = reg["obs"]

            responsabilidade_sel = st.radio("Responsabilidade", ["Secretaria", "Escolas"],
                                            index=0 if ev_responsabilidade == "Secretaria" else 1, horizontal=True)

            opcoes_escoladpto = []
            if responsabilidade_sel == "Secretaria":
                dpto_data = supabase.table("departamentos").select("departamento").execute().data
                opcoes_escoladpto = [d["departamento"] for d in dpto_data] if dpto_data else []
            else:
                esc_data = supabase.table("escolas").select("escola").execute().data
                opcoes_escoladpto = [e["escola"] for e in esc_data] if esc_data else []

            idx_escoladpto = 0
            if ev_escoladpto_val in opcoes_escoladpto:
                idx_escoladpto = opcoes_escoladpto.index(ev_escoladpto_val)

            with st.form("form_evento"):
                evento = st.text_input("Nome do Evento", value=ev_nome)
                status = st.selectbox("Status", ["aberto", "confirmado", "cancelado", "finalizado"],
                                      index=["aberto", "confirmado", "cancelado", "finalizado"].index(ev_status))

                escoladpto = st.selectbox(f"Origem / Seleção ({responsabilidade_sel})", opcoes_escoladpto,
                                          index=idx_escoladpto if opcoes_escoladpto else 0) if opcoes_escoladpto else st.text_input(
                    "Local/Origem", value=ev_escoladpto_val)

                c1, c2 = st.columns(2)
                dataevento = c1.date_input("Data do Evento", value=ev_data)
                horaevento = c2.time_input("Hora do Evento", value=ev_hora)

                local = st.text_input("Local do Evento", value=ev_local)
                responsavel = st.text_input("Responsável pelo Evento", value=ev_resp)
                obs = st.text_area("Observações", value=ev_obs)

                btn_salvar_ev = st.form_submit_button("💾 Salvar Evento")

                if btn_salvar_ev:
                    if evento.strip() and local.strip():
                        payload = {
                            "evento": evento,
                            "status": status,
                            "responsabilidade": responsabilidade_sel,
                            "dataevento": str(dataevento),
                            "horaevento": str(horaevento),
                            "local": local,
                            "escoladpto": escoladpto,
                            "responsavel": responsavel,
                            "obs": obs
                        }
                        if codigo_edit:
                            supabase.table("eventos").update(payload).eq("codigo", codigo_edit).execute()
                            st.success("Evento atualizado!")
                        else:
                            supabase.table("eventos").insert(payload).execute()
                            st.success("Evento criado com sucesso!")
                        st.rerun()
                    else:
                        st.warning("Preencha os campos obrigatórios (Evento, Local).")

            if codigo_edit:
                if st.button("🗑️️ Excluir Evento", type="primary"):
                    supabase.table("eventos").delete().eq("codigo", codigo_edit).execute()
                    st.success("Evento removido!")
                    st.rerun()

        with col2:
            st.subheader("Eventos Cadastrados")
            if not events_df.empty:
                st.dataframe(events_df, use_container_width=True)
            else:
                st.info("Nenhum evento registrado no sistema.")

    with tab2:
        st.subheader("Vincular Departamentos Envolvidos e Necessidades")
        if events_df.empty:
            st.info("Cadastre um evento primeiro para associar departamentos.")
        else:
            ev_dict = {f"{row['codigo']} - {row['evento']}": row['codigo'] for _, row in events_df.iterrows()}
            ev_sel = st.selectbox("Selecione o Evento", list(ev_dict.keys()))
            codevento_sel = ev_dict[ev_sel]

            dptos_db = supabase.table("departamentos").select("departamento").execute().data
            dptos_lista = [d["departamento"] for d in dptos_db] if dptos_db else []

            col_d1, col_d2 = st.columns([1, 1.5])

            with col_d1:
                with st.form("form_dpto_envolvido"):
                    dpto_env = st.selectbox("Departamento Envolvido", dptos_lista) if dptos_lista else st.text_input(
                        "Departamento Envolvido")
                    necessidade = st.text_area("Necessidade / Recursos Solicitados")
                    btn_add_dpto = st.form_submit_button("➕ Adicionar Envolvimento")

                    if btn_add_dpto:
                        if dpto_env:
                            supabase.table("dptoenvolvidos").insert({
                                "codevento": codevento_sel,
                                "departamento": dpto_env,
                                "necessidade": necessidade
                            }).execute()
                            st.success("Vinculado com sucesso!")
                            st.rerun()

            with col_d2:
                env_resp = supabase.table("dptoenvolvidos").select("*").eq("codevento", codevento_sel).execute()
                env_df = pd.DataFrame(env_resp.data) if env_resp.data else pd.DataFrame()

                if not env_df.empty:
                    st.dataframe(env_df[["codigo", "departamento", "necessidade"]], use_container_width=True)
                    del_id = st.selectbox("Remover Vínculo", env_df["codigo"].tolist())
                    if st.button("🗑️ Remover Envolvimento"):
                        supabase.table("dptoenvolvidos").delete().eq("codigo", del_id).execute()
                        st.success("Removido com sucesso!")
                        st.rerun()
                else:
                    st.info("Nenhum departamento vinculado a este evento.")

# -----------------------------------------------------------------------------
# 5. TELA: CALENDÁRIO VISUAL DOS EVENTOS (VISUALIZAÇÃO NATIVA MODERNA)
# -----------------------------------------------------------------------------
elif menu == "📅 Calendário de Eventos":
    events_resp = supabase.table("eventos").select("*").execute()
    events = events_resp.data if events_resp.data else []

    col_mes, col_ano = st.columns(2)
    hoje = date.today()

    meses_pt = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_sel = col_mes.selectbox("Mês", meses_pt, index=hoje.month - 1)
    ano_sel = col_ano.number_input("Ano", min_value=2020, max_value=2035, value=hoje.year)

    num_mes = meses_pt.index(mes_sel) + 1

    # Filtrar eventos do Mês/Ano selecionados
    eventos_filtrados = []
    for ev in events:
        try:
            dt_obj = datetime.strptime(str(ev["dataevento"]), "%Y-%m-%d")
            if dt_obj.month == num_mes and dt_obj.year == ano_sel:
                eventos_filtrados.append(ev)
        except Exception:
            pass

    st.markdown(f"### Eventos de **{mes_sel} de {ano_sel}** ({len(eventos_filtrados)} evento(s))")

    if eventos_filtrados:
        # Agrupar por data
        df_ev = pd.DataFrame(eventos_filtrados)
        df_ev = df_ev.sort_values(by="dataevento")

        status_colors = {
            "aberto": "🔵",
            "confirmado": "🟢",
            "cancelado": "🔴",
            "finalizado": "⚪"
        }

        for dt_group, group in df_ev.groupby("dataevento"):
            st.markdown(f"#### 📅 {datetime.strptime(str(dt_group), '%Y-%m-%d').strftime('%d/%m/%Y')}")
            for _, ev in group.iterrows():
                icone = status_colors.get(ev["status"], "🔵")
                with st.expander(f"{icone} **{ev['horaevento']}** — {ev['evento']} ({ev['local']})"):
                    c1, c2 = st.columns(2)
                    c1.write(f"**Status:** {ev['status'].capitalize()}")
                    c1.write(f"**Responsabilidade:** {ev['responsabilidade']}")
                    c1.write(f"**Origem/Dpto:** {ev['escoladpto']}")
                    c2.write(f"**Responsável:** {ev['responsavel']}")
                    c2.write(f"**Local:** {ev['local']}")
                    if ev['obs']:
                        st.caption(f"**Observações:** {ev['obs']}")
    else:
        st.info("Nenhum evento agendado para o mês selecionado.")

# -----------------------------------------------------------------------------
# 6. TELA: RELATÓRIO DE EVENTOS POR PERÍODO
# -----------------------------------------------------------------------------
elif menu == "📊 Relatórios":
    st.subheader("Gerar Relatório de Eventos por Período")

    col_r1, col_r2 = st.columns(2)
    dt_inicio = col_r1.date_input("Data Inicial", value=date.today().replace(day=1))
    dt_fim = col_r2.date_input("Data Final", value=date.today())

    if st.button("🔎 Filtrar Relatório"):
        rel_resp = supabase.table("eventos") \
            .select("evento, local, dataevento, horaevento, status, responsavel") \
            .gte("dataevento", str(dt_inicio)) \
            .lte("dataevento", str(dt_fim)) \
            .execute()

        if rel_resp.data:
            df_rel = pd.DataFrame(rel_resp.data)
            df_rel = df_rel.rename(columns={
                "evento": "Evento",
                "local": "Local",
                "dataevento": "Data",
                "horaevento": "Hora",
                "status": "Status",
                "responsavel": "Responsável"
            })

            st.success(f"Total de registros encontrados: {len(df_rel)}")
            st.dataframe(df_rel, use_container_width=True)

            csv = df_rel.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Relatório em CSV",
                data=csv,
                file_name=f"relatorio_eventos_{dt_inicio}_a_{dt_fim}.csv",
                mime="text/csv",
            )
        else:
            st.warning("Nenhum evento encontrado no período selecionado.")