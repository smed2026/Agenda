import base64
import os
import re
import time
import streamlit as st
from supabase import Client, create_client

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="I Fórum Intersetorial - Inscrições",
    page_icon="📝",
    layout="centered",
)


# --- ESTILIZAGEM CSS PARA FIXAR E ENQUADRAR O FORMULÁRIO DENTRO DA IMAGEM ---
def aplicar_estilo_formulario_enquadrado(caminho_imagem: str = "background.jpg"):
    imagem_encontrada = None
    possiveis_nomes = [
        caminho_imagem,
        "background.jpg.jpeg",
        "background.jpeg",
        "Sem título-1.jpg.jpg",
        "Sem título-1.jpg",
    ]

    for nome in possiveis_nomes:
        if os.path.exists(nome):
            imagem_encontrada = nome
            break

    encoded_string = ""
    if imagem_encontrada:
        with open(imagem_encontrada, "rb") as file:
            encoded_string = base64.b64encode(file.read()).decode()

    bg_css = (
        f'background-image: url("data:image/jpeg;base64,{encoded_string}");'
        if encoded_string
        else ""
    )

    css = f"""
    <style>
    /* Bloqueio de rolagem horizontal */
    html, body, [data-testid="stAppViewContainer"] {{
        width: 100vw;
        height: 100vh;
        margin: 0;
        padding: 0;
        overflow-x: hidden !important;
    }}

    /* Imagem de Fundo totalmente visível e centralizada */
    [data-testid="stAppViewContainer"] {{
        {bg_css}
        background-size: contain !important;
        background-position: center top !important;
        background-repeat: no-repeat !important;
        background-color: #0d1b2a;
    }}

    [data-testid="stHeader"] {{
        background-color: transparent !important;
    }}

    /* Container Fixo e Enquadrado no Centro da Imagem */
    .main .block-container {{
        max-width: 460px !important;       /* Largura enxuta para comportar 2 colunas sem sair das bordas */
        width: 82% !important;              /* Margem ideal para artes laterais da imagem */
        margin-top: 105px !important;       /* Libera a arte/cabeçalho superior da imagem */
        margin-bottom: 20px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        background: rgba(255, 255, 255, 0.96) !important;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        padding: 1.4rem 1.2rem !important;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.9);
        box-sizing: border-box !important;
    }}

    /* Estilização de Entradas e Seletores */
    div[data-baseweb="input"], div[data-baseweb="select"], .stTextInput, .stSelectbox {{
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }}

    /* Destacar o foco no seletor para facilitar a navegação via setas e PgUp/PgDn */
    div[data-baseweb="select"]:focus-within {{
        border-color: #008882 !important;
        box-shadow: 0 0 0 2px rgba(0, 136, 130, 0.3) !important;
    }}

    /* Ajuste fino nos rótulos/labels para evitar quebra em 2 colunas */
    label {{
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        color: #0b2545 !important;
        margin-bottom: 2px !important;
    }}

    /* Espaçamento Vertical Compacto */
    [data-testid="stVerticalBlock"] {{
        gap: 0.5rem !important;
    }}

    /* Responsividade Móvel */
    @media (max-width: 768px) {{
        [data-testid="stAppViewContainer"] {{
            background-size: cover !important;
        }}

        .main .block-container {{
            width: 90% !important;
            max-width: 380px !important;
            margin-top: 85px !important;
            padding: 1.2rem 0.9rem !important;
        }}
    }}

    /* Títulos e Textos Centralizados */
    h1, h2, h3, h4 {{
        color: #0b2545 !important;
        font-weight: 700 !important;
        text-align: center;
        margin-bottom: 0.2rem !important;
    }}

    /* Estilização do Alerta de Sucesso Centralizado */
    .mensagem-sucesso-centro {{
        background-color: #def7ec;
        color: #03543f;
        border: 2px solid #0e9f6e;
        border-radius: 12px;
        padding: 20px 15px;
        text-align: center;
        font-size: 1.1rem;
        font-weight: 700;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(14, 159, 110, 0.2);
    }}

    /* Estilização e Centralização de Botões */
    div.stButton > button, div.stFormSubmitButton > button {{
        background-color: #008882 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
        padding: 8px 12px !important;
        width: 100% !important;
        margin-top: 6px !important;
        transition: all 0.3s ease !important;
    }}

    div.stButton > button:hover, div.stFormSubmitButton > button:hover {{
        background-color: #00605c !important;
        box-shadow: 0 4px 12px rgba(0, 136, 130, 0.4);
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


aplicar_estilo_formulario_enquadrado("background.jpg")

# --- CONEXÃO COM SUPABASE ---
SUPABASE_URL = "https://yqlgtpwlhptrmlltvrhi.supabase.co"
SUPABASE_KEY = "sb_publishable_S3zafv2jYpXKUiyhK6XSyQ_w_0qBuYd"


@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_supabase()

# --- GERENCIAMENTO DE ESTADOS DA APLICAÇÃO ---
if "etapa" not in st.session_state:
    st.session_state["etapa"] = (
        1  # 1: Identificação | 2: Dados Pessoais | 3: Tela de Sucesso Temporária
    )

estados_iniciais = {
    "cpf_input": "",
    "telefone_input": "",
    "email_input": "",
    "nome_input": "",
    "cargo_input": "",
    "msg_erro": "",
}

for chave, valor in estados_iniciais.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor


def resetar_formulario():
    """Limpa todos os dados para permitir um novo cadastro do zero."""
    st.session_state["cpf_input"] = ""
    st.session_state["telefone_input"] = ""
    st.session_state["email_input"] = ""
    st.session_state["nome_input"] = ""
    st.session_state["cargo_input"] = ""
    st.session_state["msg_erro"] = ""
    st.session_state["etapa"] = 1


# --- MENSAGENS E ALERTAS VISUAIS ---
def exibir_alerta(mensagem: str, tipo: str):
    if not mensagem:
        return
    if tipo == "erro":
        cor_bg, cor_texto, cor_borda, icone = "#fde8e8", "#9b1c1c", "#f05252", "❌"
    elif tipo == "sucesso":
        cor_bg, cor_texto, cor_borda, icone = "#def7ec", "#03543f", "#0e9f6e", "✅"
    else:
        return

    html_alerta = f"""
    <div style="
        background-color: {cor_bg};
        color: {cor_texto};
        border-left: 4px solid {cor_borda};
        padding: 6px 10px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        margin-top: 4px;
        margin-bottom: 6px;">
        {icone} {mensagem}
    </div>
    """
    st.markdown(html_alerta, unsafe_allow_html=True)


# --- VALIDAÇÕES E FORMATAÇÕES ---
def validar_algoritmo_cpf(cpf_string: str) -> bool:
    cpf = re.sub(r"\D", "", cpf_string)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    digito_1 = 0 if resto == 10 else resto
    if digito_1 != int(cpf[9]):
        return False
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    digito_2 = 0 if resto == 10 else resto
    return digito_2 == int(cpf[10])


def formatar_cpf(texto: str) -> str:
    numeros = re.sub(r"\D", "", texto)[:11]
    if len(numeros) <= 3:
        return numeros
    if len(numeros) <= 6:
        return f"{numeros[:3]}.{numeros[3:]}"
    if len(numeros) <= 9:
        return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:]}"
    return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:11]}"


def formatar_telefone(texto: str) -> str:
    numeros = re.sub(r"\D", "", texto)[:11]
    if len(numeros) == 0:
        return ""
    tel = f"({numeros[:2]}"
    if len(numeros) > 2:
        if len(numeros) <= 10:
            tel += f") {numeros[2:6]}"
            if len(numeros) > 6:
                tel += f"-{numeros[6:10]}"
        else:
            tel += f") {numeros[2:7]}"
            if len(numeros) > 7:
                tel += f"-{numeros[7:11]}"
    return tel


def obter_grupos():
    """Busca a lista de grupos cadastrados no banco em ORDEM ALFABÉTICA (A-Z)."""
    try:
        res = (
            supabase.table("grupos")
            .select("nome, qtdvagas, qtdvagasusadas")
            .order("nome", desc=False)  # Ordenação direto na consulta SQL
            .execute()
        )
        return res.data
    except Exception as e:
        st.error(f"Erro ao carregar 'grupos': {e}")
        return []


# ==============================================================================
# TELA 1: IDENTIFICAÇÃO
# ==============================================================================
if st.session_state["etapa"] == 1:
    st.title("📝 Inscrição")
    st.caption("Passo 1 de 2: Identificação")

    with st.form("form_tela_1", clear_on_submit=False):
        cpf_digitado = st.text_input(
            "Digite seu CPF (Pressione Enter):",
            value=st.session_state["cpf_input"],
            placeholder="000.000.000-00",
            max_chars=14,
        )

        cpf_formatado = formatar_cpf(cpf_digitado)
        st.session_state["cpf_input"] = cpf_formatado

        if st.session_state["msg_erro"]:
            exibir_alerta(st.session_state["msg_erro"], "erro")

        # Botão Centralizado
        col_esq, col_btn, col_dir = st.columns([0.15, 0.7, 0.15])
        with col_btn:
            btn_avancar = st.form_submit_button(
                "Avançar para Dados Pessoais ➡️", use_container_width=True
            )

    if btn_avancar:
        numeros_cpf = re.sub(r"\D", "", cpf_formatado)

        if len(numeros_cpf) < 11:
            st.session_state["msg_erro"] = (
                "Por favor, preencha os 11 dígitos do CPF."
            )
            st.rerun()
        elif not validar_algoritmo_cpf(numeros_cpf):
            st.session_state["msg_erro"] = (
                "CPF inválido! Verifique os dígitos digitados."
            )
            st.rerun()
        else:
            try:
                res = (
                    supabase.table("inscritos")
                    .select("id")
                    .eq("cpf", cpf_formatado)
                    .execute()
                )
                if len(res.data) > 0:
                    st.session_state["msg_erro"] = (
                        "Este CPF já possui uma inscrição cadastrada!"
                    )
                    st.rerun()
                else:
                    st.session_state["msg_erro"] = ""
                    st.session_state["etapa"] = 2  # Avança para a Tela 2
                    st.rerun()
            except Exception as e:
                st.session_state["msg_erro"] = (
                    f"Erro de conexão ao verificar CPF: {e}"
                )
                st.rerun()


# ==============================================================================
# TELA 2: DADOS PESSOAIS (GRUPOS EM ORDEM ALFABÉTICA)
# ==============================================================================
elif st.session_state["etapa"] == 2:
    st.title("📋 Dados Pessoais")
    # CPF Confirmado e o Número em Negrito
    st.markdown(f"**CPF Confirmado: {st.session_state['cpf_input']}**")

    grupos_dados = obter_grupos()

    # Extrai e assegura a ordenação alfabética (A-Z)
    if grupos_dados:
        lista_nomes_grupos = [g["nome"] for g in grupos_dados]
        lista_nomes_grupos.sort()  # Ordenação alfabética secundária
    else:
        lista_nomes_grupos = []

    with st.form("form_tela_2", clear_on_submit=False):
        # 1. NOME COMPLETO
        nome_input = st.text_input(
            "Nome Completo:",
            value=st.session_state["nome_input"],
            placeholder="Digite seu nome completo",
        )

        # 2. TELEFONE E E-MAIL NA MESMA LINHA
        col_tel, col_email = st.columns(2)
        with col_tel:
            tel_input = st.text_input(
                "Telefone (DDD + Número):",
                value=st.session_state["telefone_input"],
                placeholder="(00) 00000-0000",
            )
        with col_email:
            email_input = st.text_input(
                "E-mail:",
                value=st.session_state["email_input"],
                placeholder="nome@dominio.com",
            )

        # 3. GRUPO E CARGO NA MESMA LINHA
        col_grupo, col_cargo = st.columns(2)
        with col_grupo:
            # Lista em ordem alfabética com navegação via teclado
            grupo_selecionado = st.selectbox(
                "Grupo ao qual pertence:",
                options=lista_nomes_grupos
                if lista_nomes_grupos
                else ["Nenhum grupo disponível"],
                help="Os grupos estão em ordem alfabética. Use as setas do teclado, PgUp ou PgDn para navegar.",
            )
        with col_cargo:
            cargo_input = st.text_input(
                "Cargo:",
                value=st.session_state["cargo_input"],
                placeholder="Ex: Coordenador",
            )

        if st.session_state["msg_erro"]:
            exibir_alerta(st.session_state["msg_erro"], "erro")

        # 4. BOTÃO CONFIRMAR INSCRIÇÃO CENTRALIZADO
        col_e, col_centro, col_d = st.columns([0.1, 0.8, 0.1])
        with col_centro:
            btn_confirmar = st.form_submit_button(
                "Confirmar Inscrição ✔️", use_container_width=True
            )

    if btn_confirmar:
        tel_formatado = formatar_telefone(tel_input)
        st.session_state["telefone_input"] = tel_formatado
        st.session_state["email_input"] = email_input.strip()
        st.session_state["nome_input"] = nome_input
        st.session_state["cargo_input"] = cargo_input

        numeros_tel = re.sub(r"\D", "", tel_formatado)
        padrao_email = r"^[\w\.-]+@[\w\.-]+\.\w+$"

        if len(numeros_tel) < 10:
            st.session_state["msg_erro"] = (
                "Insira um telefone válido com DDD (mínimo 10 dígitos)."
            )
            st.rerun()
        elif not re.match(padrao_email, st.session_state["email_input"]):
            st.session_state["msg_erro"] = "Insira um endereço de e-mail válido."
            st.rerun()
        elif not st.session_state["nome_input"]:
            st.session_state["msg_erro"] = "Preencha seu Nome Completo."
            st.rerun()
        elif not st.session_state["cargo_input"]:
            st.session_state["msg_erro"] = "Preencha seu Cargo."
            st.rerun()
        elif grupo_selecionado == "Nenhum grupo disponível":
            st.session_state["msg_erro"] = "Selecione um grupo válido."
            st.rerun()
        else:
            info_grupo = next(
                (g for g in grupos_dados if g["nome"] == grupo_selecionado),
                None,
            )

            if (
                    info_grupo
                    and info_grupo["qtdvagasusadas"] >= info_grupo["qtdvagas"]
            ):
                st.session_state["msg_erro"] = (
                    "As vagas para este grupo estão esgotadas."
                )
                st.rerun()
            else:
                try:
                    res_rpc = supabase.rpc(
                        "processar_inscricao",
                        {
                            "p_cpf": st.session_state["cpf_input"],
                            "p_nome": st.session_state["nome_input"],
                            "p_email": st.session_state["email_input"],
                            "p_telefone": st.session_state["telefone_input"],
                            "p_grupo_nome": grupo_selecionado,
                            "p_cargo": st.session_state["cargo_input"],
                        },
                    ).execute()

                    resultado = res_rpc.data

                    if resultado == "SEM_VAGAS":
                        st.session_state["msg_erro"] = (
                            "As vagas para este grupo estão esgotadas."
                        )
                        st.rerun()
                    elif resultado == "SUCESSO":
                        st.session_state["etapa"] = 3
                        st.rerun()

                except Exception as e:
                    st.session_state["msg_erro"] = (
                        f"Erro ao salvar no banco: {e}"
                    )
                    st.rerun()


# ==============================================================================
# TELA 3: MENSAGEM DE SUCESSO NO CENTRO (3 SEGUNDOS DEPOIS RESET AUTO)
# ==============================================================================
elif st.session_state["etapa"] == 3:
    st.markdown(
        """
        <div class="mensagem-sucesso-centro">
            🎉 INSCRIÇÃO REALIZADA COM SUCESSO!
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption("Redirecionando para um novo cadastro...")

    # Aguarda 5 segundos exibindo a mensagem centralizada
    time.sleep(8)

    # Limpa todos os campos e volta para a Tela 1
    resetar_formulario()
    st.rerun()