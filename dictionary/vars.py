from dotenv import load_dotenv
import os


load_dotenv()

API_HOST = os.getenv('DJANGO_API_URL')

API_BASE_URL = f"{API_HOST}/api/v1"
TOKEN_URL = f"{API_BASE_URL}/authentication/token/"

ABSOLUTE_APP_PATH = os.getcwd()

SERVER_CONFIG = """
[server]
headless = true
enableStaticServing = true"""

lorem_ipsum = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n
Maecenas a tincidunt justo. Mauris imperdiet ultricies libero semper mollis.\n
Ut feugiat rhoncus odio id commodo.
"""

C0NFIG_FILE_PATH: str = ".streamlit/config.toml"

PLATFORMS = {
    "FCB": "Facebook",
    "TTK": "Tiktok",
    "INT": "Instagram",
    "LKN": "Linkedin"
}

HELP_MENU = {
    "🏠 Página Inicial": """
    **Como utilizar a Página Inicial:**

    A página inicial é o ponto de entrada da aplicação UniPost.
    Aqui você encontra:

    • **Painel de Usuário**: Mostra suas informações e status de login
    • **Menu Principal**: Acesso rápido para Dashboard e Geração de Conteúdo
    • **Botão de Logout**: Para encerrar sua sessão com segurança

    **Dicas:**
    - Mantenha-se sempre logado para acessar todas as funcionalidades
    - Use o menu lateral para navegar entre as diferentes seções
    - Seu nome de usuário aparece destacado quando logado
    """,

    "📊 Dashboard": """
    **Como utilizar o Dashboard:**

    O Dashboard oferece uma visão completa das estatísticas dos textos gerados:

    • **Métricas Gerais**: Total de textos, pendentes,
    aprovados e plataformas utilizadas
    • **Gráfico de Status**: Visualização em pizza
    da distribuição de aprovações
    • **Gráfico por Plataforma**: Barras mostrando quantidade de posts
    por rede social
    • **Evolução Temporal**: Linha do tempo mostrando criação de posts por mês
    • **Insights Automáticos**: Análises inteligentes dos seus dados

    **Dicas:**
    - Use os gráficos para identificar tendências de aprovação
    - Monitore qual plataforma gera mais conteúdo
    - Acompanhe sua produtividade ao longo do tempo
    """,

    "🤖 Geração de Conteúdo": """
    **Como utilizar a Geração de Conteúdo:**

    Esta é a funcionalidade principal do UniPost para criar posts com IA:

    • **Tema do Texto**: Descreva detalhadamente o assunto do post
    • **Consulta de Busca**: Termos específicos para buscar referências
    • **Plataforma**: Escolha a rede social (
        Facebook, Instagram, TikTok, LinkedIn
    )
    • **Tom da Linguagem**: Defina o estilo (informal, formal, educativo, etc.)
    • **Nível de Criatividade**: Controle a originalidade do conteúdo
    • **Configurações Avançadas**: Tamanho, hashtags e call-to-action

    **Processo Inteligente:**
    1. Sistema busca referências na base de dados
    2. Encontra textos similares ao seu tema
    3. Gera conteúdo usando OpenAI GPT
    4. Salva automaticamente na API

    **Dicas:**
    - Seja específico no tema para melhores resultados
    - Experimente diferentes tons para variedade
    - Use o modo regeneração para melhorar posts existentes
    """,

    "📚 Biblioteca de Posts": """
    **Como utilizar a Biblioteca de Posts:**

    Visualize e gerencie todos os textos gerados pela IA:

    • **Filtros Avançados**: Busque por status (Aprovado/Pendente) ou termos
    • **Cards Informativos**: Cada post mostra tema, data, plataforma e preview
    • **Sistema de Aprovação**: Botões para aprovar, reprovar ou regenerar
    • **Status Visual**: Cores e ícones indicam o estado de cada post

    **Ações Disponíveis:**
    - ✅ **Aprovar**: Marca o post como aprovado para publicação
    - ❌ **Reprovar**: Marca como reprovado (precisa de revisão)
    - 🔄 **Regenerar**: Cria nova versão baseada no tema original

    **Dicas:**
    - Use filtros para encontrar posts específicos rapidamente
    - Aprove posts de qualidade para manter boas métricas
    - Regenere posts que não atenderam suas expectativas
    """,

    "🔐 Sistema de Login": """
    **Como utilizar o Sistema de Login:**

    Autenticação segura integrada com a API Django:

    • **Login Seguro**: Digite usuário e senha para acessar
    • **Validação JWT**: Sistema usa tokens seguros para autenticação
    • **Sessão Persistente**: Mantenha-se logado durante o uso
    • **Controle de Permissões**: Acesso baseado nas suas permissões

    **Tipos de Permissão:**
    - **Visualizar**: Ver posts existentes na biblioteca
    - **Criar**: Gerar novos textos com IA
    - **Editar**: Modificar posts e status de aprovação
    - **Admin**: Acesso completo ao sistema

    **Dicas:**
    - Mantenha suas credenciais seguras
    - Faça logout ao terminar de usar
    - Entre em contato com o admin se tiver problemas de permissão
    """,

    "📈 Métricas e Analytics": """
    **Como interpretar Métricas e Analytics:**

    Entenda o desempenho dos seus conteúdos:

    • **Taxa de Aprovação**: Porcentagem de posts aprovados vs total
    • **Distribuição por Plataforma**: Onde você produz mais conteúdo
    • **Evolução Temporal**: Tendência de produção ao longo do tempo
    • **Insights Automáticos**: Análises inteligentes dos padrões

    **Métricas Importantes:**
    - **Taxa ≥80%**: Excelente qualidade de conteúdo
    - **Taxa 60-79%**: Qualidade moderada, pode melhorar
    - **Taxa <60%**: Precisa revisar estratégia de geração

    **Insights Disponíveis:**
    - Plataforma mais utilizada
    - Período de maior produtividade
    - Padrões de aprovação
    - Sugestões de melhoria

    **Dicas:**
    - Monitore tendências para otimizar produção
    - Use insights para focar nas plataformas certas
    - Acompanhe taxa de aprovação para manter qualidade
    """
}
