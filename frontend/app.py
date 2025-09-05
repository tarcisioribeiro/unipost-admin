import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os
from decouple import config

# Configuração da página
st.set_page_config(
    page_title="UniPOST - Geração de Texto com IA",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurações da API
API_BASE_URL = config('API_BASE_URL', default='http://localhost:8000/api/v1')

# CSS personalizado para design moderno
def load_css():
    """Carrega CSS personalizado para design moderno."""
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5rem;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .text-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .approved {
        border-left-color: #28a745;
    }
    
    .denied {
        border-left-color: #dc3545;
    }
    
    .pending {
        border-left-color: #ffc107;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    </style>
    """, unsafe_allow_html=True)


class APIClient:
    """Cliente para comunicação com a API Django."""
    
    def __init__(self):
        self.base_url = API_BASE_URL
        self.token = st.session_state.get('access_token')
    
    def get_headers(self):
        """Retorna headers com token de autenticação."""
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers
    
    def login(self, username, password):
        """Realiza login e retorna dados do usuário."""
        try:
            response = requests.post(
                f"{self.base_url}/auth/login/",
                json={'username': username, 'password': password}
            )
            if response.status_code == 200:
                data = response.json()
                st.session_state['access_token'] = data['access']
                st.session_state['refresh_token'] = data['refresh']
                st.session_state['user_data'] = data['user']
                self.token = data['access']
                return True, data['user']
            else:
                return False, response.json().get('detail', 'Erro de autenticação')
        except Exception as e:
            return False, str(e)
    
    def get_statistics(self):
        """Obtém estatísticas da aplicação."""
        try:
            response = requests.get(
                f"{self.base_url}/statistics/",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            st.error(f"Erro ao buscar estatísticas: {e}")
            return None
    
    def get_texts(self, filters=None):
        """Obtém lista de textos com filtros opcionais."""
        try:
            params = {}
            if filters:
                if 'is_approved' in filters:
                    params['is_approved'] = filters['is_approved']
                if 'my_texts' in filters:
                    params['my_texts'] = filters['my_texts']
            
            response = requests.get(
                f"{self.base_url}/texts/",
                params=params,
                headers=self.get_headers()
            )
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            st.error(f"Erro ao buscar textos: {e}")
            return []
    
    def generate_text(self, theme, model='gpt-4o-mini'):
        """Gera texto usando contexto do Elasticsearch."""
        try:
            response = requests.post(
                f"{self.base_url}/generate/",
                json={
                    'theme': theme,
                    'model': model
                },
                headers=self.get_headers()
            )
            if response.status_code == 201:
                return True, response.json()
            else:
                return False, response.json()
        except Exception as e:
            return False, str(e)
    
    def create_text(self, description, text_content):
        """Cria um novo texto."""
        try:
            response = requests.post(
                f"{self.base_url}/texts/",
                json={
                    'description': description,
                    'text_content': text_content
                },
                headers=self.get_headers()
            )
            if response.status_code == 201:
                return True, response.json()
            else:
                return False, response.json()
        except Exception as e:
            return False, str(e)
    
    def approve_text(self, text_id, is_approved):
        """Aprova ou nega um texto."""
        try:
            response = requests.patch(
                f"{self.base_url}/texts/{text_id}/approve/",
                json={'is_approved': is_approved},
                headers=self.get_headers()
            )
            return response.status_code == 200
        except Exception as e:
            st.error(f"Erro ao atualizar texto: {e}")
            return False


def show_login_page():
    """Exibe a tela de login."""
    st.markdown('<h1 class="main-header">🔐 Login - UniPOST</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            st.subheader("Acesso ao Sistema")
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar", use_container_width=True)
            
            if submit:
                if username and password:
                    api = APIClient()
                    success, result = api.login(username, password)
                    
                    if success:
                        st.success(f"Bem-vindo, {result['first_name'] or username}!")
                        st.rerun()
                    else:
                        st.error(f"Erro no login: {result}")
                else:
                    st.error("Por favor, preencha usuário e senha.")


def show_dashboard():
    """Exibe o dashboard com métricas."""
    st.markdown('<h1 class="main-header">📊 Dashboard - UniPOST</h1>', unsafe_allow_html=True)
    
    api = APIClient()
    stats = api.get_statistics()
    
    if stats:
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{stats['generated_texts']}</h3>
                <p>Textos Gerados</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{stats['approved_texts']}</h3>
                <p>Textos Aprovados</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{stats['denied_texts']}</h3>
                <p>Textos Negados</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            pending = stats['generated_texts'] - stats['approved_texts'] - stats['denied_texts']
            st.markdown(f"""
            <div class="metric-card">
                <h3>{pending}</h3>
                <p>Pendentes</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de pizza
            labels = ['Aprovados', 'Negados', 'Pendentes']
            values = [stats['approved_texts'], stats['denied_texts'], pending]
            colors = ['#28a745', '#dc3545', '#ffc107']
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=labels, 
                values=values,
                marker_colors=colors,
                hole=0.4
            )])
            
            fig_pie.update_layout(
                title="Distribuição de Status dos Textos",
                showlegend=True,
                height=400
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Gráfico de barras
            fig_bar = go.Figure(data=[
                go.Bar(x=labels, y=values, marker_color=colors)
            ])
            
            fig_bar.update_layout(
                title="Quantidade por Status",
                xaxis_title="Status",
                yaxis_title="Quantidade",
                height=400
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.error("Erro ao carregar estatísticas.")


def show_text_generation():
    """Exibe a tela de geração de textos."""
    st.markdown('<h1 class="main-header">✍️ Geração de Textos</h1>', unsafe_allow_html=True)
    
    # Formulário de geração
    with st.form("generation_form"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            tema = st.text_area(
                "Tema/Descrição do Texto",
                height=100,
                placeholder="Descreva o tema para geração do texto..."
            )
        
        with col2:
            modelo = st.selectbox(
                "Modelo de IA",
                ["GPT-4o-mini", "GPT-3.5-turbo", "Claude-3-Sonnet"],
                index=0
            )
            
            temperatura = st.slider("Temperatura", 0.0, 2.0, 0.7, 0.1)
        
        generate = st.form_submit_button("🚀 Gerar Texto", use_container_width=True)
        
        if generate:
            if tema:
                with st.spinner("Buscando contexto relevante e gerando texto..."):
                    # Gerar texto usando o novo endpoint com contexto
                    api = APIClient()
                    success, result = api.generate_text(tema, modelo.lower().replace('-', ''))
                    
                    if success:
                        st.success("✅ Texto gerado com sucesso!")
                        
                        # Mostrar informações sobre a geração
                        info_cols = st.columns(3)
                        with info_cols[0]:
                            st.metric("Contexto Utilizado", f"{result.get('context_used', 0)} docs")
                        with info_cols[1]:
                            st.metric("Modelo Usado", result.get('model_used', modelo))
                        with info_cols[2]:
                            st.metric("Status", "Pendente de Aprovação")
                        
                        # Exibir texto gerado
                        st.markdown("### 📄 Texto Gerado:")
                        texto_gerado = result['generated_text']
                        
                        st.markdown(f"""
                        <div class="text-card pending">
                            <h4>💡 Tema: {tema}</h4>
                            <div style="max-height: 400px; overflow-y: auto; padding: 1rem; background: white; border-radius: 5px; margin: 1rem 0;">
                                {texto_gerado.replace(chr(10), '<br>')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Botões de ação
                        st.markdown("### 🎯 Ações:")
                        col1, col2, col3 = st.columns(3)
                        
                        text_id = result['text_data']['id']
                        
                        with col1:
                            if st.button("✅ Aprovar", use_container_width=True, type="primary"):
                                if api.approve_text(text_id, True):
                                    st.success("✅ Texto aprovado com sucesso!")
                                    st.balloons()
                                    # TODO: Vetorizar texto aprovado
                                    st.rerun()
                                else:
                                    st.error("❌ Erro ao aprovar texto")
                        
                        with col2:
                            if st.button("🔄 Gerar Novamente", use_container_width=True):
                                st.info("🔄 Gerando novo texto...")
                                st.rerun()
                        
                        with col3:
                            if st.button("❌ Negar", use_container_width=True, type="secondary"):
                                if api.approve_text(text_id, False):
                                    st.warning("❌ Texto negado")
                                    st.rerun()
                                else:
                                    st.error("❌ Erro ao negar texto")
                    else:
                        error_msg = result.get('error', 'Erro desconhecido')
                        st.error(f"❌ Erro na geração: {error_msg}")
                        
                        # Mostrar detalhes do erro se disponível
                        if 'Nenhum contexto' in error_msg:
                            st.info("""
                            💡 **Dica:** Não foi encontrado contexto relevante no Elasticsearch para este tema.
                            Certifique-se de que o Elasticsearch está configurado e contém dados relevantes.
                            """)
            else:
                st.error("⚠️ Por favor, descreva o tema do texto.")


def show_text_visualization():
    """Exibe a visualização de textos."""
    st.markdown('<h1 class="main-header">👁️ Visualização de Textos</h1>', unsafe_allow_html=True)
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Filtrar por Status",
            ["Todos", "Aprovados", "Negados", "Pendentes"]
        )
    
    with col2:
        my_texts_filter = st.checkbox("Apenas meus textos")
    
    with col3:
        st.write("")  # Espaçamento
    
    # Montar filtros para API
    filters = {}
    if status_filter == "Aprovados":
        filters['is_approved'] = 'true'
    elif status_filter == "Negados":
        filters['is_approved'] = 'false'
    
    if my_texts_filter:
        filters['my_texts'] = 'true'
    
    # Buscar textos
    api = APIClient()
    texts = api.get_texts(filters)
    
    if texts:
        # Exibir textos em grid de 5 colunas
        texts_per_row = 5
        
        for i in range(0, len(texts), texts_per_row):
            cols = st.columns(texts_per_row)
            
            for j, text in enumerate(texts[i:i+texts_per_row]):
                with cols[j]:
                    status_class = "approved" if text['is_approved'] else "pending"
                    
                    st.markdown(f"""
                    <div class="text-card {status_class}">
                        <h5>{text['description'][:50]}...</h5>
                        <p><strong>Autor:</strong> {text['created_by']['username']}</p>
                        <p><strong>Data:</strong> {text['created_at'][:10]}</p>
                        <p><strong>Status:</strong> {'✅ Aprovado' if text['is_approved'] else '⏳ Pendente'}</p>
                        <details>
                            <summary>Ver texto completo</summary>
                            <p style="font-size: 0.8rem; margin-top: 0.5rem;">{text['text_content'][:200]}...</p>
                        </details>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("Nenhum texto encontrado com os filtros aplicados.")


def show_sidebar():
    """Exibe a barra lateral com menu de navegação."""
    with st.sidebar:
        st.markdown("### 👤 Usuário Logado")
        user_data = st.session_state.get('user_data', {})
        st.write(f"**{user_data.get('first_name', 'Usuário')}**")
        st.write(f"@{user_data.get('username', 'user')}")
        
        st.markdown("---")
        
        # Menu de navegação
        menu_items = [
            "📊 Dashboard",
            "✍️ Geração de Textos", 
            "👁️ Visualização de Textos"
        ]
        
        selected = st.selectbox("Navegação", menu_items)
        
        st.markdown("---")
        
        if st.button("🚪 Sair", use_container_width=True):
            for key in ['access_token', 'refresh_token', 'user_data']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        return selected


def main():
    """Função principal da aplicação."""
    load_css()
    
    # Verificar se o usuário está logado
    if 'access_token' not in st.session_state:
        show_login_page()
        return
    
    # Mostrar sidebar e obter página selecionada
    selected_page = show_sidebar()
    
    # Exibir página selecionada
    if selected_page == "📊 Dashboard":
        show_dashboard()
    elif selected_page == "✍️ Geração de Textos":
        show_text_generation()
    elif selected_page == "👁️ Visualização de Textos":
        show_text_visualization()


if __name__ == "__main__":
    main()