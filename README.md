# UniPOST - Sistema de Geração de Textos com IA

Sistema inteligente para geração automática de textos utilizando Inteligência Artificial, com integração ao Elasticsearch para busca contextual e Redis para cache de alta performance.

## 🚀 Características Principais

- **Geração de Textos IA**: Criação de conteúdo baseado em contexto relevante
- **Busca Inteligente**: Integração com Elasticsearch para contexto preciso
- **Cache Performático**: Redis para otimização de consultas
- **Interface Moderna**: Streamlit com design responsivo em português
- **Autenticação Segura**: Integração com API Django via JWT
- **Workflow de Aprovação**: Sistema de aprovação/rejeição de conteúdo

## 🏗️ Arquitetura

```
├── app/                    # Aplicação Streamlit
│   ├── components/        # Componentes reutilizáveis
│   ├── pages/            # Páginas da aplicação
│   ├── services/         # Serviços de integração
│   ├── utils/            # Utilitários e validadores
│   ├── config/           # Configurações
│   └── main.py           # Ponto de entrada
├── docker-compose.yml     # Orquestração de containers
├── Dockerfile            # Container da aplicação
└── requirements.txt      # Dependências Python
```

## 🛠️ Tecnologias Utilizadas

- **Frontend**: Streamlit (Python)
- **Backend**: Django API (externo)
- **Busca**: Elasticsearch (externo)
- **Cache**: Redis
- **Containerização**: Docker & Docker Compose
- **Monitoramento**: Kibana
- **IA/ML**: SentenceTransformers, HuggingFace

## 📋 Pré-requisitos

- Docker >= 20.0
- Docker Compose >= 2.0
- API Django configurada e rodando
- Elasticsearch cluster acessível

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
DJANGO_API_URL=http://localhost:8000
DJANGO_API_TOKEN=your_jwt_token_here

# Elasticsearch Configuration  
ELASTICSEARCH_URL=https://your-elasticsearch-host:9200
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=your_elasticsearch_password

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

- **Aplicação Principal**: http://localhost:8501
- **Redis Commander**: http://localhost:8081
- **Kibana**: http://localhost:5601

## 📱 Funcionalidades

### 🔐 Autenticação
- Login seguro via API Django
- Validação de token JWT
- Gerenciamento de sessão

### 🎯 Geração de Textos
- Interface para entrada de tema
- Seleção de modelos de IA
- Configuração de parâmetros de geração
- Busca automática de contexto no Elasticsearch

### 📚 Visualização de Textos
- Grid de 5 colunas para exibição
- Filtros por status (aprovado/pendente/negado)
- Busca por palavras-chave
- Ações de aprovação/rejeição

### 🔄 Sistema de Aprovação
- Workflow de aprovação manual
- Webhooks para atualização de status
- Integração com API Django

## 🏠 Estrutura das Páginas

### Dashboard Principal (`main.py`)
- Visão geral do sistema
- Estatísticas básicas
- Ações rápidas
- Status dos serviços

### Geração de Textos (`pages/01_🎯_Geração_de_Textos.py`)
- Formulário de geração
- Seleção de modelos
- Configurações avançadas
- Visualização do resultado

### Visualização de Textos (`pages/02_📚_Visualização_de_Textos.py`)
- Grid responsivo
- Filtros avançados
- Gerenciamento de aprovações

## 🔧 Configuração de Desenvolvimento

### Estrutura de Serviços

```python
# Principais serviços implementados
- AuthService: Autenticação JWT
- ElasticsearchService: Busca e contexto
- RedisService: Cache de resultados
- TextGenerationService: Geração de IA
```

### Validações Implementadas

```python
# Validadores disponíveis
- validate_topic: Validação de temas
- validate_model_selection: Seleção de modelos
- validate_user_credentials: Credenciais de usuário
- validate_text_content: Conteúdo gerado
```

## 📊 Monitoramento

### Logs e Debugging
```bash
# Ver logs dos containers
docker compose logs -f unipost-app
docker compose logs -f redis
```

### Métricas e Status
- Status dos serviços no dashboard
- Verificação automática de conexões
- Health checks dos containers

## 🔒 Segurança

- Todas as credenciais via variáveis de ambiente
- Validação de entrada em todos os formulários
- Sanitização de conteúdo gerado
- Tokens JWT com expiração
- Comunicação HTTPS com Elasticsearch

## 🚀 Deployment

### Produção
```bash
# Configurar variáveis de ambiente para produção
export DEBUG=False
export SECRET_KEY=your-secure-secret-key

# Executar em produção
docker compose -f docker-compose.yml up -d
```

### Escalabilidade
- Redis para cache distribuído
- Elasticsearch para busca escalável
- Containers stateless para horizontal scaling

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Padrões de Código

- **POO e Clean Code**: Orientação a objetos com código limpo
- **Documentação**: NumPy docstrings em todas as funções
- **Nomenclatura**: CamelCase para classes, snake_case para funções
- **Tipagem**: MyPy para validação de tipos
- **Qualidade**: flake8 e PEP 8 compliance

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🆘 Suporte

Para questões e suporte:
1. Abra uma issue no repositório
2. Consulte a documentação da API Django
3. Verifique os logs dos containers
4. Entre em contato com a equipe de desenvolvimento

---

**UniPOST** - Desenvolvido com ❤️ para geração inteligente de conteúdo