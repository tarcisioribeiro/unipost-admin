# Log de erro

Este é um report de erro, vou detalha-lo para que possa entender mais precisamente o que está errado.

## Erro(s):

**Obs.**: Vou listar pela ordem de prioridade.

---



---

## Pós correção

Após corrigir o problema:

  * Ative o venv, e execute o comando abaixo para detectar problemas de sintaxe:

        flake8 --exclude venv > flake_errors.txt

  * Leia o conteúdo do arquivo flake_errors.txt, e aplique as correções pedidas pelo flake8 pelo autopep8.

  * Caso não haja como corrigir com o autopep8, encontre outra forma de corrigir.

  * Em seguida, faça uma varredura do arquivo com o mypy 'nome_do_arquivo'.py, para verificar se a tipagem está adequada.

  * Rode o comando flake acima novamente, para garantir que não há sintaxe ruim.

  * Refaça o container, com o comando:

      `docker compose up --build -d`
