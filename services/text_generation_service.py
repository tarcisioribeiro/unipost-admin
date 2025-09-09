import requests
import openai
import os
from sentence_transformers import SentenceTransformer
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dictionary.vars import API_BASE_URL, PLATFORMS
from dotenv import load_dotenv
import logging
import numpy as np

load_dotenv()

logger = logging.getLogger(__name__)


class TextGenerationService:
    """
    Serviço para geração de texto usando SentenceTransformers e LLM.
    Responsável pela vetorização, busca de similaridade e geração de texto.
    """

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Inicializa o modelo SentenceTransformers e configura OpenAI.

        Parameters
        ----------
        model_name : str
            Nome do modelo SentenceTransformers
        """
        try:
            self.model: Optional[SentenceTransformer] = (
                SentenceTransformer(model_name)
            )
            logger.info(f"SentenceTransformer model loaded: {model_name}")
        except Exception as e:
            logger.error(f"Error loading SentenceTransformer model: {e}")
            self.model = None

        # Configuração OpenAI
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.default_model = os.getenv('DEFAULT_MODEL', 'gpt-4o-mini')
        self.max_tokens = int(os.getenv('MAX_TOKENS', '1000'))
        self.temperature = float(os.getenv('TEMPERATURE', '0.1'))

        if self.openai_api_key:
            self.openai_client: Optional[openai.OpenAI] = (
                openai.OpenAI(api_key=self.openai_api_key)
            )
            logger.info("OpenAI API configured successfully")
        else:
            self.openai_client = None
            logger.warning("OpenAI API key not found in environment variables")

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

    def get_platform_context(self, platform: str) -> str:
        """
        Obtém o contexto específico para uma plataforma.

        Parameters
        ----------
        platform : str
            Código da plataforma (FCB, TTK, INT, LKN)

        Returns
        -------
        str
            Contexto específico da plataforma
        """
        platform_contexts = {
            "FCB": (
                "Para Facebook: Crie conteúdo envolvente que gere interação "
                "e compartilhamentos. Use uma linguagem acessível, "
                "inclua call-to-actions e considere o uso de hashtags "
                "relevantes. "
                "O texto deve ser informativo mas também conversacional, "
                "adequado para o feed de notícias."
            ),
            "TTK": (
                "Para TikTok: Desenvolva conteúdo dinâmico e conciso que "
                "capture a atenção rapidamente. Use linguagem jovem e atual, "
                "focando em tendências e elementos visuais. O texto deve ser "
                "curto, impactante e adequado para vídeos de formato vertical."
            ),
            "INT": (
                "Para Instagram: Crie conteúdo visualmente atrativo e "
                "inspiracional. Use linguagem criativa, inclua hashtags "
                "estratégicas e considere o aspecto estético. O texto deve "
                "complementar imagens e stories, sendo conciso mas impactante."
            ),
            "LKN": (
                "Para LinkedIn: Desenvolva conteúdo profissional e educativo "
                "que agregue valor à rede de contatos. Use linguagem formal "
                "mas acessível, inclua insights relevantes e mantenha um tom "
                "respeitoso e construtivo adequado ao ambiente corporativo."
            )
        }
        return platform_contexts.get(
            platform, "Contexto genérico para redes sociais.")

    def create_prompt_context(
            self,
            user_topic: str,
            similar_texts: List[Tuple[str, float]],
            platform: str = "",
            tone: str = "profissional",
            creativity_level: str = "equilibrado",
            length: str = "Médio (300-500 palavras)"
    ) -> str:
        """
        Elaboração do contexto de prompt com novos parâmetros.

        Parameters
        ----------
        user_topic : str
            Tema proposto pelo usuário
        similar_texts : List[Tuple[str, float]]
            Textos similares com scores
        platform : str
            Plataforma de destino (opcional)
        tone : str
            Tom da linguagem
        creativity_level : str
            Nível de criatividade
        length : str
            Tamanho desejado do texto

        Returns
        -------
        str
            Contexto completo para o prompt
        """
        # Extrair o número específico de palavras do parâmetro length
        word_count = self.extract_word_count(length)

        context_parts = [
            f"TEMA: {user_topic}\n\n"
        ]

        # Instruções OBRIGATÓRIAS sobre tamanho (sempre no início)
        context_parts.append(
            f"INSTRUÇÃO OBRIGATÓRIA DE TAMANHO:\n"
            f"Você DEVE escrever EXATAMENTE {word_count} palavras. "
            f"Não mais, não menos. Este é um requisito RIGOROSO.\n"
            f"Conte as palavras conforme escreve e ajuste para atingir "
            f"precisamente {word_count} palavras.\n\n"
        )

        # Parâmetros de estilo
        context_parts.append(
            f"PARÂMETROS DE ESTILO:\n"
            f"• Tom: {tone}\n"
            f"• Criatividade: {creativity_level}\n"
        )

        # Contexto da plataforma (reescrito para ser mais direto)
        if platform and platform in PLATFORMS:
            platform_name = PLATFORMS[platform]
            platform_context = self.get_platform_context_optimized(platform)
            context_parts.append(
                f"• Plataforma: {platform_name}\n"
                f"• Adaptação: {platform_context}\n"
            )

        context_parts.append("\n")

        # Referências (limitadas para não confundir o foco no tamanho)
        if similar_texts:
            context_parts.append("REFERÊNCIAS (use como inspiração):\n")
            # Limitar a 2 referências para não sobrecarregar
            for i, (text, score) in enumerate(similar_texts[:2], 1):
                # Truncar referências muito longas
                ref_text = text[:200] + "..." if len(text) > 200 else text
                context_parts.append(f"• Ref {i}: {ref_text}\n")
        else:
            context_parts.append(
                "REFERÊNCIAS: Nenhuma encontrada. Baseie-se apenas no tema.\n"
            )

        # Instruções finais REFORÇADAS
        context_parts.append(
            f"\nINSTRUÇÃO FINAL:\n"
            f"Crie um texto sobre '{user_topic}' com EXATAMENTE {word_count} "
            f"palavras. Use tom {tone} e nível {creativity_level}. "
            f"CRÍTICO: O texto deve ter precisamente {word_count} palavras. "
            f"Verifique a contagem antes de finalizar."
        )

        if platform:
            platform_name = PLATFORMS.get(platform, platform)
            context_parts.append(
                f" Otimize para {platform_name}."
            )

        context_parts.append(
            f"\n\nLEMBRETE: {word_count} palavras é OBRIGATÓRIO!"
        )

        return "".join(context_parts)

    def extract_word_count(self, length: str) -> int:
        """
        Extrai o número de palavras do parâmetro de tamanho.

        Parameters
        ----------
        length : str
            String de tamanho (ex: "Exato (300 palavras)"
            ou "Curto (100-200 palavras)")

        Returns
        -------
        int
            Número de palavras alvo
        """
        import re

        # Primeiro, tentar extrair de formato "Exato (X palavras)"
        if "Exato" in length:
            match = re.search(r'Exato \((\d+) palavras\)', length)
            if match:
                return int(match.group(1))

        # Mapear opções legadas para números específicos
        length_mapping = {
            "Curto (100-200 palavras)": 150,  # Meio termo entre 100-200
            "Médio (300-500 palavras)": 400,  # Meio termo entre 300-500
            "Longo (500+ palavras)": 600      # Target para textos longos
        }

        # Retornar valor mapeado ou tentar extrair número
        if length in length_mapping:
            return length_mapping[length]

        # Tentar extrair número da string usando regex
        numbers = re.findall(r'\d+', length)
        if numbers:
            # Se há range (ex: 100-200), usar o meio termo
            if len(numbers) >= 2:
                return (int(numbers[0]) + int(numbers[1])) // 2
            else:
                return int(numbers[0])

        # Fallback: médio
        return 300

    def get_platform_context_optimized(self, platform: str) -> str:
        """
        Contexto otimizado e conciso por plataforma (reescrito).

        Parameters
        ----------
        platform : str
            Código da plataforma

        Returns
        -------
        str
            Contexto específico otimizado
        """
        platform_contexts = {
            "FCB": "Engajamento social, linguagem acessível, call-to-actions" +
            " claros",
            "TTK": "Linguagem jovem, conteúdo dinâmico, foco na viralidade",
            "INT": "Visual atrativo, linguagem inspiracional, hashtags" +
            " estratégicas",
            "LKN": "Tom profissional, insights valiosos, networking" +
            " corporativo"
        }
        return platform_contexts.get(
            platform,
            "Linguagem adaptada para redes sociais"
        )

    def count_words(self, text: str) -> int:
        """
        Conta palavras em um texto.

        Parameters
        ----------
        text : str
            Texto para contar

        Returns
        -------
        int
            Número de palavras
        """
        if not text:
            return 0
        return len(text.split())

    def validate_word_count(
            self,
            text: str,
            target_count: int,
            tolerance: int = 10
    ) -> tuple[bool, int]:
        """
        Valida se o texto tem a quantidade de palavras esperada.

        Parameters
        ----------
        text : str
            Texto gerado
        target_count : int
            Número alvo de palavras
        tolerance : int
            Tolerância aceitável (+/-)

        Returns
        -------
        tuple[bool, int]
            (É válido, contagem atual)
        """
        actual_count = self.count_words(text)
        is_valid = abs(actual_count - target_count) <= tolerance
        return is_valid, actual_count

    def extract_word_count_from_context(self, context: str) -> int:
        """
        Extrai a contagem de palavras alvo do contexto gerado.

        Parameters
        ----------
        context : str
            Contexto do prompt

        Returns
        -------
        int
            Número alvo de palavras
        """
        import re

        # Procurar por "EXATAMENTE X palavras" no contexto
        match = re.search(r'EXATAMENTE\s+(\d+)\s+palavras', context)
        if match:
            return int(match.group(1))

        # Fallback: procurar qualquer número seguido de "palavras"
        match = re.search(r'(\d+)\s+palavras', context)
        if match:
            return int(match.group(1))

        # Fallback final
        return 400

    def clean_text_formatting(self, text: str) -> str:
        """
        Remove asteriscos e outras formatações indesejadas do texto.

        Parameters
        ----------
        text : str
            Texto com formatação

        Returns
        -------
        str
            Texto limpo sem asteriscos
        """
        if not text:
            return text

        # Remove asteriscos usados para negrito/itálico
        cleaned_text = text.replace('*', '')

        # Remove múltiplas quebras de linha consecutivas
        import re
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)

        # Remove espaços extras
        cleaned_text = re.sub(r' {2,}', ' ', cleaned_text)

        return cleaned_text.strip()

    def generate_text_via_openai(self, prompt_context: str) -> Optional[str]:
        """
        Gera texto usando a API da OpenAI.

        Parameters
        ----------
        prompt_context : str
            Contexto completo do prompt

        Returns
        -------
        Optional[str]
            Texto gerado pela OpenAI sem asteriscos
        """
        try:
            if not self.openai_client:
                logger.error("OpenAI API key not configured")
                return None

            response = self.openai_client.chat.completions.create(
                model=self.default_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Você é um assistente especializado em criação" +
                            " de conteúdo "
                            "para redes sociais com foco RIGOROSO em" +
                            " contagem de palavras. "
                            "REGRAS OBRIGATÓRIAS: "
                            "1. SEMPRE respeite o número EXATO" +
                            " de palavras solicitado "
                            "2. Conte as palavras conforme escreve "
                            "3. Não use asteriscos (*) ou formatação markdown "
                            "4. Se o texto ficar curto," +
                            " adicione mais conteúdo relevante "
                            "5. Se ficar longo, corte mantendo a essência "
                            "6. O número de palavras é CRÍTICO e não" +
                            " negociável")},
                    {
                        "role": "user",
                        "content": prompt_context}],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0)

            generated_text = response.choices[0].message.content
            if generated_text:
                generated_text = generated_text.strip()
                # Limpar formatação indesejada
                generated_text = self.clean_text_formatting(generated_text)

                # Validar contagem de palavras
                target_count = self.extract_word_count_from_context(
                    prompt_context
                )
                is_valid, actual_count = self.validate_word_count(
                    generated_text,
                    target_count,
                    tolerance=20
                )

                if not is_valid:
                    logger.warning(f"""Word count mismatch: expected {
                        target_count
                    }, got {actual_count}""")
                    # Logar mas não rejeitar - a IA fez seu melhor

                logger.info(f"""Text generated successfully via OpenAI ({
                    actual_count
                } palavras)""")
                return generated_text
            else:
                logger.error("Empty response from OpenAI")
                return None

        except Exception as e:
            logger.error(f"Error generating text via OpenAI: {e}")
            return None

    def generate_text_with_retry(
            self,
            prompt_context: str,
            max_retries: int = 2
    ) -> Optional[str]:
        """
        Gera texto com tentativas automáticas para atingir
        contagem de palavras.

        Parameters
        ----------
        prompt_context : str
            Contexto do prompt
        max_retries : int
            Número máximo de tentativas

        Returns
        -------
        Optional[str]
            Texto gerado com contagem mais precisa
        """
        target_count = self.extract_word_count_from_context(prompt_context)
        best_text = None
        best_score = float('inf')  # Diferença da contagem alvo

        for attempt in range(max_retries + 1):
            text = self.generate_text_via_openai(prompt_context)
            if not text:
                continue

            word_count = self.count_words(text)
            score = abs(word_count - target_count)

            logger.info(f"""Tentativa {
                attempt + 1
            }: {
                word_count
            } palavras (alvo: {
                target_count
            }, score: {
                score
            })""")

            # Se está dentro da tolerância aceitável, retornar imediatamente
            if score <= 15:
                logger.info(f"""Contagem aceitável alcançada na tentativa {
                    attempt + 1
                }""")
                return text

            # Salvar a melhor tentativa
            if score < best_score:
                best_score = score
                best_text = text

            # Se não é a última tentativa, ajustar o prompt
            if attempt < max_retries:
                if word_count < target_count:
                    adjustment = f"""\n\nATENÇÃO: Sua última tentativa teve {
                        word_count
                    } palavras, mas precisa de {
                        target_count
                    }. Adicione aproximadamente {
                        target_count - word_count
                    } palavras mais de conteúdo relevante."""
                else:
                    adjustment = f"""\n\nATENÇÃO: Sua última tentativa teve {
                        word_count
                    } palavras, mas precisa de {
                        target_count
                    }. Corte aproximadamente {
                        word_count - target_count
                    } palavras mantendo a essência."""

                prompt_context = prompt_context + adjustment

        logger.warning(f"""Melhor resultado após {
            max_retries + 1
        } tentativas: {
            self.count_words(best_text) if best_text else 0
        } palavras""")
        return best_text

    def generate_text_via_llm(self, prompt_context: str) -> Optional[str]:
        """
        Wrapper para geração de texto - tenta OpenAI com retry primeiro,
        fallback para API local.

        Parameters
        ----------
        prompt_context : str
            Contexto completo do prompt

        Returns
        -------
        Optional[str]
            Texto gerado pelo LLM
        """
        # Tentar OpenAI com retry para contagem de palavras
        if self.openai_client:
            openai_result = self.generate_text_with_retry(
                prompt_context,
                max_retries=1
            )
            if openai_result:
                return openai_result
            logger.warning("""OpenAI generation with retry failed,
                           trying fallback API""")

        # Fallback para API local
        try:
            response = requests.post(
                f"{API_BASE_URL}/text-generation/",
                json={
                    "prompt": prompt_context,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('generated_text', '')
                if generated_text:
                    # Aplicar limpeza de formatação também no fallback
                    generated_text = self.clean_text_formatting(generated_text)
                logger.info("Text generated successfully via fallback API")
                return generated_text
            else:
                logger.error(f"Fallback LLM API error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error generating text via fallback LLM: {e}")
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
