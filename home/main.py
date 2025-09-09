from api.token import Token
from texts.main import Texts
from dashboard.main import Dashboard
from dictionary.vars import HELP_MENU
from time import sleep
import streamlit as st


class HomePage:
    """
    Classe que representa a página inicial da aplicação.
    """

    @st.dialog("❓ Manual de Uso - UniPost")
    def show_help_dialog(self):
        """
        Exibe o dialog de ajuda com manual de uso das funcionalidades.
        """
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h3 style="color: #1f77b4;">📚 Como usar o UniPost</h3>
            <p style="color: #666;">
                Selecione uma funcionalidade para ver as instruções detalhadas
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Selectbox com as opções de ajuda
        selected_help = st.selectbox(
            "Escolha uma funcionalidade:",
            options=list(HELP_MENU.keys()),
            index=0,
            key="help_selectbox"
        )
        
        # Exibir conteúdo da ajuda selecionada
        if selected_help:
            st.markdown("---")
            st.markdown(HELP_MENU[selected_help])
        
        # Botão para fechar
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("✅ Fechar", use_container_width=True, type="primary"):
                st.rerun()

    def main_menu(self):
        """
        Menu principal da aplicação.
        """
        permissions = Token().get_user_permissions(
            token=st.session_state.token
        )
        if permissions:
            # Garantir que as permissões são uma lista
            perms_list = permissions.get("permissions", [])
            if isinstance(perms_list, list):
                st.session_state.user_permissions = sorted(perms_list)
            else:
                st.session_state.user_permissions = []
        else:
            st.session_state.user_permissions = []

        menu_options = {
            "📊 Dashboard": Dashboard,
            "🤖 Geração de Conteúdo": Texts,
        }

        with st.sidebar:
            st.markdown("""
            <div style="text-align: center; padding: 20px 0;">
                <h2 style="color: #1f77b4; margin-bottom: 5px;">📚 UniPost</h2>
                <p style="color: #666; font-size: 0.9rem;">
                    Gerador automático de Posts com IA
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.divider()

            # Informações do usuário
            if 'user_name' in st.session_state:
                st.markdown(f"""
                <div style="
                    background: linear-gradient(90deg, #667eea 0%,
                        #764ba2 100%);
                    padding: 15px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                    color: white;
                    text-align: center;
                ">
                    <strong>👤 {st.session_state.user_name}</strong><br>
                    <small>Usuário ativo</small>
                </div>
                """, unsafe_allow_html=True)

            st.subheader("Menu")

            # Menu com ícones melhorados
            selected_option = st.selectbox(
                label="Selecione uma opção:",
                options=list(menu_options.keys()),
                label_visibility="collapsed"
            )

            # Botão de ajuda
            st.markdown("<br>", unsafe_allow_html=True)
            help_button = st.button(
                "❓ Ajuda",
                use_container_width=True,
                type="secondary",
                help="Clique para ver o manual de uso da aplicação"
            )

            # Botão de logout com estilo melhorado
            logout_button = st.button(
                "🔓 Sair",
                use_container_width=True,
                type="secondary"
            )

            # Dialog de ajuda
            if help_button:
                self.show_help_dialog()

            if logout_button:
                with st.spinner("Encerrando sessão..."):
                    Token().logout(st.session_state.token)
                    st.session_state.pop("token", None)
                    st.session_state.pop("messages", None)
                    st.session_state.is_logged_in = False
                    sleep(1.5)
                st.toast("✅ Logout realizado com sucesso!")
                sleep(1)
                st.rerun()

        selected_option = menu_options[selected_option]
        selected_option().main_menu(
            st.session_state.token,
            st.session_state.user_permissions
        )
