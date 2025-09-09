"""
Módulo para a página de dashboard.

Este módulo contém a classe Dashboard responsável por exibir
estatísticas e informações gerais do sistema.
"""

import streamlit as st
from typing import Dict, Any


class Dashboard:
    """
    Classe responsável pela página de dashboard.
    
    Esta classe gerencia a exibição do dashboard principal
    com estatísticas e ações rápidas do sistema.
    """

    def __init__(self):
        """Inicializa o dashboard."""
        pass

    def render_page(self) -> None:
        """Renderiza a página do dashboard."""
        st.markdown("""
            <div class="custom-header fade-in">
                <h1>📊 Dashboard</h1>
                <p style="margin: 8px 0 0 0; font-size: 16px; opacity: 0.9;">
                    Sistema de Geração de Posts com IA
                </p>
            </div>
        """, unsafe_allow_html=True)

        # Stats
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
                <div class="metric-card fade-in">
                    <h2 style="color: var(--primary-blue); margin: 0; font-size: 2.5em;">--</h2>
                    <p style="color: var(--medium-gray); margin: 8px 0 0 0; font-weight: 600;">
                        📝 Textos Gerados
                    </p>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
                <div class="metric-card fade-in">
                    <h2 style="color: var(--success-green); margin: 0; font-size: 2.5em;">--</h2>
                    <p style="color: var(--medium-gray); margin: 8px 0 0 0; font-weight: 600;">
                        ✅ Aprovados
                    </p>
                </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
                <div class="metric-card fade-in">
                    <h2 style="color: var(--warning-yellow); margin: 0; font-size: 2.5em;">--</h2>
                    <p style="color: var(--medium-gray); margin: 8px 0 0 0; font-weight: 600;">
                        ⏳ Pendentes
                    </p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

        # Quick actions
        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "Gerar Novo Texto",
                use_container_width=True,
                type="primary"
            ):
                st.session_state["nav_clicked"] = "Geração de Posts"
                st.rerun()

        with col2:
            if st.button("Ver Textos", use_container_width=True):
                st.session_state["nav_clicked"] = "Visualização de Posts"
                st.rerun()

        # Recent activity section
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        st.markdown("### 📈 Atividade Recente")
        
        # Mock recent activity data
        st.info("Funcionalidade de atividade recente será implementada em breve.")
        
        # System health indicators
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        st.markdown("### 🔧 Status do Sistema")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
                <div class="service-status">
                    🟢 <strong>API Django</strong> - Online
                </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
                <div class="service-status">
                    🟢 <strong>Redis Cache</strong> - Conectado
                </div>
            """, unsafe_allow_html=True)