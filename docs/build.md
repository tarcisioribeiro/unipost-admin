# Proposta de Geração e Aprovação de Texto - UniPOST

Esta proposta detalha a arquitetura e os requisitos para o desenvolvimento de uma aplicação de geração de texto, chamada UniPOST. O objetivo é criar um sistema robusto e modular, dividido entre uma API de backend, uma interface de frontend e um ambiente de desenvolvimento containerizado, com um fluxo de trabalho claro para a geração e gestão de conteúdo.

---

## 1. Requisitos do Backend (API Django)

* O backend será construído com Django e usará JSON Web Tokens (JWT) para a autenticação, localizada em pt_BR.

---

### 1.1. Modelos de Dados
    

* Serão implementados os seguintes modelos:


    #### User

    Gerenciado pelo sistema de autenticação padrão do Django.

    Deverá haver um grupo de permissões **Visitors** que terá acesso de visualização a todos os textos, mas não poderá gerar ou aprovar novos textos.

    Outro grupo, chamado **Members**, terá por padrão todas as permissões, exceto exclusão de registros.

    #### Text:

    * Modelo para registro e atualização de textos gerados.

        ```python
        id: Gerado automaticamente pelo Django.
        description: Texto de entrada fornecido pelo usuário via Streamlit.
        text_content: Campo de texto longo para armazenar o conteúdo gerado.
        created_by: Chave estrangeira para o User que criou o texto.
        created_at: Campo de data e hora preenchido automaticamente ao criar o texto.
        is_approved: Campo booleano para indicar o status de aprovação.
        ```
    
    #### Statistics:

    * Modelo para rastrear e registrar métricas da aplicação.

        ```python
        approved_texts: Total de textos aprovados.
        denied_texts: Total de textos negados.
        generated_texts: Total de textos gerados.
        ```

---

### 1.2. Funcionalidade de Webhook

A API deve expor um endpoint de webhook que reaja a um sinal externo para atualizar o status de aprovação de um texto. Este endpoint deve receber o id do texto e um status (True para aprovado, False para negado/regerado) e atualizar o campo is_approved no modelo Text correspondente.

---

### 2. Requisitos do Frontend (Interface Streamlit)

A interface do usuário será desenvolvida com **Streamlit**, utilizando CSS customizado para um design moderno e padronizado (UI/UX).


### 2.1. Páginas da Aplicação

A aplicação terá uma barra lateral (sidebar) com o seguinte menu de navegação para diferentes telas, com toda a localização (datas, valores númericos e textos) em pt_BR.

---

#### Tela de Login

Apresentará campos para usuário e senha.
Validará as credenciais de acesso contra a API Django para autenticar o usuário.
Dashboard (Página Inicial):
Exibirá gráficos de métricas.

Serão mostradas métricas sobre:

* Vetores armazenados no banco de dados Postgres vetorizado.
* Contagem de textos aprovados e negados.
* Número total de gerações de texto realizadas.

---

#### Geração de Textos

* Permitirá ao usuário criar novos textos.
* Incluirá opções para seleção de modelo e um campo de entrada de texto (input) para o tema.
* Um botão "Gerar" iniciará o processo de busca e criação de texto.
* Após a geração, botões de "Aprovar", "Gerar Novamente" e "Negar" serão exibidos.
* O botão "Aprovar" acionará o webhook do backend para definir o status como True.
* Os botões "Gerar Novamente" e "Negar" acionarão o webhook para definir o status como False.

---

#### Visualização de Textos

* Renderizará os textos gerados em um formato de 5 colunas por linha.
* Contará com filtros para visualizar textos por status: negados, pendentes (não aprovados) e aprovados.

---

## 3. Arquitetura e Fluxo de Trabalho

A aplicação terá uma arquitetura de microsserviços com bancos de dados dedicados para diferentes propósitos.

* Banco de dados Principal (Postgres): Armazenará os dados da API Django (User, Text, Statistics).
* Banco de dados Vetorizado (Postgres): Armazenará exclusivamente os vetores de texto.
* Redis: Atuará como um cache de alta velocidade para os resultados da busca.
* Elasticsearch: Servirá como motor de busca principal, trazendo ao contexto, vetores armazenados sobre reuniões, treinamentos, etc.

---

### 3.1. Fluxo de Geração de Texto

* O usuário insere um tema na interface Streamlit;
* A interface une o tema e um contexto relevante para a busca;
* Essa busca é enviada ao Elasticsearch;
* Se não houver resultados, a geração é interrompida;
* Se a busca for bem-sucedida, os dados são armazenados no Redis para evitar sobrecarga em futuras consultas;
* O texto é gerado e exibido na tela.

---

3.2. Fluxo de Aprovação de Texto

* O usuário clica no botão "Aprovar" na interface Streamlit;
* O sistema aciona o webhook no backend, atualizando o status do texto para is_approved = **True**.
* Em seguida, o texto aprovado é vetorizado e registrado no banco de dados Postgres com extensão para vetores.

---

## 4. Ambiente de Desenvolvimento (Docker)

O ambiente será gerenciado por Docker Compose, contendo os seguintes serviços:

* unipost-app: Contêineres da aplicação Django e Streamlit.
* unipost-db: Banco de dados para a API Django.
* unipost-vector: Banco de dados para os vetores de texto.
* redis: Servidor de cache Redis.
* elasticsearch: Motor de busca sem app no docker compose, apenas configurado no código, chamando via ambiente de variável o acesso ao motor ES externo.
* kibana: Interface de visualização para o Elasticsearch.
* pgadmin: Interface de administração para os bancos de dados Postgres.
* redis-commander: Interface para acessar o Redis (se possível).

### 4.1 Segurança do ambiente

Nenhum dado deve ser exposto, com todos os dados sensíveis sendo armazenados via arquivo de variáveis de ambiente (.env).

O comando para reconstruir o ambiente será:

```bash
docker compose down -v && docker compose up --build -d
```

---

## 5. Padrões de Codificação e Documentação


Para garantir a qualidade do código, as seguintes práticas devem ser seguidas:

* Ambiente Virtual: Sempre ativar o ambiente virtual (venv) antes de trabalhar.
* Padrão de código: POO (Programação orientada a objetos) e Clean Code.
* Documentação: Todos os módulos, classes e funções devem ser documentados de forma clara, utilizando o formato NumPy docstrings.
* Nomenclatura:

    - Classes devem usar CamelCase.
    - Funções e variáveis devem usar snake_case.
    - Todas as nomenclaturas (classes, funções, variáveis) devem estar em inglês.

* Tipagem: Usar MyPy para garantir a tipagem correta das variáveis.

Qualidade do Código:

Executar flake8 para verificar problemas de sintaxe e estilo.

Seguir estritamente a PEP 8, usando autopep8 para formatação automática.