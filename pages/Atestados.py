import io
import time
import datetime
import pandas as pd
import streamlit as st
import plotly.express as px
from supabase import create_client, Client

# Configuração da página
st.set_page_config(page_title="Fichas Médicas", layout="wide")

# Estilização CSS para botões no tom azul pastel/ciano claro
st.markdown("""
    <style>
    div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
        background-color: #81D4FA !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: bold !important;
        transition: background-color 0.3s ease !important;
    }

    div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
        background-color: #4FC3F7 !important;
        color: #000000 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Inicialização do Supabase
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://seu-projeto.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "sua-chave-anon-key")


@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_supabase()

st.title("📋 Fichas Médicas")

# Menu Principal
aba1, aba2, aba3 = st.tabs(["📝 Cadastro & CRUD", "🔍 Pesquisa & Registros", "📊 Gráficos & Relatórios"])

# ==========================================
# ABA 1: CADASTRO E CRUD
# ==========================================
with aba1:
    st.header("Gestão de Documentos Digitalizados")

    modo = st.radio("Selecione a Ação:", ["Cadastrar Novo", "Editar / Excluir"], horizontal=True)

    if modo == "Cadastrar Novo":
        st.subheader("Novo Cadastro")
        with st.form("form_cadastro", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                codigo = st.text_input("Código do Documento")
                escola = st.text_input("Escola")
                secretario = st.text_input("Secretário(a)")
                data_reg = st.date_input("Data do Registro", datetime.date.today())

            with col2:
                nome_doc = st.text_input("Nome do Documento")
                nome_func = st.text_input("Nome do Funcionário")
                tipo_afast = st.selectbox("Tipo de Afastamento", ["Licença Médica", "Maternidade", "Prêmio", "Particular", "Outro"])

            with col3:
                data_inicio = st.date_input("Início do Afastamento", datetime.date.today())
                data_fim = st.date_input("Fim do Afastamento", datetime.date.today())
                obs = st.text_area("Observações")

            arquivo = st.file_uploader("Upload / Digitalização da Imagem ou PDF", type=["png", "jpg", "jpeg", "pdf"])

            btn_salvar = st.form_submit_button("Salvar Documento")

            if btn_salvar:
                if not codigo or not escola or not nome_func:
                    st.error("Por favor, preencha os campos obrigatórios (Código, Escola, Funcionário).")
                else:
                    imagem_url = None
                    if arquivo is not None:
                        try:
                            file_path = f"docs/{datetime.datetime.now().timestamp()}_{arquivo.name}"
                            res = supabase.storage.from_("documentos-bucket").upload(
                                file_path,
                                arquivo.getvalue(),
                                file_options={"content-type": arquivo.type}
                            )
                            imagem_url = supabase.storage.from_("documentos-bucket").get_public_url(file_path)
                        except Exception as e:
                            st.error(f"Erro ao realizar upload do arquivo: {e}")

                    dados = {
                        "codigo": codigo,
                        "escola": escola,
                        "secretario": secretario,
                        "data_registro": str(data_reg),
                        "imagem_url": imagem_url,
                        "nome_doc": nome_doc,
                        "nome_funcionario": nome_func,
                        "data_inicio_afastamento": str(data_inicio),
                        "data_fim_afastamento": str(data_fim),
                        "tipo_afastamento": tipo_afast,
                        "obs": obs
                    }
                    try:
                        supabase.table("documentos").insert(dados).execute()
                        st.success("Documento e ficha cadastrados com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao salvar registro no banco de dados: {e}")

    elif modo == "Editar / Excluir":
        st.subheader("Editar ou Excluir Registro")
        try:
            res = supabase.table("documentos").select("*").execute()
            df = pd.DataFrame(res.data)
        except Exception as e:
            df = pd.DataFrame()
            st.error(f"Erro ao buscar dados: {e}")

        if not df.empty:
            id_selecionado = st.selectbox(
                "Selecione o Registro (ID - Funcionário - Documento):",
                options=df["id"],
                format_func=lambda
                    x: f"ID: {x} | {df[df['id'] == x]['nome_funcionario'].values[0]} - {df[df['id'] == x]['nome_doc'].values[0]}"
            )

            registro = df[df["id"] == id_selecionado].iloc[0]

            with st.form("form_edicao"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    e_codigo = st.text_input("Código", value=str(registro["codigo"] or ""))
                    e_escola = st.text_input("Escola", value=str(registro["escola"] or ""))
                    e_secretario = st.text_input("Secretário(a)", value=str(registro["secretario"] or ""))

                with col2:
                    e_nome_doc = st.text_input("Nome Doc", value=str(registro["nome_doc"] or ""))
                    e_nome_func = st.text_input("Funcionário", value=str(registro["nome_funcionario"] or ""))

                    opcoes_tipo = ["Licença Médica", "Maternidade", "Prêmio", "Particular", "Outro"]
                    idx_tipo = opcoes_tipo.index(registro["tipo_afastamento"]) if registro["tipo_afastamento"] in opcoes_tipo else 0
                    e_tipo_afast = st.selectbox("Tipo Afastamento", opcoes_tipo, index=idx_tipo)

                with col3:
                    e_obs = st.text_area("Obs", value=str(registro["obs"] or ""))

                if registro["imagem_url"]:
                    st.markdown(f"[📎 Visualizar Imagem/Documento Atual]({registro['imagem_url']})")

                c_salvar, c_excluir = st.columns(2)
                btn_atualizar = c_salvar.form_submit_button("Atualizar Registro")
                btn_excluir = c_excluir.form_submit_button("🗑️ Excluir Registro")

                if btn_atualizar:
                    dados_update = {
                        "codigo": e_codigo,
                        "escola": e_escola,
                        "secretario": e_secretario,
                        "nome_doc": e_nome_doc,
                        "nome_funcionario": e_nome_func,
                        "tipo_afastamento": e_tipo_afast,
                        "obs": e_obs
                    }
                    supabase.table("documentos").update(dados_update).eq("id", id_selecionado).execute()
                    st.success("Registro atualizado com sucesso!")
                    time.sleep(1)
                    st.rerun()

                if btn_excluir:
                    supabase.table("documentos").delete().eq("id", id_selecionado).execute()
                    st.warning("Registro excluído com sucesso!")
                    time.sleep(1)
                    st.rerun()
        else:
            st.info("Nenhum registro disponível para edição.")

# ==========================================
# ABA 2: PESQUISA E FILTROS
# ==========================================
with aba2:
    st.header("Consulta de Fichas e Documentos")

    try:
        res = supabase.table("documentos").select("*").execute()
        df_busca = pd.DataFrame(res.data)
    except Exception as e:
        df_busca = pd.DataFrame()
        st.error(f"Erro ao carregar dados para busca: {e}")

    if not df_busca.empty:
        col_f1, col_f2 = st.columns(2)

        escolas = ["Todas"] + list(df_busca["escola"].dropna().unique())
        escola_filtro = col_f1.selectbox("Filtrar por Escola:", escolas)

        func_filtro = col_f2.text_input("Filtrar por Nome do Funcionário:")

        df_filtrado = df_busca.copy()
        if escola_filtro != "Todas":
            df_filtrado = df_filtrado[df_filtrado["escola"] == escola_filtro]
        if func_filtro:
            df_filtrado = df_filtrado[df_filtrado["nome_funcionario"].str.contains(func_filtro, case=False, na=False)]

        st.subheader(f"Resultados Encontrados ({len(df_filtrado)})")

        for _, row in df_filtrado.iterrows():
            with st.expander(f"📌 Código: {row['codigo']} | Funcionário: {row['nome_funcionario']} ({row['escola']})"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Documento:** {row['nome_doc']}")
                    st.write(f"**Secretário(a):** {row['secretario']}")
                    st.write(f"**Data do Registro:** {row['data_registro']}")
                    st.write(f"**Tipo Afastamento:** {row['tipo_afastamento']}")
                    st.write(f"**Período:** {row['data_inicio_afastamento']} até {row['data_fim_afastamento']}")
                    st.write(f"**Observação:** {row['obs']}")
                with c2:
                    if row['imagem_url']:
                        if str(row['imagem_url']).lower().endswith(('png', 'jpg', 'jpeg')):
                            st.image(row['imagem_url'], caption="Anexo Digitalizado", width=320)
                        else:
                            st.markdown(f"🔗 [Abrir Documento / PDF Anexo]({row['imagem_url']})")
                    else:
                        st.info("Sem documento anexo.")
    else:
        st.info("Nenhum registro encontrado no sistema.")

# ==========================================
# ABA 3: GRÁFICOS E RELATÓRIOS
# ==========================================
with aba3:
    st.header("Painel Analítico de Atestados e Afastamentos")

    try:
        res = supabase.table("documentos").select("*").execute()
        df_graficos = pd.DataFrame(res.data)
    except Exception as e:
        df_graficos = pd.DataFrame()
        st.error(f"Erro ao carregar gráficos: {e}")

    if not df_graficos.empty:
        g1, g2 = st.columns(2)

        with g1:
            st.subheader("Afastamentos por Escola")
            df_escola_counts = df_graficos['escola'].value_counts().reset_index()
            df_escola_counts.columns = ['escola', 'count']

            fig_escola = px.bar(
                df_escola_counts,
                x='escola',
                y='count',
                labels={'escola': 'Escola', 'count': 'Quantidade'},
                color_discrete_sequence=['#81D4FA']
            )
            st.plotly_chart(fig_escola, use_container_width=True)

        with g2:
            st.subheader("Distribuição por Tipo de Afastamento")
            fig_tipo = px.pie(
                df_graficos,
                names='tipo_afastamento',
                hole=0.4,
                color_discrete_sequence=['#81D4FA', '#4FC3F7', '#29B6F6', '#0288D1', '#0277BD']
            )
            st.plotly_chart(fig_tipo, use_container_width=True)

        st.subheader("Top Funcionários com Mais Registros/Atestados")
        df_func_counts = df_graficos['nome_funcionario'].value_counts().head(10).reset_index()
        df_func_counts.columns = ['nome_funcionario', 'count']

        fig_func = px.bar(
            df_func_counts,
            x='nome_funcionario',
            y='count',
            labels={'nome_funcionario': 'Funcionário', 'count': 'Total de Documentos'},
            color_discrete_sequence=['#4FC3F7']
        )
        st.plotly_chart(fig_func, use_container_width=True)
    else:
        st.info("Cadastre dados no sistema para visualizar os gráficos e métricas.")