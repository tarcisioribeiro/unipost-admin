"""
Módulo para página de configurações.

Este módulo contém a classe Settings responsável por gerenciar
as configurações do sistema e preferências do usuário.
"""

import streamlit as st
import os
from typing import Dict, Any


class Settings:
    """
    Classe responsável pela página de configurações.
    
    Esta classe gerencia as configurações do sistema,
    incluindo temas, preferências e configurações avançadas.
    """

    def __init__(self):
        """Inicializa a página de configurações."""
        pass

    def render_page(self) -> None:
        """Renderiza a página de configurações."""
        st.markdown("""
            <div class="custom-header fade-in">
                <h1>⚙️ Configurações</h1>
                <p style="margin: 8px 0 0 0; font-size: 16px; opacity: 0.9;">
                    Gerencie suas preferências e configurações do sistema
                </p>
            </div>
        """, unsafe_allow_html=True)

        st.divider()
        
        # User Preferences
        self._render_user_preferences()
        
        st.divider()
        
        # System Information
        self._render_system_info()
        
        st.divider()
        
        # Advanced Settings
        self._render_advanced_settings()


    def _render_user_preferences(self) -> None:
        """Renderiza a seção de preferências do usuário."""
        st.markdown("### 👤 Preferências do Usuário")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Configurações de Exibição:**")
            
            # Auto-refresh option
            auto_refresh = st.checkbox(
                "Auto-atualizar dados",
                value=st.session_state.get('auto_refresh', True),
                help="Atualiza automaticamente os dados ao navegar entre páginas",
                key="auto_refresh_setting"
            )
            st.session_state.auto_refresh = auto_refresh
            
            # Items per page
            items_per_page = st.slider(
                "Itens por página",
                min_value=6,
                max_value=30,
                value=st.session_state.get('items_per_page', 12),
                step=3,
                help="Número de posts exibidos por página na visualização",
                key="items_per_page_setting"
            )
            st.session_state.items_per_page = items_per_page
            
        with col2:
            st.markdown("**Configurações de Notificação:**")
            
            # Success notifications
            show_success = st.checkbox(
                "Exibir notificações de sucesso",
                value=st.session_state.get('show_success_notifications', True),
                help="Mostra mensagens de confirmação para ações bem-sucedidas",
                key="success_notifications_setting"
            )
            st.session_state.show_success_notifications = show_success
            
            # Error notifications
            show_errors = st.checkbox(
                "Exibir notificações de erro",
                value=st.session_state.get('show_error_notifications', True),
                help="Mostra mensagens de erro detalhadas",
                key="error_notifications_setting"
            )
            st.session_state.show_error_notifications = show_errors

    def _render_system_info(self) -> None:
        """Renderiza informações do sistema."""
        st.markdown("### 📊 Informações do Sistema")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Versão da Aplicação:**")
            st.markdown("""
                <div style="background: var(--input-dark); 
                           color: var(--secondary-blue); 
                           border: 1px solid var(--border-dark); 
                           padding: 8px 12px; 
                           border-radius: 6px; 
                           font-weight: 600; 
                           text-align: center; 
                           font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;">
                    v1.0.0
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("**Status dos Serviços:**")
            st.markdown("""
                - 🟢 **API Django**: Online
                - 🟢 **Redis Cache**: Conectado
                - 🟢 **Streamlit**: Executando
            """)
            
        with col2:
            st.markdown("**Estatísticas de Sessão:**")
            session_keys = len(st.session_state.keys())
            st.metric("Variáveis de Sessão", session_keys)
            
            st.markdown("**Cache:**")
            cache_status = "Ativo" if "cached_texts" in st.session_state else "Limpo"
            
            # Custom styled cache status
            cache_color = "var(--success-green)" if cache_status == "Ativo" else "var(--border-dark)"
            st.markdown(f"""
                <div style="background: var(--card-dark); 
                           border: 1px solid {cache_color}; 
                           border-radius: 8px; 
                           padding: 16px; 
                           text-align: center;
                           margin: 8px 0;">
                    <div style="color: var(--text-muted); font-size: 14px; margin-bottom: 4px;">Status do Cache</div>
                    <div style="color: var(--text-light); font-size: 24px; font-weight: 600;">{cache_status}</div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("🗑️ Limpar Cache", use_container_width=True, type="secondary"):
                keys_to_remove = [k for k in st.session_state.keys() if k.startswith('cached_')]
                for key in keys_to_remove:
                    del st.session_state[key]
                st.success("Cache limpo com sucesso!")
                st.rerun()

    def _render_advanced_settings(self) -> None:
        """Renderiza configurações avançadas."""
        st.markdown("### 🔧 Configurações Avançadas")
        
        with st.expander("⚠️ Configurações Avançadas", expanded=False):
            st.markdown("""
                <div style="background: var(--warning-yellow); 
                           color: var(--darker-navy); 
                           padding: 12px; 
                           border-radius: 8px; 
                           border: 1px solid var(--border-dark);
                           margin: 8px 0;">
                    <strong>⚠️ Atenção:</strong> Estas configurações são para usuários avançados. Alterações incorretas podem afetar o funcionamento do sistema.
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Debug Mode:**")
                debug_mode = st.checkbox(
                    "Ativar modo debug",
                    value=st.session_state.get('debug_mode', False),
                    help="Exibe informações detalhadas de debug",
                    key="debug_mode_setting"
                )
                st.session_state.debug_mode = debug_mode
                
                st.markdown("**API Timeout:**")
                api_timeout = st.number_input(
                    "Timeout da API (segundos)",
                    min_value=5,
                    max_value=60,
                    value=st.session_state.get('api_timeout', 10),
                    help="Tempo limite para requisições da API",
                    key="api_timeout_setting"
                )
                st.session_state.api_timeout = api_timeout
                
            with col2:
                st.markdown("**Ações de Sistema:**")
                
                if st.button("🔄 Reiniciar Sessão", use_container_width=True, type="secondary"):
                    # Clear all session state except auth
                    keys_to_keep = ['authenticated', 'user_token', 'username']
                    keys_to_remove = [k for k in st.session_state.keys() if k not in keys_to_keep]
                    for key in keys_to_remove:
                        del st.session_state[key]
                    st.success("Sessão reiniciada!")
                    st.rerun()
                
                if st.button("📋 Exportar Configurações", use_container_width=True, type="secondary"):
                    config_data = {
                        'auto_refresh': st.session_state.get('auto_refresh', True),
                        'items_per_page': st.session_state.get('items_per_page', 12),
                        'debug_mode': st.session_state.get('debug_mode', False),
                        'api_timeout': st.session_state.get('api_timeout', 10)
                    }
                    st.json(config_data)
                    st.info("Configurações exportadas. Você pode copiar estes dados para backup.")

