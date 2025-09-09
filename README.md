# 📝 UniPost - Sistema de Geração de Posts com IA

Sistema inteligente para geração automática de posts para redes sociais utilizando Inteligência Artificial, com interface moderna em Streamlit, autenticação segura e sistema de temas claro/escuro.

## 🚀 Características Principais

- **🤖 Geração de Posts IA**: Criação de conteúdo para múltiplas plataformas sociais
- **🔐 Autenticação Segura**: Sistema de login com sessão persistente
- **🎨 Temas Dinâmicos**: Interface com temas claro e escuro
- **⚙️ Configurações Avançadas**: Painel completo de configurações do sistema
- **📊 Dashboard Interativo**: Visão geral com métricas e status dos serviços
- **💾 Cache Inteligente**: Sistema de cache Redis para otimização
- **🔄 Sistema de Aprovação**: Workflow para aprovar/rejeitar posts gerados

## 🏗️ Arquitetura

```
├── app.py                 # Ponto de entrada da aplicação
├── components/           # Componentes reutilizáveis
│   ├── auth_components.py    # Login e autenticação
│   └── text_components.py    # Geração e exibição de texto
├── pages/                # Páginas da aplicação
│   ├── dashboard.py          # Dashboard principal
│   ├── post_generator.py     # Geração de posts
│   ├── posts_viewer.py       # Visualização de posts
│   └── settings.py           # Configurações do sistema
├── services/             # Serviços de integração
│   ├── auth_service.py       # Autenticação e JWT
│   ├── text_generation_service.py  # IA para geração
│   ├── redis_service.py      # Cache Redis
│   └── elasticsearch_service.py    # Busca contextual
├── utils/                # Utilitários e validadores
├── config/               # Configurações da aplicação
├── static/               # CSS customizado para temas
├── .streamlit/           # Configurações do Streamlit
├── docker-compose.yml    # Orquestração de containers
├── Dockerfile           # Container da aplicação
└── requirements.txt     # Dependências Python
```

## 🛠️ Tecnologias Utilizadas

- **Frontend**: Streamlit 1.49.1 com interface responsiva
- **Backend**: Django API (externo) via JWT
- **IA/ML**: OpenAI GPT, SentenceTransformers, HuggingFace
- **Cache**: Redis 7-alpine para alta performance
- **Busca**: Elasticsearch (opcional)
- **Containerização**: Docker & Docker Compose
- **Estilização**: CSS customizado com temas claro/escuro
- **Desenvolvimento**: MyPy, Flake8, Autopep8

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

## 📱 Funcionalidades

### 🔐 Autenticação
- Login seguro com usuário e senha
- Validação via API Django com JWT
- Gerenciamento de sessão persistente
- Logout seguro com limpeza de dados

### 📊 Dashboard
- Visão geral do sistema com métricas
- Status dos serviços em tempo real
- Informações do sistema e versão
- Ações rápidas de navegação

### 🎯 Geração de Posts
- Interface intuitiva para criação de conteúdo
- Suporte a múltiplas plataformas (Facebook, Instagram, TikTok, LinkedIn)
- Integração com OpenAI GPT para IA avançada
- Visualização em tempo real do conteúdo gerado

### 📚 Visualização de Posts
- Grid responsivo para exibição de posts
- Filtros por status e plataforma
- Sistema de aprovação/rejeição
- Busca e organização de conteúdo

### ⚙️ Configurações Avançadas
- **Temas**: Alternância entre claro e escuro
- **Preferências**: Auto-refresh, itens por página
- **Sistema**: Debug mode, timeout de API
- **Cache**: Gerenciamento e limpeza
- **Sessão**: Reinicialização e exportação de configs

## 🏠 Estrutura das Páginas

### Dashboard Principal (`dashboard.py`)
- Métricas do sistema e estatísticas
- Status dos serviços (Redis, API, Streamlit)
- Informações de versão e cache
- Navegação rápida entre funcionalidades

### Geração de Posts (`post_generator.py`)
- Formulário para criação de posts
- Seleção de plataformas sociais
- Configuração de parâmetros de IA
- Aprovação/rejeição de conteúdo gerado

### Visualização de Posts (`posts_viewer.py`)
- Grid de 5 colunas responsivo
- Filtros por status e palavra-chave
- Ações em lote para posts
- Histórico completo de posts

### Configurações (`settings.py`)
- **Temas**: Claro/escuro com preview
- **Preferências**: Configurações de usuário
- **Sistema**: Informações e monitoramento
- **Avançadas**: Debug, timeout, ações de sistema

## 🔧 Configuração de Desenvolvimento

### Estrutura de Serviços

```python
# Principais serviços implementados
- AuthService: Autenticação JWT com Django API
- TextGenerationService: Geração de IA com OpenAI/local
- RedisService: Cache de alta performance
- ElasticsearchService: Busca contextual (opcional)
```

### Componentes Principais

```python
# Componentes de UI implementados
- AuthStateManager: Gerenciamento de sessão
- LoginForm: Formulário de autenticação
- TextGenerator: Interface de geração
- PostsViewer: Visualizador de posts

# Validadores disponíveis
- validate_topic: Validação de temas
- validate_credentials: Credenciais de usuário
- validate_content: Conteúdo gerado
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