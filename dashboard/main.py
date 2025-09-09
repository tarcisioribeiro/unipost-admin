import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from texts.request import TextsRequest
from dictionary.vars import PLATFORMS


class Dashboard:
    """
    Classe responsável pelo dashboard com estatísticas e gráficos dos textos.
    """

    def __init__(self):
        pass

    def format_br_date(self, date_str):
        """Converte data para formato brasileiro."""
        if date_str and len(date_str) >= 10:
            try:
                date_obj = datetime.strptime(date_str[:10], '%Y-%m-%d')
                return date_obj.strftime('%d/%m/%Y')
            except BaseException:
                return date_str[:10]
        return 'N/A'

    def main_menu(self, token, permissions):
        """
        Exibe o dashboard principal com estatísticas e gráficos.

        Parameters
        ----------
        token : str
            Token de autenticação do usuário
        permissions : list
            Lista de permissões do usuário
        """
        # Verificar se é superusuário (admin)
        from api.token import Token
        user_data = Token().get_user_permissions(token)
        is_superuser = user_data.get(
            'is_superuser', False) if user_data else False

        if is_superuser:
            st.markdown("""
            <div style="text-align: center; padding: 50px;
                background: #f8d7da; border-radius: 15px;
                border: 1px solid #f5c6cb;">
                <h3 style="color: #721c24;">
                    ⚠️ Acesso Restrito para Superusuário
                </h3>
                <p style="color: #721c24; font-size: 1.1rem;">
                    O dashboard não está disponível para superusuários.<br>
                    Esta funcionalidade é destinada apenas aos usuários
                        regulares<br>
                    que trabalham diretamente com a geração de textos.
                </p>
            </div>
            """, unsafe_allow_html=True)
            return

        # Verificar se tem permissões de texto usando formato Django
        django_text_permissions = [
            'texts.add_text',
            'texts.view_text',
            'texts.change_text',
            'texts.delete_text'
        ]
        has_text_permission = any(
            perm in permissions for perm in django_text_permissions)

        if not has_text_permission:
            st.markdown("""
            <div style="text-align: center; padding: 50px;
                background: #fff3cd; border-radius: 15px;
                border: 1px solid #ffeaa7;">
                <h3 style="color: #856404;">🔒 Acesso Restrito</h3>
                <p style="color: #856404; font-size: 1.1rem;">
                    Você não possui permissões relacionadas aos textos.<br>
                    O dashboard está disponível apenas para usuários<br>
                    com permissões de texto (ler, criar, editar ou excluir).
                    <br>
                <br>
                    Entre em contato com o administrador do sistema.
                </p>
            </div>
            """, unsafe_allow_html=True)
            return

        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <h1 style="color: #1f77b4;">📊 Dashboard</h1>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        texts = TextsRequest().get_texts(token)

        if not texts:
            st.markdown("""
            <div style="text-align: center; padding: 50px;
                background: #f8f9fa; border-radius: 15px;
                border: 2px dashed #dee2e6;">
                <h3 style="color: #6c757d;">📄 Nenhum texto encontrado</h3>
                <p style="color: #6c757d; font-size: 1.1rem;">
                    Ainda não há textos para gerar estatísticas.<br>
                    Que tal gerar seu primeiro texto usando IA?
                </p>
            </div>
            """, unsafe_allow_html=True)
            return

        # Preparar dados para análise
        df = pd.DataFrame(texts)

        # Adicionar colunas processadas
        df['created_date'] = pd.to_datetime(df['created_at'].str[:10])
        df['month_year'] = df['created_date'].dt.to_period('M').astype(str)
        df['platform_name'] = df['platform'].map(PLATFORMS)
        df['status_text'] = df['is_approved'].map(
            {
                True: 'Aprovado',
                False: 'Pendente'
            }
        )

        # Métricas principais
        st.markdown("### 📈 Métricas Gerais")

        col1, col2, col3, col4 = st.columns(4)

        total_texts = len(texts)
        pending_texts = len(
            [t for t in texts if not t.get('is_approved', False)])
        approved_texts = len([t for t in texts if t.get('is_approved', False)])
        platforms_count = len(df['platform'].unique())

        with col1:
            st.metric("📝 Total de Textos", total_texts)
        with col2:
            st.metric(
                "⏳ Pendentes",
                pending_texts,
                delta=f"{(pending_texts / total_texts * 100):.1f}%" if (
                    total_texts > 0
                ) else "0%"
            )
        with col3:
            st.metric(
                "✅ Aprovados",
                approved_texts,
                delta=f"{(approved_texts / total_texts * 100):.1f}%" if (
                    total_texts > 0
                ) else "0%"
            )
        with col4:
            st.metric("🌐 Plataformas", platforms_count)

        st.divider()

        # Gráficos em duas colunas
        col_left, col_right = st.columns(2)

        with col_left:
            # Gráfico de status (pizza)
            st.markdown("### 📊 Status dos Textos")
            status_data = df['status_text'].value_counts()

            fig_status = px.pie(
                values=status_data.values,
                names=status_data.index,
                title="Distribuição por Status",
                color_discrete_map={
                    'Aprovado': '#28a745',
                    'Pendente': '#ffc107'
                }
            )
            fig_status.update_layout(height=400)
            st.plotly_chart(fig_status, use_container_width=True)

        with col_right:
            # Gráfico de plataformas (barras)
            st.markdown("### 🌐 Textos por Plataforma")
            platform_data = df['platform_name'].value_counts()

            fig_platform = px.bar(
                x=platform_data.index,
                y=platform_data.values,
                title="Quantidade por Plataforma",
                color=platform_data.values,
                color_continuous_scale="viridis"
            )
            fig_platform.update_layout(
                height=400,
                xaxis_title="Plataforma",
                yaxis_title="Quantidade",
                showlegend=False
            )
            fig_platform.update_layout(xaxis_tickangle=45)
            st.plotly_chart(fig_platform, use_container_width=True)

        # Gráfico de linha temporal
        st.markdown("### 📅 Evolução Temporal")

        # Agrupar por mês
        monthly_data = df.groupby(
            ['month_year', 'status_text']).size().unstack(fill_value=0)

        fig_timeline = go.Figure()

        if 'Aprovado' in monthly_data.columns:
            fig_timeline.add_trace(
                go.Scatter(
                    x=monthly_data.index,
                    y=monthly_data['Aprovado'],
                    mode='lines+markers',
                    name='Aprovados',
                    line=dict(color='#28a745', width=3),
                    marker=dict(size=8)
                )
            )

        if 'Pendente' in monthly_data.columns:
            fig_timeline.add_trace(
                go.Scatter(
                    x=monthly_data.index,
                    y=monthly_data['Pendente'],
                    mode='lines+markers',
                    name='Pendentes',
                    line=dict(color='#ffc107', width=3),
                    marker=dict(size=8)
                )
            )

        fig_timeline.update_layout(
            title="Textos Criados por Mês",
            xaxis_title="Período",
            yaxis_title="Quantidade de Textos",
            height=400,
            hovermode='x unified'
        )

        st.plotly_chart(fig_timeline, use_container_width=True)

        st.divider()

        # Tabela resumo detalhada
        st.markdown("### 📋 Resumo Detalhado")

        col_table1, col_table2 = st.columns(2)

        with col_table1:
            st.markdown("#### Por Plataforma")
            platform_summary = df.groupby('platform_name').agg({
                'id': 'count',
                'is_approved': lambda x: sum(x),
            }).rename(columns={'id': 'Total', 'is_approved': 'Aprovados'})
            platform_summary['Pendentes'] = platform_summary['Total'] - \
                platform_summary['Aprovados']
            platform_summary['Taxa Aprovação'] = (
                platform_summary['Aprovados'] / platform_summary['Total'] * 100
            ).round(1).astype(str) + '%'

            st.dataframe(platform_summary, use_container_width=True)

        with col_table2:
            st.markdown("#### Por Período")
            monthly_summary = df.groupby('month_year').agg({
                'id': 'count',
                'is_approved': lambda x: sum(x),
            }).rename(columns={'id': 'Total', 'is_approved': 'Aprovados'})
            monthly_summary['Pendentes'] = monthly_summary['Total'] - \
                monthly_summary['Aprovados']
            monthly_summary = monthly_summary.sort_index(
                ascending=False).head(6)  # Últimos 6 meses

            st.dataframe(monthly_summary, use_container_width=True)

        # Insights automáticos
        st.markdown("### 💡 Insights")

        insights_col1, insights_col2 = st.columns(2)

        with insights_col1:
            # Plataforma mais utilizada
            top_platform = platform_data.index[0] if len(
                platform_data) > 0 else "N/A"
            top_platform_count = platform_data.iloc[0] if len(
                platform_data) > 0 else 0

            st.info(
                f"""🏆 **Plataforma mais utilizada:** {
                    top_platform
                } ({top_platform_count} textos)""")

            # Taxa de aprovação
            approval_rate = (
                approved_texts /
                total_texts *
                100) if total_texts > 0 else 0
            if approval_rate >= 80:
                st.success(
                    f"✅ **Excelente taxa de aprovação:** {approval_rate:.1f}%")
            elif approval_rate >= 60:
                st.warning(
                    f"⚠️ **Taxa de aprovação moderada:** {approval_rate:.1f}%")
            else:
                st.error(
                    f"⚠️ **Taxa de aprovação baixa:** {approval_rate:.1f}%")

        with insights_col2:
            # Textos criados nos últimos 7 dias
            last_week = datetime.now() - timedelta(days=7)
            recent_texts = len([t for t in texts if datetime.strptime(
                t['created_at'][:10], '%Y-%m-%d') >= last_week])

            if recent_texts > 0:
                st.info(
                    f"📈 **Textos criados na última semana:** {recent_texts}")
            else:
                st.info("📊 **Nenhum texto criado na última semana**")

            # Média de textos por mês
            if len(monthly_data) > 0:
                avg_per_month = total_texts / len(monthly_data)
                st.info(f"📅 **Média por mês:** {int(avg_per_month)} textos")
