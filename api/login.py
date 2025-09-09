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
            st.error(f"Erro na requisição: {error}")
            token = None

        return token, status_code

    def get_login(self):
        """
        Interface para realização do login na aplicação.
        """
        if 'token' in st.session_state and st.session_state.token is None:
            del st.session_state["token"]

        if "token" not in st.session_state:
            st.markdown("""
            <div style="text-align: center; padding: 40px 0;">
                <h1 style="color: #1f77b4; font-size: 3rem;
                    margin-bottom: 10px;">📚 UniPost</h1>
                <p style="font-size: 1.2rem; color: #666;
                    margin-bottom: 40px;">
                    Gerador Automático de Posts com IA
                </p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns([1, 2, 1])

            with col2:
                st.subheader("🔑 Login")

                with st.form("login_form", clear_on_submit=False):
                    username = st.text_input(
                        "👤 Usuário",
                        placeholder="Digite seu nome de usuário",
                        help="Entre com suas credenciais de acesso"
                    )
                    password = st.text_input(
                        ":unlock: Senha",
                        type="password",
                        placeholder="Digite sua senha",
                        help="Digite sua senha de acesso"
                    )

                    submit_button = st.form_submit_button(
                        "🚀 Entrar",
                        use_container_width=True,
                        type="primary"
                    )

                    if submit_button:
                        if not username or not password:
                            st.error("⚠️ Preencha todos os campos!")
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
                                    st.success(
                                        "✅ Login realizado com sucesso!")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error("❌ Usuário ou senha incorretos.")

                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("""
                <div style="text-align: center; margin-top: 30px;
                    color: #888;">
                    <h4>
                        🤖 Melhorado por IA • 🔐 Acesso Seguro<br>
                        Entre em contato com o administrador para obter acesso
                    </h4>
                </div>
                """, unsafe_allow_html=True)
        else:
            HomePage().main_menu()
