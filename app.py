from api.login import Login
import streamlit as st


# CSS simplificado e otimizado
st.markdown("""
<style>
/* Variáveis CSS essenciais */
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --success-color: #28a745;
    --warning-color: #ffc107;
    --light-color: #f8f9fa;
    --dark-color: #343a40;
    --border-radius: 8px;
    --box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    --transition: all 0.2s ease;
}

/* Animação simples de entrada */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Estilos globais */
.main > div {
    padding-top: 1rem;
    animation: fadeIn 0.3s ease-out;
}

/* Botões simplificados */
.stButton > button {
    transition: var(--transition);
    border-radius: var(--border-radius);
    font-weight: 500;
}

.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: var(--box-shadow);
}

/* Inputs limpos */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    transition: var(--transition);
    border-radius: var(--border-radius);
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

/* Cards organizados */
.hover-card {
    transition: var(--transition);
    border-radius: var(--border-radius);
    cursor: pointer;
}

.hover-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--box-shadow);
}

/* Breadcrumbs */
.breadcrumb {
    display: flex;
    padding: 0.5rem 1rem;
    background: var(--light-color);
    border-radius: var(--border-radius);
    margin: 1rem 0;
}

.breadcrumb-item {
    color: var(--primary-color);
    text-decoration: none;
}

.breadcrumb-item + .breadcrumb-item::before {
    content: ">";
    margin: 0 0.5rem;
    color: #666;
}

/* Status badges */
.status-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 500;
}

.status-approved {
    background-color: #d4edda;
    color: #155724;
}

.status-pending {
    background-color: #fff3cd;
    color: #856404;
}

/* Responsividade */
@media (max-width: 768px) {
    .main > div {
        padding: 0.5rem;
    }

    .stColumns > div {
        margin-bottom: 1rem;
    }
}

/* Scrollbar simples */
::-webkit-scrollbar {
    width: 6px;
}

::-webkit-scrollbar-track {
    background: var(--light-color);
}

::-webkit-scrollbar-thumb {
    background: var(--primary-color);
    border-radius: 3px;
}

/* Foco acessível */
*:focus {
    outline: 2px solid var(--primary-color);
    outline-offset: 2px;
}
</style>
""", unsafe_allow_html=True)

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
