import streamlit as st
import hashlib
from supabase import create_client, Client

# Configuração da página inicial (deve ser a primeira chamada Streamlit)
st.set_page_config(
    page_title="Portal de Acesso — Sistema Integrado",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização do Supabase (utilizando os secrets ou chaves diretas)
SUPABASE_URL = "https://sldhiftwxqynjcnpaysl.supabase.co"
SUPABASE_KEY = "sb_publishable_m9NM4QJ433cSXQLvM-4PRw_NMEKEorT"

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_supabase()


# Função para hash de senha simples (caso armazene criptografado, ajuste conforme necessário)
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


# Inicialização de variáveis de sessão
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "usuario_cpf" not in st.session_state:
    st.session_state["usuario_cpf"] = ""
if "usuario_nome" not in st.session_state:
    st.session_state["usuario_nome"] = ""
if "permissoes" not in st.session_state:
    st.session_state["permissoes"] = {}

# =============================================================================
# CONTROLE DE VISIBILIDADE DO MENU LATERAL
# =============================================================================
if not st.session_state["autenticado"]:
    # Oculta completamente o menu de navegação lateral se não estiver logado
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {
                display: none !important;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 style='text-align: center;'>🔐 Acesso Restrito ao Sistema</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Por favor, informe suas credenciais para continuar.</p>", unsafe_allow_html=True)

    col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
    with col_l2:
        with st.form("form_login"):
            input_cpf = st.text_input("CPF do Usuário (Apenas números ou formatado)")
            input_senha = st.text_input("Senha", type="password")
            btn_entrar = st.form_submit_button("Entrar no Sistema", use_container_width=True)

            if btn_entrar:
                if not input_cpf or not input_senha:
                    st.warning("Preencha todos os campos de login.")
                else:
                    try:
                        # Consulta na tabela de usuários
                        res_user = supabase.table("usuarios").select("*").eq("cpf", input_cpf.strip()).execute()

                        if res_user.data and len(res_user.data) > 0:
                            user_data = res_user.data[0]
                            senha_cadastrada = user_data["senha"]

                            # Validação da senha (suporta texto puro ou hash, ajuste se necessário)
                            if input_senha == senha_cadastrada or hash_senha(input_senha) == senha_cadastrada:
                                st.session_state["autenticado"] = True
                                st.session_state["usuario_cpf"] = user_data["cpf"]
                                st.session_state["usuario_nome"] = user_data["nome"]

                                # Carrega as permissões do usuário para as telas
                                res_perm = supabase.table("permissoes").select("*").eq("cpf", user_data["cpf"]).execute()
                                perms = {}
                                if res_perm.data:
                                    for p in res_perm.data:
                                        perms[p["tela"]] = {
                                            "acessar": p["acessar"],
                                            "inserir": p["inserir"],
                                            "alterar": p["alterar"],
                                            "deletar": p["deletar"]
                                        }
                                st.session_state["permissoes"] = perms

                                st.success(f"Bem-vindo(a), {user_data['nome']}!")
                                st.rerun()
                            else:
                                st.error("❌ Login inválido: Senha incorreta.")
                        else:
                            st.error("❌ Login inválido: CPF não encontrado.")
                    except Exception as e:
                        st.error(f"Erro ao conectar com o banco de dados: {e}")

else:
    # =============================================================================
    # TELA PRINCIPAL (APÓS LOGIN BEM-SUCEDIDO)
    # =============================================================================
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/user-menu-male.png", width=60)
        st.write(f"**Usuário:** {st.session_state['usuario_nome']}")
        st.markdown("---")

        # Menu lateral visível apenas após autenticação
        modulos_disponiveis = ["🏠 Início / Dashboard"]

        permissoes_usuario = st.session_state["permissoes"]

        # Verifica permissão de acesso para cada script anexado
        if permissoes_usuario.get("Atestados.py", {}).get("acessar", True):
            modulos_disponiveis.append("📋 Fichas Médicas (Atestados)")
        if permissoes_usuario.get("Calendario.py", {}).get("acessar", True):
            modulos_disponiveis.append("📅 Agenda Eletrônica")
        if permissoes_usuario.get("Projetos.py", {}).get("acessar", True):
            modulos_disponiveis.append("📊 Gestão de Projetos")

        escolha_modulo = st.sidebar.radio("Navegação Principal", modulos_disponiveis)

        st.markdown("---")
        if st.sidebar.button("🚪 Sair / Encerrar Sessão", use_container_width=True):
            st.session_state["autenticado"] = False
            st.session_state["usuario_cpf"] = ""
            st.session_state["usuario_nome"] = ""
            st.session_state["permissoes"] = {}
            st.rerun()

    # Roteamento dos scripts anexados com base na escolha do menu
    if escolha_modulo == "🏠 Início / Dashboard":
        st.title("🌟 Painel Central do Sistema")
        st.write(
            f"Olá, **{st.session_state['usuario_nome']}**. Utilize o menu lateral esquerdo para navegar entre os módulos liberados para o seu perfil.")
        st.info("O acesso aos scripts anexados é validado dinamicamente conforme as permissões cadastradas no banco de dados.")

    elif escolha_modulo == "📋 Fichas Médicas (Atestados)":
        # Importa e executa o script Atestados.py anexado
        try:
            import Atestados
        except Exception as e:
            st.error(f"Erro ao carregar o módulo de Atestados: {e}")

    elif escolha_modulo == "📅 Agenda Eletrônica":
        # Importa e executa o script Calendario.py anexado
        try:
            import Calendario
        except Exception as e:
            st.error(f"Erro ao carregar o módulo de Calendário: {e}")

    elif escolha_modulo == "📊 Gestão de Projetos":
        # Importa e executa o script Projetos.py anexado
        try:
            import Projetos
        except Exception as e:
            st.error(f"Erro ao carregar o módulo de Projetos: {e}")