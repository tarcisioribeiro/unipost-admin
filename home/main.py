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
            # Cabeçalho da sidebar estilizado
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1.5rem;
                border-radius: 12px;
                margin-bottom: 1.5rem;
                text-align: center;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            ">
                <h2 style="
                    color: white;
                    margin: 0 0 0.5rem 0;
                    font-size: 1.8rem;
                    font-weight: 700;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                ">
                    🤖 UniPost
                </h2>
                <p style="
                    color: rgba(255,255,255,0.9);
                    margin: 0;
                    font-size: 0.9rem;
                    font-weight: 300;
                ">
                    Gerador automático de Posts com IA
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Informações do usuário estilizadas
            if 'user_name' in st.session_state:
                st.markdown(f"""
                <div style="
                    background-color: #e8f5e8;
                    padding: 1rem;
                    border-radius: 8px;
                    margin-bottom: 1rem;
                    border-left: 4px solid #28a745;
                ">
                    <p style="
                        margin: 0;
                        color: #155724;
                        font-weight: 500;
                        line-height: 1.4;
                    ">
                        👤 <strong>{st.session_state.user_name}</strong><br>
                        <span style="font-size: 0.9rem; opacity: 0.8;">\
Usuário ativo</span>
                    </p>
                </div>
                """, unsafe_allow_html=True)

            # Breadcrumb de navegação
            st.markdown("""
            <div class="breadcrumb">
                <span class="breadcrumb-item">🏠 Início</span>
                <span class="breadcrumb-item">Menu Principal</span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="
                background-color: #f8f9fa;
                padding: 1rem;
                border-radius: 8px;
                margin: 1rem 0;
                border-left: 4px solid #667eea;
            ">
                <h4 style="
                    color: #333;
                    margin: 0;
                    font-size: 1.2rem;
                    font-weight: 600;
                ">
                    📋 Menu de Navegação
                </h4>
            </div>
            """, unsafe_allow_html=True)

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
