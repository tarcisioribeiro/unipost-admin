import requests
from dictionary.vars import API_BASE_URL


class TextsRequest:
    """
    Classe responsável pelas requisições referentes aos textos.
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
            A lista de permissões do usuário para a aplicação de textos.
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
        Consulta e retorna os dados dos textos registrados.

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
        Consulta e retorna os dados do texto selecionado.

        Parameters
        ----------
        token : str
            Token utilizado na requisição de consulta.
        text_id : int
            Número identificador do texto.

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
        Envia e cria o texto por meio da requisição.

        Parameters
        ----------
        token : str
            Token utilizado para o envio da requisição.
        text_data: dict
            Dicionário com os dados do texto.

        Returns
        -------
        response : dict
            Dicionário com a resposta da requisição e ID do texto criado.
        """
        result = {
            "success": False,
            "message": "",
            "text_id": None
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                f"{API_BASE_URL}/texts/",
                headers=headers,
                json=text_data,
                timeout=30
            )

            if response.status_code == 201:
                response_data = response.json()
                result["success"] = True
                result["message"] = "✅ Texto registrado com sucesso!"
                result["text_id"] = response_data.get("id")
            else:
                # Log detalhado do erro
                error_detail = ""
                try:
                    error_data = response.json()
                    error_detail = str(error_data)
                except Exception:
                    error_detail = response.text

                result["message"] = (
                    f"Erro ao registrar texto na API. "
                    f"Status: {response.status_code}. "
                    f"Detalhes: {error_detail}"
                )

        except requests.exceptions.RequestException as e:
            result["message"] = f"Erro de conexão com a API: {str(e)}"

        return result

    def update_text(self, token, text_id, updated_data):
        """
        Faz a atualização do texto com base no identificador, token e dados.

        Parameters
        ----------
        token : str
            Token utilizado para o envio da requisição.
        text_id: int
            Número de identificação do texto.
        updated_data : dict
            Os novos dados do texto.

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
            return_text = ":white_check_mark: Texto atualizado."
        elif response.status_code == 400:
            return_text = "Dados inválidos para atualização."
        elif response.status_code == 404:
            return_text = "Texto não encontrado."
        else:
            return_text = "Erro desconhecido."

        return return_text

    def delete_text(self, token, text_id):
        """
        Faz a exclusão do texto com base no identificador e token.

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
        returned_text = None

        headers = {"Authorization": f"Bearer {token}"}

        response = requests.delete(
            f"{API_BASE_URL}/texts/{text_id}/",
            headers=headers
        )

        if response.status_code == 204:
            returned_text = """:white_check_mark: Texto excluído."""
        else:
            returned_text = response

        return returned_text

    def approve_text(self, token, text_id):
        """
        Aprova um texto específico (mantido para compatibilidade).
        Agora usa o webhook interno.

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
        # Usar webhook para aprovação
        approval_result = self.approve_text_via_webhook(text_id)
        return approval_result["message"]

    def approve_text_via_webhook(self, text_id):
        """
        Aprova um texto específico via webhook (sem autenticação).

        Parameters
        ----------
        text_id: int
            Número de identificação do texto.

        Returns
        -------
        response : dict
            Dicionário com resultado da operação.
        """
        result = {
            "success": False,
            "message": ""
        }

        headers = {
            "Content-Type": "application/json"
        }

        # Usar webhook de aprovação (sem autenticação)
        webhook_data = {
            "id": text_id,
            "status": True
        }

        try:
            response = requests.post(
                f"{API_BASE_URL}/webhook/approval/",
                headers=headers,
                json=webhook_data,
                timeout=30
            )

            if response.status_code == 200:
                result["success"] = True
                result["message"] = "✅ Texto aprovado com sucesso!"
            elif response.status_code == 400:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("error", "Dados inválidos")
                result["message"] = f"❌ Erro na aprovação: {error_msg}"
            else:
                result[
                    "message"
                ] = f"""❌ Erro na aprovação. Status: {response.status_code}"""

        except requests.exceptions.RequestException as e:
            result["message"] = f"❌ Erro de conexão: {str(e)}"

        return result

    def generate_embedding(self, token, text_content, text_theme):
        """
        Gera embedding para um texto aprovado.

        Parameters
        ----------
        token : str
            Token utilizado para autenticação.
        text_content : str
            Conteúdo do texto.
        text_theme : str
            Tema do texto.

        Returns
        -------
        response : dict
            Dicionário com resultado da operação.
        """
        result = {
            "success": False,
            "message": ""
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Dados para criação do embedding
        embedding_data = {
            "origin": "generated",
            "content": text_content,
            "title": text_theme,
            "metadata": {
                "source": "unipost_approved_text",
                "type": "generated_post"
            }
        }

        try:
            response = requests.post(
                f"{API_BASE_URL}/embeddings/",
                headers=headers,
                json=embedding_data,
                timeout=30
            )

            if response.status_code == 201:
                result["success"] = True
                result["message"] = "✅ Embedding gerado com sucesso!"
            else:
                result[
                    "message"
                ] = f"""❌ Erro na geração do embedding. Status: {
                    response.status_code
                }"""

        except requests.exceptions.RequestException as e:
            result["message"] = f"❌ Erro de conexão: {str(e)}"

        return result

    def approve_and_generate_embedding(
        self,
        token,
        text_id,
        text_content,
        text_theme
    ):
        """
        Aprova um texto e gera seu embedding em sequência.

        Parameters
        ----------
        token : str
            Token utilizado para autenticação.
        text_id: int
            Número de identificação do texto.
        text_content : str
            Conteúdo do texto.
        text_theme : str
            Tema do texto.

        Returns
        -------
        response : str
            Mensagem de resultado da operação.
        """
        # Primeiro aprova o texto via webhook
        approval_result = self.approve_text_via_webhook(text_id)

        if not approval_result["success"]:
            return approval_result["message"]

        # Depois gera o embedding
        embedding_result = self.generate_embedding(
            token,
            text_content,
            text_theme
        )

        if embedding_result["success"]:
            return "✅ Texto aprovado e embedding gerado com sucesso!"
        else:
            return f"""✅ Texto aprovado, mas erro no embedding: {
                embedding_result['message']
            }"""

    def reject_text_via_webhook(self, text_id):
        """
        Reprova um texto específico via webhook (sem autenticação).

        Parameters
        ----------
        text_id: int
            Número de identificação do texto.

        Returns
        -------
        response : str
            A resposta da requisição.
        """
        headers = {
            "Content-Type": "application/json"
        }

        # Usar webhook de aprovação com status False para reprovar
        webhook_data = {
            "id": text_id,
            "status": False
        }

        try:
            response = requests.post(
                f"{API_BASE_URL}/webhook/approval/",
                headers=headers,
                json=webhook_data,
                timeout=30
            )

            if response.status_code == 200:
                return "❌ Texto reprovado com sucesso!"
            elif response.status_code == 400:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("error", "Dados inválidos")
                return f"❌ Erro na reprovação: {error_msg}"
            else:
                return f"❌ Erro na reprovação. Status: {response.status_code}"

        except requests.exceptions.RequestException as e:
            return f"❌ Erro de conexão: {str(e)}"

    def reject_text(self, token, text_id):
        """
        Reprova um texto específico (mantido para compatibilidade).
        Agora usa o webhook interno.

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
        # Usar webhook para reprovação
        return self.reject_text_via_webhook(text_id)
