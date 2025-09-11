import streamlit as st
import requests
from dictionary.vars import API_BASE_URL


class Token:
    """
    Classe com métodos referentes as permissões e logout do usuário.
    """

    def logout(self, token):
        """
        Realiza o logout da aplicação.

        Parameters
        ----------
        token : str
            Token utilizado para acesso.

        Returns
        -------
        response : int
            Código de retorno da requisição de logout.
        """
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f'{API_BASE_URL}/authentication/logout/',
            headers=headers
        )
        return response.status_code == 200

    def get_user_permissions(self, token):
        """
        Obtém as permissões do usuário.

        Parameters
        ----------
        token : str
            Token utilizado para acesso.

        Returns
        -------
        response : int
            Código de retorno da requisição de consulta.
        """
        headers = {"Authorization": f"Bearer {token}"}
        url = f'{API_BASE_URL}/user/permissions/'

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            st.toast(f"Erro ao buscar permissões: {e}", icon="❌")
            return None
