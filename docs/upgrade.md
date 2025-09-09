# Log de upgrade

Este é um pedido de upgrade, vou detalha-lo para que possa entender mais precisamente o que quero.

---

Faça uma varredura do projeto e verifique se ainda há algo a implementar, algo marcado como TODO.
Se houver, implemente ou corrija o que estiver pendente.

Remova do docker compose o Elastic Search local, adaptando o código para refletir as configurações que coloquei no arquivo .env, que agora armazena dados de um Elastic Search externo.

Se ainda houver alguma menção a variável de ambiente DJANGO_API_TOKEN, remova-a e adapte o código que a use para usar os dados obtidos a partir da url de autorização.

Se não houver uso da variável de ambiente SECRET_KEY, remova-a e adate/corrija o código onde ela é mencionada.

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
