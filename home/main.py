from api.token import Token
from texts.main import Texts
from dashboard.main import Dashboard
from time import sleep
import streamlit as st


class HomePage:
    """
    Classe que representa a página inicial da aplicação.
    """

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

            st.divider()

            # Informações adicionais
            with st.expander("ℹ️ Informações", expanded=False):
                st.markdown("""
                **Recursos disponíveis:**
                - ✅ Geração automática de textos
                - ✅ Busca inteligente no ElasticSearch
                - ✅ Cache otimizado com Redis
                - ✅ IA para processamento de linguagem
                - ✅ Sistema de aprovação de conteúdo
                """)

            # Botão de logout com estilo melhorado
            st.markdown("<br>", unsafe_allow_html=True)
            logout_button = st.button(
                "🔓 Sair do Sistema",
                use_container_width=True,
                type="secondary"
            )

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
