# 📝 UniPost - Sistema Inteligente de Geração de Posts com IA

Sistema avançado para geração automática de posts para redes sociais utilizando Inteligência Artificial, com interface moderna em Streamlit, autenticação segura, sistema de busca semântica e cache inteligente.

## 🚀 Características Principais

- **🤖 Geração Inteligente de Posts**: IA avançada com OpenAI GPT para múltiplas plataformas sociais
- **🔍 Busca Semântica**: ElasticSearch para encontrar conteúdos relacionados automaticamente
- **🧠 Vetorização com SentenceTransformers**: Análise semântica profunda dos textos
- **⚡ Cache Redis**: Sistema de cache inteligente para otimização de performance
- **🔐 Autenticação JWT**: Login seguro integrado com API Django
- **📊 Dashboard Analytics**: Métricas detalhadas, gráficos interativos e insights automáticos
- **🎯 Sistema de Aprovação**: Workflow completo para gerenciar posts gerados
- **❓ Sistema de Ajuda**: Manual interativo integrado na sidebar da aplicação
- **🌐 Multi-Plataforma**: Suporte para Facebook, Instagram, TikTok e LinkedIn
- **🔧 Configurações Avançadas**: Personalização completa da experiência do usuário

## 🏗️ Arquitetura do Sistema

```
UniPost/
├── app.py                          # 🚀 Ponto de entrada principal
├── api/                           # 🔗 Integração com API Django
│   ├── __init__.py
│   ├── login.py                   # Sistema de autenticação
│   └── token.py                   # Gerenciamento de JWT tokens
├── home/                          # 🏠 Página inicial e navegação
│   └── main.py                    # Menu principal com sistema de ajuda
├── dashboard/                     # 📊 Analytics e métricas
│   └── main.py                    # Dashboard com gráficos interativos
├── texts/                         # 🤖 Geração e gerenciamento de textos
│   ├── __init__.py
│   ├── main.py                    # Interface principal de geração IA
│   └── request.py                 # Requisições para API
├── services/                      # ⚙️ Serviços core do sistema
│   ├── __init__.py
│   ├── elasticsearch_service.py   # Busca semântica avançada
│   ├── redis_service.py           # Cache inteligente de vetores
│   └── text_generation_service.py # IA e vetorização
├── dictionary/                    # 📚 Configurações e dados
│   └── vars.py                    # Constantes, plataformas e manual de ajuda
├── references/                    # 🔧 Utilitários e funções auxiliares
│   └── functions.py
├── style/                         # 🎨 Estilos e temas visuais
│   └── custom.css                 # CSS customizado
├── .streamlit/                    # ⚙️ Configurações do Streamlit
├── venv/                          # 🐍 Ambiente virtual Python
├── docs/                          # 📖 Documentação do projeto
│   ├── build.md
│   ├── errors.md
│   ├── instructions.md
│   └── upgrade.md
├── docker-compose.yml             # 🐳 Orquestração de containers
├── Dockerfile                     # 🐳 Container da aplicação
└── requirements.txt               # 📦 Dependências Python
```

## 🛠️ Stack Tecnológico

### 🎨 Frontend & Interface
- **Streamlit 1.49.1**: Interface web moderna e responsiva
- **CSS Customizado**: Temas claro/escuro com design profissional
- **Plotly**: Gráficos interativos no dashboard (Express & Graph Objects)
- **st.dialog**: Sistema de diálogos modais para ajuda integrada

### 🤖 Inteligência Artificial & Machine Learning
- **OpenAI GPT-4o-mini**: Geração de texto com qualidade profissional
- **SentenceTransformers (all-MiniLM-L6-v2)**: Vetorização semântica de textos
- **HuggingFace Transformers**: Pipeline completo de processamento de linguagem natural
- **NumPy & SciPy**: Operações matemáticas para similaridade de vetores

### 🔍 Busca & Cache
- **Elasticsearch 9.1.0**: Busca semântica avançada e indexação de conteúdo
- **Redis 7-alpine**: Cache inteligente de vetores com expiração automática
- **Similaridade Coseno**: Algoritmo para encontrar conteúdos relacionados

### 🔐 Backend & API
- **Django API (externa)**: Autenticação, CRUD e gerenciamento de dados
- **JWT (PyJWT 2.8.0)**: Tokens seguros para autenticação stateless
- **Requests**: Cliente HTTP para integração com APIs externas

### 🐳 DevOps & Containerização
- **Docker & Docker Compose**: Orquestração de containers
- **Redis Commander**: Interface web para monitoramento do cache
- **Health Checks**: Monitoramento automático dos serviços

### 🔧 Desenvolvimento & Qualidade
- **MyPy 1.17.1**: Type checking estático
- **Flake8 7.3.0**: Linting e verificação de código
- **Autopep8 2.3.2**: Formatação automática seguindo PEP 8
- **Python-dotenv**: Gerenciamento de variáveis de ambiente

## 📋 Pré-requisitos

- Docker >= 20.0
- Docker Compose >= 2.0
- Python 3.11+ (para desenvolvimento local)
- API Django configurada e acessível
- Chave da API OpenAI (opcional)

## 🚀 Instalação e Execução

### 1. Clone o Repositório

```bash
git clone <repository-url>
cd UniPost
```

### 2. Configure as Variáveis de Ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações:

```bash
# Django API Configuration
DJANGO_API_URL=http://localhost:8005

# OpenAI Configuration (opcional)
OPENAI_API_KEY=your_openai_api_key

# Elasticsearch Configuration (opcional)
ES_HOST=https://your-elasticsearch-host:9200
ES_USER=elastic
ES_PASS=your_elasticsearch_password

# Redis Configuration
REDIS_URL=redis://redis:6379/0
```

### 3. Execute com Docker Compose

```bash
# Construir e executar todos os serviços
docker compose up --build -d

# Ou usar o comando de reconstrução completa
docker compose down -v && docker compose up --build -d
```

### 4. Acesse a Aplicação

- **Aplicação Principal**: http://localhost:8555
- **Redis Commander**: http://localhost:8081

## 📱 Funcionalidades Detalhadas

### 🔐 Sistema de Autenticação Segura
- **Login JWT**: Autenticação via tokens seguros da API Django
- **Sessão Persistente**: Mantenha-se logado durante todo o uso
- **Controle de Permissões**: Acesso diferenciado baseado em roles
- **Logout Seguro**: Limpeza completa de dados da sessão
- **Validação em Tempo Real**: Verificação contínua do token

### 📊 Dashboard Analytics Avançado
- **Métricas Principais**: Total de posts, taxa de aprovação, distribuição por plataforma
- **Gráficos Interativos**: Pizza, barras e linha temporal com Plotly
- **Insights Automáticos**: Análises inteligentes dos padrões de conteúdo
- **Resumo Detalhado**: Tabelas com estatísticas por plataforma e período
- **Restrições de Acesso**: Interface adaptada conforme permissões do usuário

### 🤖 Geração Inteligente de Conteúdo
#### Fluxo Completo de IA:
1. **Busca Automática**: ElasticSearch encontra conteúdos relacionados
2. **Vetorização Semântica**: SentenceTransformers analisa significado dos textos
3. **Cache Inteligente**: Redis armazena vetores para performance otimizada
4. **Similaridade Contextual**: Algoritmo coseno identifica referências relevantes
5. **Geração via LLM**: OpenAI GPT cria conteúdo baseado no contexto
6. **Salvamento Automático**: Post registrado na API com metadata completo

#### Configurações Avançadas:
- **Plataformas**: Facebook, Instagram, TikTok, LinkedIn com otimização específica
- **Tom de Linguagem**: 8 opções (informal, formal, educativo, técnico, etc.)
- **Nível de Criatividade**: 6 níveis de originalidade
- **Tamanho Customizável**: Curto, médio ou longo
- **Hashtags Inteligentes**: Inclusão automática de tags relevantes
- **Call-to-Action**: Chamadas para ação personalizadas

### 📚 Biblioteca de Posts Avançada
- **Filtros Múltiplos**: Status, palavra-chave, data e plataforma
- **Cards Informativos**: Preview completo com metadata
- **Sistema de Aprovação**: Workflow completo (aprovar/reprovar/regenerar)
- **Status Visual**: Códigos de cores e ícones intuitivos
- **Paginação Inteligente**: Navegação otimizada para grandes volumes
- **Busca Semântica**: Encontre posts por contexto, não apenas palavras exatas

### ❓ Sistema de Ajuda Integrado
- **Dialog Modal**: Interface elegante sem sair da aplicação
- **Manual Interativo**: 10 seções detalhadas de funcionalidades
- **Instruções Contextuais**: Dicas específicas para cada ferramenta
- **Acesso Rápido**: Botão na sidebar sempre disponível
- **Conteúdo Atualizado**: Documentação sincronizada com features

### ⚙️ Configurações e Personalização
- **Temas Visuais**: Modo claro/escuro com CSS otimizado
- **Preferências de Interface**: Auto-refresh, timeout, itens por página
- **Debug Mode**: Logs detalhados para troubleshooting
- **Gerenciamento de Cache**: Limpeza e monitoramento do Redis
- **Exportação de Configurações**: Backup das preferências do usuário

## 🏠 Estrutura das Páginas

### Página Inicial (`home/main.py`)
- **Menu Principal**: Navegação intuitiva entre Dashboard e Geração de Conteúdo
- **Painel do Usuário**: Informações de login e permissões
- **❓ Sistema de Ajuda**: Botão integrado na sidebar com manual interativo
- **Logout Seguro**: Encerramento de sessão com limpeza de dados

### Dashboard Analytics (`dashboard/main.py`)
- **Métricas Principais**: Total, aprovados, pendentes e plataformas
- **Gráficos Plotly**: Pizza (status), barras (plataformas) e timeline (evolução)
- **Insights Automáticos**: Análises inteligentes dos padrões
- **Restrições**: Interface adaptada para superusuários e permissões
- **Tabelas Resumo**: Estatísticas detalhadas por plataforma e período

### Geração de Posts (`texts/main.py`)
- **Interface Dual**: Parâmetros (esquerda) e resultado (direita)
- **Formulário Inteligente**: Tema, plataforma, tom, criatividade
- **Processo IA Transparente**: Barra de progresso com etapas detalhadas
- **Ações Completas**: Aprovar, reprovar, regenerar, copiar, limpar
- **Modo Regeneração**: Carregamento automático de dados de posts existentes

### Biblioteca de Posts (`texts/main.py` - método render)
- **Cards Informativos**: Layout elegante com preview e metadata
- **Filtros Avançados**: Status, palavra-chave com busca em tempo real
- **Sistema de Ações**: Botões contextuais para cada post
- **Paginação**: Exibição otimizada para grandes volumes
- **Cores Semânticas**: Verde (aprovado), amarelo (pendente)

## 🔧 Configuração de Desenvolvimento

## ❓ Sistema de Ajuda Integrado

### Implementação do Manual Interativo

O UniPost agora inclui um sistema de ajuda completo integrado na sidebar:

#### Localização: `home/main.py` 
```python
@st.dialog("❓ Manual de Uso - UniPost")
def show_help_dialog(self):
    # Dialog modal elegante com st.selectbox para navegar entre tópicos
```

#### Configuração: `dictionary/vars.py`
```python
HELP_MENU = {
    "🏠 Página Inicial": "...",      # Instruções da tela inicial
    "📊 Dashboard": "...",            # Como usar analytics
    "🤖 Geração de Conteúdo": "...", # Manual da IA
    "📚 Biblioteca de Posts": "...",  # Gerenciamento de posts
    "🔐 Sistema de Login": "...",     # Autenticação e permissões
    "⚙️ Configurações Avançadas": "...", # Personalização
    "🧠 Inteligência Artificial": "...", # Como funciona a IA
    "🔍 Busca e Filtros": "...",     # Sistema de busca
    "📈 Métricas e Analytics": "...", # Interpretação de dados
}
```

#### Características:
- **Acesso Imediato**: Botão `❓ Ajuda` sempre visível na sidebar
- **Dialog Modal**: Interface elegante sem sair da aplicação
- **10 Seções Detalhadas**: Cobertura completa de todas as funcionalidades
- **Navegação Intuitiva**: st.selectbox para alternar entre tópicos
- **Conteúdo Rico**: Instruções detalhadas com dicas práticas
- **Design Responsivo**: Interface adaptada para diferentes dispositivos

### Estrutura de Serviços

```python
# Principais serviços implementados
services/
├── elasticsearch_service.py    # Busca semântica com multi_match queries
├── redis_service.py            # Cache inteligente com hash MD5 e TTL
├── text_generation_service.py  # Pipeline IA: vetorização → similaridade → LLM
└── __init__.py

# Fluxo de dados dos serviços
1. ElasticSearch → busca conteúdos relacionados
2. SentenceTransformers → vetorização semântica  
3. Redis → cache de vetores processados
4. OpenAI GPT → geração contextualizada
5. Django API → persistência e CRUD
```

### Componentes Principais

```python
# Arquitetura modular implementada
api/
├── login.py          # AuthenticationService integrado
├── token.py          # JWTManager com validação contínua
└── __init__.py

home/
└── main.py           # HomePage com HelpSystem integrado

dashboard/
└── main.py           # Dashboard com Plotly analytics

texts/
├── main.py           # TextGenerator com IA pipeline
├── request.py        # APIClient para CRUD operations
└── __init__.py

dictionary/
└── vars.py           # Constants, PLATFORMS, HELP_MENU
```

## 📊 Monitoramento

### Logs e Debugging
```bash
# Ver logs dos containers
docker compose logs -f unipost-streamlit
docker compose logs -f unipost-redis

# Monitorar Redis
docker compose logs -f unipost-redis-commander
```

### Métricas e Status
- Dashboard com status em tempo real
- Health checks automáticos dos containers
- Monitoramento de cache e sessões
- Interface Redis Commander para debugging

## 🔒 Segurança

- Credenciais seguras via variáveis de ambiente
- Autenticação JWT com expiração automática
- Validação de entrada em todos os formulários
- Sanitização de conteúdo gerado
- Execução em container não-root
- Health checks para monitoramento

## 🚀 Deployment

### Produção
```bash
# Executar em produção
docker compose up -d

# Monitorar logs
docker compose logs -f
```

### Execução Local (Desenvolvimento)
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
streamlit run app.py --server.port=8555
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Padrões de Código

- **Arquitetura**: Clean Code com separação de responsabilidades
- **Documentação**: Docstrings detalhados em português
- **Nomenclatura**: PascalCase para classes, snake_case para funções
- **Tipagem**: Type hints com MyPy para validação
- **Qualidade**: Flake8, Autopep8 e PEP 8 compliance
- **Temas**: CSS modular com variáveis CSS para fácil manutenção

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🛠️ Desenvolvimento

### Executar Testes
```bash
# Linting
flake8 .

# Type checking
mypy .

# Auto-formatting
autopep8 --in-place --recursive .
```

### Estrutura de Temas
- `static/styles.css`: Tema claro
- `static/styles-dark.css`: Tema escuro
- `.streamlit/config.toml`: Configurações base

## 🆘 Suporte

Para questões e suporte:
1. Verifique os logs dos containers: `docker compose logs`
2. Acesse Redis Commander em http://localhost:8081
3. Consulte a documentação da API Django
4. Entre em contato com a equipe de desenvolvimento

---

**UniPOST** - Desenvolvido com ❤️ para geração inteligente de conteúdo