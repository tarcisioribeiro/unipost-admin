# Docker Setup - UniPost

## Configuração Completa do Ambiente

Este setup inclui:
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

- **Aplicação:** http://127.0.0.1:8555
- **Redis Commander:** http://127.0.0.1:8081