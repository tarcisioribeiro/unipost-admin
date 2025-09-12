from api.token import Token
from texts.main import Texts
from dashboard.main import Dashboard
from dictionary.vars import HELP_MENU
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
        st.header("📚 Como usar o UniPost")
        st.caption(
            "Selecione uma funcionalidade para ver as instruções detalhadas"
        )

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
            st.title("📚 UniPost")
            st.caption("Gerador automático de Posts com IA")

            st.divider()

            # Informações do usuário
            if 'user_name' in st.session_state:
                with st.container():
                    st.info(
                        f"👤 **{st.session_state.user_name}**\n\nUsuário ativo"
                    )

            st.subheader("Menu")

            # Menu com ícones melhorados
            selected_option = st.selectbox(
                label="Selecione uma opção:",
                options=list(menu_options.keys()),
                label_visibility="collapsed"
            )

            # Botão de ajuda
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
                st.toast("✅ Logout realizado com sucesso!")
                st.rerun()

        selected_class = menu_options[selected_option]
        selected_class().main_menu(
            st.session_state.token,
            st.session_state.user_permissions
        )
