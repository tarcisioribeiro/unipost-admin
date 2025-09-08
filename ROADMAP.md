# UniPOST

Aplicação de IA para geração de texto natural com base em textos extraídos do ElasticSearch,
que estará externo a este projeto.
    
    
## Primeira fase

* Realizar coleta automática de textos no ElasticSearch, que estará externo a este projeto.
    
### Tarefas:
    
    Criar um código que automatize a busca de textos no ElasticSearch;
    Tratamento do texto das postagens em formato legível;

### Tecnologias a serem utilizadas:

    Vetorização de texto: SentenceTransformers - HuggingFace

Elaborar a partir das referências obtidas dos blogs, textos em linguagem natural.
Tarefas:

    Busca dos vetores que correspondam ao tema proposto pelo usuário;
    Armazenamento em cache de vetores consultados;
    Interface para input do usuário, que permita que o usuário informe o texto proposto das postagens;
    Elaboração do contexto de prompt, unindo referência (vetores) e tema proposto (input).
    Coleta da resposta gerada pelo modelo de linguagem e geração de envio do texto via webhook para ferramenta de aprovação manual.

Tecnologias a serem utilizadas:

    Armazenamento em cache dos vetores obtidos: Redis
    Interface de input: Streamlit
    Contexto de prompt: Core do Python
    Envio da resposta gerada pelo LLM via webhook e aprovações de textos: API Django + Aproveitamento da interface Streamlit de input.