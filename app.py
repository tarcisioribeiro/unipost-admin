from api.login import Login
import streamlit as st


st.set_page_config(
    page_title="UniPost - Gerador de Posts",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


if __name__ == "__main__":
    Login().get_login()
