import streamlit as st
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
            st.error("""
            **⚠️ Acesso Restrito para Superusuário**

            O dashboard não está disponível para superusuários.
            Esta funcionalidade é destinada apenas aos usuários regulares
            que trabalham diretamente com a geração de textos.
            """)
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
            st.warning("""
            **🔒 Acesso Restrito**

            Você não possui permissões relacionadas aos textos.
            O dashboard está disponível apenas para usuários
            com permissões de texto (ler, criar, editar ou excluir).

            Entre em contato com o administrador do sistema.
            """)
            return

        # Cabeçalho do dashboard com estilo aprimorado
        st.markdown("""
        <div style="
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <h1 style="
                color: white;
                margin: 0;
                font-size: 2.5rem;
                font-weight: 700;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            ">
                📊 Dashboard Analytics
            </h1>
            <p style="
                color: rgba(255,255,255,0.9);
                margin: 0.5rem 0 0 0;
                font-size: 1.1rem;
                font-weight: 300;
            ">
                Análise completa dos textos gerados por IA
            </p>
        </div>
        """, unsafe_allow_html=True)

        texts = TextsRequest().get_texts(token)

        if not texts:
            col1, col2, col3 = st.columns(3)
            with col2:
                st.info("""
                **📄 Nenhum texto encontrado**

                Ainda não há textos para gerar estatísticas.
                Que tal gerar seu primeiro texto usando IA?
                """)
            return

        # Preparar dados para análise
        df = pd.DataFrame(texts)

        # Adicionar colunas processadas
        df['created_date'] = pd.to_datetime(df['created_at'].str[:10])
        # Formatação de mês em português brasileiro
        df['month_year_period'] = df['created_date'].dt.to_period('M')
        df['month_year'] = df['created_date'].dt.strftime('%m/%Y')
        df['platform_name'] = df['platform'].map(PLATFORMS)
        df['status_text'] = df['is_approved'].map(
            {
                True: 'Aprovado',
                False: 'Pendente'
            }
        )

        # Métricas principais com visual aprimorado
        st.markdown("""
        <div style="
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
            border-left: 4px solid #667eea;
        ">
            <h3 style="
                color: #333;
                margin: 0 0 1rem 0;
                font-size: 1.4rem;
                font-weight: 600;
            ">
                📈 Métricas Principais
            </h3>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)

        total_texts = len(texts)
        pending_texts = len(
            [t for t in texts if not t.get('is_approved', False)])
        approved_texts = len([t for t in texts if t.get('is_approved', False)])
        platforms_count = len(df['platform'].unique())

        # Cartões de métricas estilizados
        metrics_style = """
        <style>
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            margin: 0.5rem 0;
            border-top: 3px solid;
        }
        .metric-card.total { border-top-color: #667eea; }
        .metric-card.pending { border-top-color: #ffc107; }
        .metric-card.approved { border-top-color: #28a745; }
        .metric-card.platforms { border-top-color: #17a2b8; }
        </style>
        """
        st.markdown(metrics_style, unsafe_allow_html=True)

        with col1:
            st.metric(
                "📝 Total de Textos",
                total_texts,
                help="Número total de textos criados"
            )
        with col2:
            pending_percent = (pending_texts / total_texts *
                               100) if total_texts > 0 else 0
            st.metric(
                "⏳ Pendentes",
                pending_texts,
                delta=f"{pending_percent:.1f}%",
                delta_color="inverse",
                help="Textos aguardando aprovação"
            )
        with col3:
            approved_percent = (approved_texts / total_texts *
                                100) if total_texts > 0 else 0
            st.metric(
                "✅ Aprovados",
                approved_texts,
                delta=f"{approved_percent:.1f}%",
                delta_color="normal",
                help="Textos aprovados para publicação"
            )
        with col4:
            st.metric(
                "🌐 Plataformas",
                platforms_count,
                help="Número de plataformas utilizadas"
            )

        st.divider()

        # Seção de gráficos
        st.divider()

        # Gráficos em duas colunas
        col_left, col_right = st.columns(2)

        with col_left:
            # Gráfico de status (pizza 3D)
            st.markdown("### 📊 Status dos Textos")
            status_data = df['status_text'].value_counts()

            # Cores com gradiente 3D
            status_colors = ['#1f77b4', '#ff7f0e']  # Azul e laranja clássicos

            fig_status = go.Figure(data=[go.Pie(
                labels=status_data.index,
                values=status_data.values,
                textinfo='label+percent+value',
                textposition='auto',
                textfont=dict(size=12, color='white', family="Courier New"),
                marker=dict(
                    colors=status_colors,
                    line=dict(color='#000000', width=2)
                ),
                pull=[0.1, 0],
                sort=False
            )])

            fig_status.update_layout(
                title=dict(
                    text="Status Distribution",
                    x=0.5,
                    font=dict(size=16, color='#333333', family="Courier New")
                ),
                height=400,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.1,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=11, family="Courier New")
                ),
                margin=dict(t=50, b=50, l=50, r=50),
                font=dict(family="Courier New, monospace"),
                paper_bgcolor='rgba(248,249,250,1)',
                plot_bgcolor='rgba(248,249,250,1)'
            )

            st.plotly_chart(fig_status, use_container_width=True)

        with col_right:
            # Gráfico de plataformas (pizza 3D)
            st.markdown("### 🌐 Textos por Plataforma")
            platform_data = df['platform_name'].value_counts()

            # Cores 3D clássicas
            platform_colors = [
                '#2ca02c', '#d62728', '#9467bd', '#8c564b',
                '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
            ]

            fig_platform = go.Figure(data=[go.Pie(
                labels=platform_data.index,
                values=platform_data.values,
                textinfo='label+percent+value',
                textposition='auto',
                textfont=dict(size=11, color='white', family="Courier New"),
                marker=dict(
                    colors=platform_colors[:len(platform_data)],
                    line=dict(color='#000000', width=2)
                ),
                pull=[
                    0.1 if i == 0 else 0.05 for i in range(len(platform_data))
                ],
                sort=False
            )])

            fig_platform.update_layout(
                title=dict(
                    text="Platform Distribution",
                    x=0.5,
                    font=dict(size=16, color='#333333', family="Courier New")
                ),
                height=400,
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.02,
                    font=dict(size=10, family="Courier New")
                ),
                margin=dict(t=50, b=50, l=50, r=120),
                font=dict(family="Courier New, monospace"),
                paper_bgcolor='rgba(248,249,250,1)',
                plot_bgcolor='rgba(248,249,250,1)'
            )

            st.plotly_chart(fig_platform, use_container_width=True)

        # Gráfico de linha temporal com estilo
        st.markdown("""
        <div style="
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            margin: 2rem 0 1rem 0;
            border-left: 4px solid #667eea;
        ">
            <h3 style="
                color: #333;
                margin: 0;
                font-size: 1.4rem;
                font-weight: 600;
            ">
                📅 Evolução Temporal dos Textos
            </h3>
        </div>
        """, unsafe_allow_html=True)

        # Agrupar por mês
        monthly_data = df.groupby(
            ['month_year_period', 'status_text']).size().unstack(fill_value=0)

        # Converter índice Period para string para compatibilidade com Plotly
        monthly_data.index = monthly_data.index.astype(str)

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
            title="Evolução Temporal dos Textos",
            title_font_size=16,
            title_x=0.5,
            xaxis_title="Período",
            yaxis_title="Quantidade de Textos",
            height=450,
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=60, b=50, l=50, r=50),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            ),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)'
            )
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

            # Renomear o índice para português
            platform_summary.index.name = 'Plataforma'

            st.dataframe(
                platform_summary,
                use_container_width=True,
                hide_index=False,
                column_config={
                    "Total": st.column_config.NumberColumn(
                        "Total",
                        help="Total de textos criados",
                        format="%d"
                    ),
                    "Aprovados": st.column_config.NumberColumn(
                        "Aprovados",
                        help="Textos aprovados",
                        format="%d"
                    ),
                    "Pendentes": st.column_config.NumberColumn(
                        "Pendentes",
                        help="Textos pendentes",
                        format="%d"
                    ),
                    "Taxa Aprovação": st.column_config.TextColumn(
                        "Taxa Aprovação",
                        help="Percentual de aprovação"
                    )
                }
            )

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

            # Renomear o índice para português
            monthly_summary.index.name = 'Período'

            st.dataframe(
                monthly_summary,
                use_container_width=True,
                hide_index=False,
                column_config={
                    "Total": st.column_config.NumberColumn(
                        "Total",
                        help="Total de textos no período",
                        format="%d"
                    ),
                    "Aprovados": st.column_config.NumberColumn(
                        "Aprovados",
                        help="Textos aprovados no período",
                        format="%d"
                    ),
                    "Pendentes": st.column_config.NumberColumn(
                        "Pendentes",
                        help="Textos pendentes no período",
                        format="%d"
                    )
                }
            )

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

            # Taxa de aprovação - exibir como métrica permanente
            approval_rate = (
                approved_texts /
                total_texts *
                100) if total_texts > 0 else 0

            if approval_rate >= 80:
                icon = "📊"
            elif approval_rate >= 60:
                icon = "📈"
            else:
                icon = "📉"

            st.info(
                f"{icon} **Taxa de aprovação geral:** {approval_rate:.1f}%")

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
