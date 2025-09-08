# Docker Setup - UniPost

## Configuração Completa do Ambiente

Este setup inclui:
- **Elasticsearch 8.11.0** com dados de exemplo populados
- **Kibana** para visualização dos dados
- **Redis** para cache
- **Aplicação Streamlit**

## Como executar

1. **Subir todos os serviços:**
   ```bash
   docker-compose up -d
   ```

2. **Verificar se os serviços estão funcionando:**
   ```bash
   docker-compose ps
   ```

## Acessos

- **Aplicação:** http://localhost:8501
- **Elasticsearch:** http://localhost:9200
- **Kibana:** http://localhost:5601
- **Redis Commander:** http://localhost:8081

## Credenciais

- **Elasticsearch:**
  - Usuario: `elastic`
  - Senha: `unipost_elastic_2024`

## Dados Pré-populados

O Elasticsearch será inicializado automaticamente com:
- Índice `unipost_content` configurado
- 5 documentos de exemplo sobre marketing digital
- Mapeamento otimizado para busca em português

## Troubleshooting

Se o Elasticsearch não inicializar corretamente:

1. Verificar logs:
   ```bash
   docker logs unipost-elasticsearch
   ```

2. Reiniciar apenas o Elasticsearch:
   ```bash
   docker-compose restart elasticsearch
   ```

3. Verificar se o índice foi criado:
   ```bash
   curl -u elastic:unipost_elastic_2024 http://localhost:9200/unipost_content/_count
   ```