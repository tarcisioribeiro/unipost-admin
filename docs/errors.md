# Log de erro

Este é um report de erro, vou detalha-lo para que possa entender mais precisamente o que está errado.

## Erro(s):

**Obs.**: Vou listar pela ordem de prioridade.

---

Erro ao tentar acessar:

pydantic_core._pydantic_core.ValidationError: 3 validation errors for Settings es_host Extra inputs are not permitted [type=extra_forbidden, input_value='https://elastic:9200', input_type=str] For further information visit https://errors.pydantic.dev/2.11/v/extra_forbidden es_user Extra inputs are not permitted [type=extra_forbidden, input_value='elastic', input_type=str] For further information visit https://errors.pydantic.dev/2.11/v/extra_forbidden es_pass Extra inputs are not permitted [type=extra_forbidden, input_value='orrARDrdr27!', input_type=str] For further information visit https://errors.pydantic.dev/2.11/v/extra_forbidden
Traceback:
File "/app/app.py", line 9, in <module>
    from components.auth_components import AuthStateManager, LoginForm
File "/app/components/__init__.py", line 3, in <module>
    from .auth_components import LoginForm, AuthStateManager
File "/app/components/auth_components.py", line 11, in <module>
    from services.auth_service import AuthService
File "/app/services/__init__.py", line 3, in <module>
    from .auth_service import AuthService
File "/app/services/auth_service.py", line 14, in <module>
    from config.settings import settings
File "/app/config/__init__.py", line 3, in <module>
    from .settings import settings
File "/app/config/settings.py", line 98, in <module>
    settings = Settings()
               ^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/pydantic_settings/main.py", line 188, in __init__
    super().__init__(
File "/usr/local/lib/python3.11/site-packages/pydantic/main.py", line 253, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
