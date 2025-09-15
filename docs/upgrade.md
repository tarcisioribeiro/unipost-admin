# Log de upgrade

Este é um pedido de upgrade, vou detalha-lo para que possa entender mais precisamente o que quero.

---

Preciso que melhore as tabelas de estatísticas que estão na sessão dashboard, pois algumas colunas estão sem tradução.

Esta é a imagem que reporta o problema:

file:///home/tarcisio/Pictures/Screenshots/Screenshot_2025-09-12-16-13-27.png

---

## Pós upgrade

Após isso:

  * Ative o venv, e execute o comando abaixo para detectar problemas de sintaxe:

        flake8 --exclude venv > flake_errors.txt

  * Leia o conteúdo do arquivo flake_errors.txt, e aplique as correções pedidas pelo flake8 pelo autopep8.

  * Caso não haja como corrigir com o autopep8, encontre outra forma de corrigir.

  * Em seguida, faça uma varredura do arquivo com o mypy, para verificar se a tipagem está adequada.

  * Rode o comando flake acima novamente, para garantir que não há sintaxe ruim.

  * Refaça o container, com o comando:

      `docker compose up --build -d`
