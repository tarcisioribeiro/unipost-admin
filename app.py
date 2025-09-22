from api.login import Login
import streamlit as st


st.set_page_config(
    page_title="UniPost - Gerador de Posts",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get help': None,
        'Report a bug': None,
        'About': '''
        ### 🤖 UniPost - Gerador de Posts com IA

        **Versão:** 2.0
        **Desenvolvido com:** Streamlit & OpenAI

        Plataforma inteligente para geração automática de conteúdo para \
redes sociais.
        '''
    }
)


if __name__ == "__main__":
    Login().get_login()
