# Log de erro

Este é um report de erro, vou detalha-lo para que possa entender mais precisamente o que está errado.

## Erro(s):

**Obs.**: Vou listar pela ordem de prioridade.

---

ImportError: cannot import name 'cached_download' from 'huggingface_hub' (/usr/local/lib/python3.11/site-packages/huggingface_hub/__init__.py)
Traceback:
File "/usr/local/lib/python3.11/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 534, in _run_script
    exec(code, module.__dict__)
File "/app/app.py", line 8, in <module>
    from src.core.text_processor import TextProcessor
File "/app/src/core/text_processor.py", line 9, in <module>
    from sentence_transformers import SentenceTransformer
File "/usr/local/lib/python3.11/site-packages/sentence_transformers/__init__.py", line 3, in <module>
    from .datasets import SentencesDataset, ParallelSentencesDataset
File "/usr/local/lib/python3.11/site-packages/sentence_transformers/datasets/__init__.py", line 3, in <module>
    from .ParallelSentencesDataset import ParallelSentencesDataset
File "/usr/local/lib/python3.11/site-packages/sentence_transformers/datasets/ParallelSentencesDataset.py", line 4, in <module>
    from .. import SentenceTransformer
File "/usr/local/lib/python3.11/site-packages/sentence_transformers/SentenceTransformer.py", line 12, in <module>
    from huggingface_hub import HfApi, HfFolder, Repository, hf_hub_url, cached_

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