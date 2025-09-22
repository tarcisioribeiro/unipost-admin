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
            # Cabeçalho principal
            st.title("🤖 UniPost")
            st.subheader("Gerador de Posts com IA")
            st.divider()

            # Layout de login centralizado
            _, col2, _ = st.columns([1, 2, 1])

            with col2:
                # Container de login
                st.header("🔑 Acesso Seguro")

                # Formulário de login simplificado
                with st.form("login_form", clear_on_submit=False):

                    username = st.text_input(
                        "👤 Usuário",
                        placeholder="Digite seu usuário",
                        help="Nome de usuário"
                    )
                    password = st.text_input(
                        "🔒 Senha",
                        type="password",
                        placeholder="Digite sua senha",
                        help="Senha de acesso"
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

                # Rodapé
                st.info("""
                🤖 **Melhorado por IA** • 🔐 **Acesso Seguro**

                Contate o administrador para acesso
                """)
        else:
            HomePage().main_menu()
