from api.login import Login
import streamlit as st
import os


st.set_page_config(
    page_title="UniPost - Gerador de Posts",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Carregar CSS customizado


def load_custom_css():
    """Carrega estilos CSS customizados para melhorar a aparência"""
    css_file_path = "style/custom.css"
    if os.path.exists(css_file_path):
        with open(css_file_path, "r") as css_file:
            st.markdown(
                f"""<style>{
                    css_file.read()}</style>""",
                unsafe_allow_html=True)

    # CSS adicional inline para elementos específicos
    st.markdown("""
    <style>
    /* Hide Streamlit header and footer */
    header[data-testid="stHeader"] {
        background-color: rgba(0,0,0,0);
        height: 0px;
    }

    .stDeployButton {
        visibility: hidden;
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb {
        background: #1f77b4;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #17a2b8;
    }

    /* Improve sidebar styling */
    .css-1d391kg {
        padding-top: 1rem;
    }

    /* Better spacing for main content */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)


# Aplicar estilos customizados
load_custom_css()


if __name__ == "__main__":
    Login().get_login()
