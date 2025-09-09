import requests
from dictionary.vars import API_BASE_URL


class TextsRequest:
    """
    Classe responsável pelas requisições referentes aos autores.
    """

    def get_text_permissions(self, user_permissions):
        """
        Consulta e retorna as permissões do usuário.

        Parameters
        ----------
        user_permissions : list
            Lista das permissões do usuário.

        Returns
        -------
        text_permissions : list
            A lista de permissões do usuário para a aplicação de autores.
        """

        text_permissions = []

        # Verificar se user_permissions não é None
        if user_permissions is None:
            return text_permissions

        if "texts.add_text" in user_permissions:
            text_permissions.append('create')
        if "texts.view_text" in user_permissions:
            text_permissions.append('read')
        if "texts.change_text" in user_permissions:
            text_permissions.append('update')
        if "texts.delete_text" in user_permissions:
            text_permissions.append('delete')

        return text_permissions

    def get_texts(self, token):
        """
        Consulta e retorna os dados dos autores registrados.

        Parameters
        ----------
        token : str
            Token utilizado na requisição de consulta.

        Returns
        -------
        texts_dataframe : Any
            O dado obtido com base na requisição.
        """
        texts_dataframe = []

        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"""{API_BASE_URL}/texts/""",
            headers=headers
        )
        if response.status_code == 200:
            texts_dataframe = response.json()
        else:
            texts_dataframe = None

        return texts_dataframe

    def get_text(self, token, text_id):
        """
        Consulta e retorna os dados do autor selecionado.

        Parameters
        ----------
        token : str
            Token utilizado na requisição de consulta.
        text_id : int
            Número identificador do autor.

        Returns
        -------
        text_data : dict
            O dicionário obtido com base na requisição.
        """
        text_data = {}

        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"""{API_BASE_URL}/texts/{text_id}/""",
            headers=headers
        )
        if response.status_code == 200:
            text_data = response.json()
        else:
            text_data = None

        return text_data

    def create_text(self, token, text_data):
        """
        Envia e cria o autor por meio da requisição.

        Parameters
        ----------
        token : str
            Token utilizado para o envio da requisição.
        text_data: str
            Dicionário com os dados do autor.

        Returns
        -------
        response : str
            A resposta da requisição.
        """
        return_text = ""

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            f"{API_BASE_URL}/texts/",
            headers=headers,
            json=text_data
        )

        if response.status_code == 201:
            return_text = ":white_check_mark: Autor registrado."
        else:
            return_text = "Este autor já foi registrado."

        return return_text

    def update_text(self, token, text_id, updated_data):
        """
        Faz a exclusão autor com base no identificador, token e novos dados.

        Parameters
        ----------
        token : str
            Token utilizado para o envio da requisição.
        text_id: int
            Número de identificação do autor.
        updated_data : dict
            Os novos dados do autor.

        Returns
        -------
        response : str
            A resposta da requisição.
        """
        return_text = ""

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.put(
            f"{API_BASE_URL}/texts/{text_id}/",
            headers=headers,
            json=updated_data
        )

        if response.status_code in [200, 204]:
            return_text = ":white_check_mark: Autor atualizado."
        elif response.status_code == 400:
            return_text = "Dados inválidos para atualização."
        elif response.status_code == 404:
            return_text = "Autor não encontrado."
        else:
            return_text = "Erro desconhecido."

        return return_text

    def delete_text(self, token, text_id):
        """
        Faz a exclusão do autor com base no identificador e token.

        Parameters
        ----------
        token : str
            Token utilizado para o envio da requisição.
        text_id: int
            Número de identificação do autor.

        Returns
        -------
        response : str
            A resposta da requisição.
        """
        returned_text = None

        headers = {"Authorization": f"Bearer {token}"}

        response = requests.delete(
            f"{API_BASE_URL}/texts/{text_id}/",
            headers=headers
        )

        if response.status_code == 204:
            returned_text = """:white_check_mark: Autor excluído."""
        else:
            returned_text = response

        return returned_text

    def approve_text(self, token, text_id):
        """
        Aprova um texto específico.

        Parameters
        ----------
        token : str
            Token utilizado para o envio da requisição.
        text_id: int
            Número de identificação do texto.

        Returns
        -------
        response : str
            A resposta da requisição.
        """
        return_text = ""

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.patch(
            f"{API_BASE_URL}/texts/{text_id}/",
            headers=headers,
            json={"is_approved": True}
        )

        if response.status_code in [200, 204]:
            return_text = "✅ Texto aprovado com sucesso!"
        elif response.status_code == 404:
            return_text = "Texto não encontrado."
        else:
            return_text = "Erro ao aprovar texto."

        return return_text

    def reject_text(self, token, text_id):
        """
        Reprova um texto específico.

        Parameters
        ----------
        token : str
            Token utilizado para o envio da requisição.
        text_id: int
            Número de identificação do texto.

        Returns
        -------
        response : str
            A resposta da requisição.
        """
        return_text = ""

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.patch(
            f"{API_BASE_URL}/texts/{text_id}/",
            headers=headers,
            json={"is_approved": False}
        )

        if response.status_code in [200, 204]:
            return_text = "❌ Texto reprovado."
        elif response.status_code == 404:
            return_text = "Texto não encontrado."
        else:
            return_text = "Erro ao reprovar texto."

        return return_text
