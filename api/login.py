from home.main import HomePage
from api.token import Token
from dictionary.vars import TOKEN_URL
import requests
import streamlit as st


class Login:
    """
    Classe responsável pelo login do usuário na aplicação.
    """

    def login(self, username, password):
        """
        Faz a obtenção do token de acesso a API.

        Parameters
        ----------
        username : str
            O nome do usuário.
        password : str
            A senha do usuário.

        Returns
        -------
        token : str
            O token para acesso.
        status_code : int
            O código retornado pela requisição.
        """
        token = ""
        status_code = 0

        try:
            response = requests.post(
                TOKEN_URL,
                data={
                    "username": username,
                    "password": password
                }
            )
            status_code = response.status_code
            if status_code == 200:
                token = response.json().get("access")
            else:
                token = response.status_code
        except Exception as error:
            st.toast(f"Erro na requisição: {error}", icon="❌")
            token = None

        return token, status_code

    def get_login(self):
        """
        Interface para realização do login na aplicação.
        """
        if 'token' in st.session_state and st.session_state.token is None:
            del st.session_state["token"]

        if "token" not in st.session_state:
            # Cabeçalho principal simplificado
            st.markdown("""
            <div style="text-align: center; padding: 2rem 0;">
                <h1 style="
                    color: #1f77b4;
                    font-size: 3rem;
                    margin-bottom: 0.5rem;
                    font-weight: 700;
                ">
                    🤖 UniPost
                </h1>
                <p style="
                    color: #666;
                    font-size: 1.1rem;
                    margin-bottom: 2rem;
                    font-weight: 300;
                ">
                    Gerador Inteligente de Posts com IA
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Layout de login centralizado
            _, col2, _ = st.columns([1, 2, 1])

            with col2:
                # Container de login limpo
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, \
#764ba2 100%);
                    padding: 2rem;
                    border-radius: 12px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    margin: 1rem 0;
                ">
                    <h3 style="
                        color: white;
                        text-align: center;
                        margin-bottom: 1.5rem;
                        font-weight: 500;
                    ">
                        🔑 Acesso Seguro
                    </h3>
                </div>
                """, unsafe_allow_html=True)

                # Formulário de login simplificado
                with st.form("login_form", clear_on_submit=False):

                    username = st.text_input(
                        "👤 Usuário",
                        placeholder="Digite seu nome de usuário",
                        help="Entre com suas credenciais de acesso"
                    )
                    password = st.text_input(
                        "🔒 Senha",
                        type="password",
                        placeholder="Digite sua senha",
                        help="Digite sua senha de acesso"
                    )

                    _, col_center, _ = st.columns([1, 1, 1])
                    with col_center:
                        submit_button = st.form_submit_button(
                            "🚀 Entrar",
                            use_container_width=True,
                            type="primary"
                        )

                    if submit_button:
                        if not username or not password:
                            st.toast("Preencha todos os campos!", icon="⚠️")
                        else:
                            with st.spinner("Verificando credenciais..."):
                                token, status_code = self.login(
                                    username, password)

                                if token and status_code == 200:
                                    st.session_state.token = token
                                    st.session_state.is_logged_in = True
                                    st.session_state.user_name = username
                                    st.session_state.user_permissions = (
                                        Token().get_user_permissions(
                                            token=token
                                        )
                                    )
                                    st.toast(
                                        "Login realizado com sucesso!",
                                        icon="✅"
                                    )
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.toast("Credenciais inválidas", icon="❌")

                # Rodapé simplificado
                st.markdown("""
                <div style="
                    text-align: center;
                    margin-top: 2rem;
                    padding: 1rem;
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    border-left: 4px solid #667eea;
                ">
                    <p style="
                        margin: 0;
                        color: #666;
                        font-size: 0.9rem;
                    ">
                        🤖 <strong>Melhorado por IA</strong> • 🔐 \
<strong>Acesso Seguro</strong><br>
                        <small>Entre em contato com o administrador \
para obter acesso</small>
                    </p>
                </div>
                """, unsafe_allow_html=True)
        else:
            HomePage().main_menu()
