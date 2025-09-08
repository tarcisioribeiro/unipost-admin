# Log de erro

Este é um report de erro, vou detalha-lo para que possa entender mais precisamente o que está errado.

## Erro(s):

**Obs.**: Vou listar pela ordem de prioridade.

---

Erro na página de Dashboard ao clicar em gerar novo texto:

streamlit.errors.StreamlitAPIException: st.session_state.current_page cannot be modified after the widget with key current_page is instantiated.

Traceback:
File "/app/app.py", line 491, in <module>
    app.run()
File "/app/app.py", line 48, in run
    self._render_main_app()
File "/app/app.py", line 85, in _render_main_app
    self._render_dashboard()
File "/app/app.py", line 146, in _render_dashboard
    st.session_state.current_page = "Geração de Textos"
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/streamlit/runtime/metrics_util.py", line 443, in wrapped_func
    result = non_optional_func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/streamlit/runtime/state/session_state_proxy.py", line 136, in __setattr__
    self[key] = value
    ~~~~^^^^^
File "/usr/local/lib/python3.11/site-packages/streamlit/runtime/metrics_util.py", line 443, in wrapped_func
    result = non_optional_func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/streamlit/runtime/state/session_state_proxy.py", line 114, in __setitem__
    get_session_state()[key] = value
    ~~~~~~~~~~~~~~~~~~~^^^^^
File "/usr/local/lib/python3.11/site-packages/streamlit/runtime/state/safe_session_state.py", line 109, in __setitem__
    self._state[key] = value
    ~~~~~~~~~~~^^^^^
File "/usr/local/lib/python3.11/site-packages/streamlit/runtime/state/session_state.py", line 533, in __setitem__
    raise StreamlitAPIException(

Erro ao clicar em Ver Texto na página de Dashboard:

streamlit.errors.StreamlitAPIException: st.session_state.current_page cannot be modified after the widget with key current_page is instantiated.

Traceback:
File "/app/app.py", line 491, in <module>
    app.run()
File "/app/app.py", line 48, in run
    self._render_main_app()
File "/app/app.py", line 85, in _render_main_app
    self._render_dashboard()
File "/app/app.py", line 151, in _render_dashboard
    st.session_state.current_page = "Visualização de Textos"
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/streamlit/runtime/metrics_util.py", line 443, in wrapped_func
    result = non_optional_func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/streamlit/runtime/state/session_state_proxy.py", line 136, in __setattr__
    self[key] = value
    ~~~~^^^^^
File "/usr/local/lib/python3.11/site-packages/streamlit/runtime/metrics_util.py", line 443, in wrapped_func
    result = non_optional_func(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/usr/local/lib/python3.11/site-packages/streamlit/runtime/state/session_state_proxy.py", line 114, in __setitem__
    get_session_state()[key] = value
    ~~~~~~~~~~~~~~~~~~~^^^^^
File "/usr/local/lib/python3.11/site-packages/streamlit/runtime/state/safe_session_state.py", line 109, in __setitem__
    self._state[key] = value
    ~~~~~~~~~~~^^^^^
File "/usr/local/lib/python3.11/site-packages/streamlit/runtime/state/session_state.py", line 533, in __setitem__
    raise StreamlitAPIException(

Erro ao conectar ao ElasticSearch

Preciso que esse erro não aconteça, pois preciso testar a busca de vetores no ES.

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
