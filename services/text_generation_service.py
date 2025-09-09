import requests
from sentence_transformers import SentenceTransformer
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dictionary.vars import API_BASE_URL
import logging
import numpy as np

logger = logging.getLogger(__name__)


class TextGenerationService:
    """
    Serviço para geração de texto usando SentenceTransformers e LLM.
    Responsável pela vetorização, busca de similaridade e geração de texto.
    """

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Inicializa o modelo SentenceTransformers.

        Parameters
        ----------
        model_name : str
            Nome do modelo SentenceTransformers
        """
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"SentenceTransformer model loaded: {model_name}")
        except Exception as e:
            logger.error(f"Error loading SentenceTransformer model: {e}")
            self.model = None

    def treat_text_content(self, texts: List[Dict]) -> List[str]:
        """
        Realiza o tratamento dos textos das postagens em formato legível.

        Parameters
        ----------
        texts : List[Dict]
            Lista de textos obtidos do ElasticSearch

        Returns
        -------
        List[str]
            Textos tratados e formatados
        """
        treated_texts = []

        for text in texts:
            content = text.get('content', '')
            title = text.get('title', '')
            author = text.get('author', '')

            treated_content = ""
            if title:
                treated_content += f"Título: {title}\n"
            if author:
                treated_content += f"Autor: {author}\n"
            if title or author:
                treated_content += "\n"
            treated_content += content

            treated_content = treated_content.strip()

            if treated_content:
                treated_texts.append(treated_content)

        logger.info(f"Treated {len(treated_texts)} texts")
        return treated_texts

    def vectorize_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Gera vetores usando SentenceTransformers - HuggingFace.

        Parameters
        ----------
        texts : List[str]
            Lista de textos para vetorizar

        Returns
        -------
        List[List[float]]
            Lista de vetores
        """
        try:
            if not self.model:
                logger.error("SentenceTransformer model not initialized")
                return []

            vectors = self.model.encode(texts).tolist()
            logger.info(f"Generated {len(vectors)} vectors")
            return vectors

        except Exception as e:
            logger.error(f"Error vectorizing texts: {e}")
            return []

    def find_similar_vectors(
            self,
            user_input: str,
            cached_vectors: List[List[float]],
            cached_texts: List[str],
            top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Busca dos vetores que correspondam ao tema proposto pelo usuário.

        Parameters
        ----------
        user_input : str
            Input do usuário
        cached_vectors : List[List[float]]
            Vetores em cache
        cached_texts : List[str]
            Textos correspondentes
        top_k : int
            Número de resultados mais similares

        Returns
        -------
        List[Tuple[str, float]]
            Lista de (texto, score de similaridade)
        """
        try:
            if not self.model:
                return []

            user_vector = self.model.encode([user_input])[0]

            similarities = []
            for i, vector in enumerate(cached_vectors):
                similarity = self._cosine_similarity(user_vector, vector)
                similarities.append((cached_texts[i], similarity))

            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]

        except Exception as e:
            logger.error(f"Error finding similar vectors: {e}")
            return []

    def _cosine_similarity(
            self,
            vec1: List[float],
            vec2: List[float]
    ) -> float:
        """
        Calcula similaridade cosseno entre dois vetores.

        Parameters
        ----------
        vec1 : List[float]
            Primeiro vetor
        vec2 : List[float]
            Segundo vetor

        Returns
        -------
        float
            Similaridade cosseno (0-1)
        """
        vec1 = np.array(vec1)  # type: ignore
        vec2 = np.array(vec2)  # type: ignore

        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)

        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0

        return dot_product / (norm_vec1 * norm_vec2)

    def create_prompt_context(
            self,
            user_topic: str,
            similar_texts: List[Tuple[str, float]]
    ) -> str:
        """
        Elaboração do contexto de prompt, unindo referência e tema.

        Parameters
        ----------
        user_topic : str
            Tema proposto pelo usuário
        similar_texts : List[Tuple[str, float]]
            Textos similares com scores

        Returns
        -------
        str
            Contexto completo para o prompt
        """
        context_parts = [
            f"Tema solicitado: {user_topic}\n\n",
            "Referências encontradas:\n\n"
        ]

        for i, (text, score) in enumerate(similar_texts, 1):
            context_parts.append(
                f"Referência {i} (similaridade: {score:.3f}):\n{text}\n\n"
            )

        context_parts.append(
            "Instrução:\n"
            f"""Com base nas referências acima, crie um texto natural e
            coerente sobre o tema '{user_topic}'. """
            """O texto deve ser informativo, bem estruturado e incorporar
            as informações relevantes das referências. """
            "Mantenha um tom profissional e educativo."
        )

        return "".join(context_parts)

    def generate_text_via_llm(self, prompt_context: str) -> Optional[str]:
        """
        Coleta da resposta gerada pelo modelo de linguagem.

        Parameters
        ----------
        prompt_context : str
            Contexto completo do prompt

        Returns
        -------
        Optional[str]
            Texto gerado pelo LLM
        """
        try:
            response = requests.post(
                f"{API_BASE_URL}/text-generation/",
                json={
                    "prompt": prompt_context,
                    "max_tokens": 1000,
                    "temperature": 0.7
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('generated_text', '')
                logger.info("Text generated successfully")
                return generated_text
            else:
                logger.error(f"LLM API error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error generating text via LLM: {e}")
            return None

    def send_for_approval(self, generated_text: str, user_topic: str) -> bool:
        """
        Geração de envio do texto via webhook para ferramenta de aprovação.

        Parameters
        ----------
        generated_text : str
            Texto gerado
        user_topic : str
            Tópico original

        Returns
        -------
        bool
            Sucesso do envio
        """
        try:
            webhook_data = {
                "topic": user_topic,
                "generated_text": generated_text,
                "timestamp": datetime.now().isoformat(),
                "status": "pending_approval"
            }

            response = requests.post(
                f"{API_BASE_URL}/approval-webhook/",
                json=webhook_data,
                timeout=10
            )

            if response.status_code in [200, 201]:
                logger.info("Text sent for approval successfully")
                return True
            else:
                logger.error(f"Webhook error: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error sending for approval: {e}")
            return False

    def is_model_loaded(self) -> bool:
        """
        Verifica se o modelo SentenceTransformers está carregado.

        Returns
        -------
        bool
            True se carregado, False caso contrário
        """
        return self.model is not None
