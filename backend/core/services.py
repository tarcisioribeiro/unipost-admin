import redis
import json
import logging
from typing import List, Dict, Optional, Any
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import numpy as np
from django.conf import settings
from .models import Statistics

logger = logging.getLogger(__name__)


class RedisService:
    """
    Serviço para gerenciamento de cache Redis.
    Armazena resultados de busca para evitar sobrecarga em consultas futuras.
    """
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.cache_ttl = 3600  # 1 hora
    
    def get_cached_search(self, search_query: str) -> Optional[Dict]:
        """
        Busca resultado em cache baseado na query de busca.
        
        Args:
            search_query (str): Query de busca
            
        Returns:
            Optional[Dict]: Resultado em cache ou None se não encontrado
        """
        try:
            cache_key = f"search:{hash(search_query)}"
            cached_result = self.redis_client.get(cache_key)
            
            if cached_result:
                logger.info(f"Cache hit para query: {search_query[:50]}...")
                return json.loads(cached_result)
            
            logger.info(f"Cache miss para query: {search_query[:50]}...")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar cache: {e}")
            return None
    
    def cache_search_result(self, search_query: str, result: Dict) -> bool:
        """
        Armazena resultado de busca no cache.
        
        Args:
            search_query (str): Query de busca
            result (Dict): Resultado da busca
            
        Returns:
            bool: True se armazenado com sucesso
        """
        try:
            cache_key = f"search:{hash(search_query)}"
            self.redis_client.setex(
                cache_key, 
                self.cache_ttl, 
                json.dumps(result, default=str)
            )
            logger.info(f"Resultado armazenado em cache para: {search_query[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao armazenar cache: {e}")
            return False
    
    def clear_cache(self) -> bool:
        """
        Limpa todo o cache de busca.
        
        Returns:
            bool: True se limpo com sucesso
        """
        try:
            keys = self.redis_client.keys("search:*")
            if keys:
                self.redis_client.delete(*keys)
            logger.info("Cache de busca limpo com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")
            return False


class ElasticsearchService:
    """
    Serviço para integração com Elasticsearch.
    Realiza buscas contextuais para geração de texto.
    """
    
    def __init__(self):
        self.es_client = Elasticsearch([settings.ELASTICSEARCH_URL])
        self.index_name = "unipost_context"
    
    def search_context(self, query: str, size: int = 10) -> List[Dict]:
        """
        Busca contexto relevante no Elasticsearch.
        
        Args:
            query (str): Query de busca
            size (int): Número máximo de resultados
            
        Returns:
            List[Dict]: Lista de documentos relevantes
        """
        try:
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2", "content", "description"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                },
                "highlight": {
                    "fields": {
                        "content": {"max_analyzed_offset": 1000000},
                        "title": {}
                    }
                },
                "size": size
            }
            
            response = self.es_client.search(
                index=self.index_name,
                body=search_body
            )
            
            results = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                source['score'] = hit['_score']
                
                # Adicionar highlights se disponíveis
                if 'highlight' in hit:
                    source['highlighted_content'] = hit['highlight'].get('content', [])
                    source['highlighted_title'] = hit['highlight'].get('title', [])
                
                results.append(source)
            
            logger.info(f"Elasticsearch retornou {len(results)} resultados para: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Erro na busca Elasticsearch: {e}")
            return []
    
    def index_document(self, doc_id: str, document: Dict) -> bool:
        """
        Indexa um documento no Elasticsearch.
        
        Args:
            doc_id (str): ID único do documento
            document (Dict): Dados do documento
            
        Returns:
            bool: True se indexado com sucesso
        """
        try:
            response = self.es_client.index(
                index=self.index_name,
                id=doc_id,
                body=document
            )
            
            logger.info(f"Documento {doc_id} indexado com sucesso")
            return response['result'] in ['created', 'updated']
            
        except Exception as e:
            logger.error(f"Erro ao indexar documento {doc_id}: {e}")
            return False


class TextVectorizationService:
    """
    Serviço para vetorização de textos aprovados.
    Usa SentenceTransformers para gerar embeddings.
    """
    
    def __init__(self):
        self.model_name = settings.HUGGINGFACE_MODEL
        self.model = SentenceTransformer(self.model_name)
    
    def vectorize_text(self, text: str) -> np.ndarray:
        """
        Vetoriza um texto usando SentenceTransformers.
        
        Args:
            text (str): Texto para vetorizar
            
        Returns:
            np.ndarray: Vetor representativo do texto
        """
        try:
            # Preprocessar texto (remover quebras de linha excessivas, etc.)
            cleaned_text = ' '.join(text.split())
            
            # Gerar embedding
            embedding = self.model.encode(cleaned_text)
            
            logger.info(f"Texto vetorizado: {len(embedding)} dimensões")
            return embedding
            
        except Exception as e:
            logger.error(f"Erro ao vetorizar texto: {e}")
            return np.array([])
    
    def similarity_search(self, query_text: str, stored_vectors: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Busca por similaridade usando vetores armazenados.
        
        Args:
            query_text (str): Texto de consulta
            stored_vectors (List[Dict]): Lista de vetores armazenados
            top_k (int): Número de resultados mais similares
            
        Returns:
            List[Dict]: Lista de textos mais similares
        """
        try:
            # Vetorizar query
            query_vector = self.vectorize_text(query_text)
            
            if len(query_vector) == 0:
                return []
            
            similarities = []
            
            for stored in stored_vectors:
                if 'vector' in stored and len(stored['vector']) > 0:
                    # Calcular similaridade coseno
                    similarity = np.dot(query_vector, stored['vector']) / (
                        np.linalg.norm(query_vector) * np.linalg.norm(stored['vector'])
                    )
                    
                    similarities.append({
                        **stored,
                        'similarity': float(similarity)
                    })
            
            # Ordenar por similaridade e retornar top_k
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Erro na busca por similaridade: {e}")
            return []


class TextGenerationService:
    """
    Serviço principal para geração de textos.
    Coordena a busca, cache e geração de texto.
    """
    
    def __init__(self):
        self.redis_service = RedisService()
        self.es_service = ElasticsearchService()
        self.vector_service = TextVectorizationService()
    
    def generate_text_with_context(self, theme: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
        """
        Gera texto usando contexto do Elasticsearch.
        
        Args:
            theme (str): Tema fornecido pelo usuário
            model (str): Modelo de IA a ser usado
            
        Returns:
            Dict: Resultado da geração com contexto e texto gerado
        """
        try:
            # 1. Verificar cache
            cached_result = self.redis_service.get_cached_search(theme)
            if cached_result and 'context' in cached_result:
                logger.info("Usando contexto do cache")
                context_docs = cached_result['context']
            else:
                # 2. Buscar contexto no Elasticsearch
                context_docs = self.es_service.search_context(theme)
                
                if not context_docs:
                    logger.warning(f"Nenhum contexto encontrado para: {theme}")
                    return {
                        'success': False,
                        'error': 'Nenhum contexto relevante encontrado',
                        'theme': theme
                    }
                
                # 3. Armazenar contexto no cache
                cache_data = {'context': context_docs, 'theme': theme}
                self.redis_service.cache_search_result(theme, cache_data)
            
            # 4. Preparar contexto para o prompt
            context_text = self._prepare_context_for_prompt(context_docs)
            
            # 5. Gerar texto usando modelo de IA (simulado por agora)
            generated_text = self._generate_text_with_model(theme, context_text, model)
            
            # 6. Atualizar estatísticas
            stats = Statistics.get_instance()
            stats.increment_generated()
            
            return {
                'success': True,
                'generated_text': generated_text,
                'context_used': len(context_docs),
                'theme': theme,
                'model_used': model
            }
            
        except Exception as e:
            logger.error(f"Erro na geração de texto: {e}")
            return {
                'success': False,
                'error': str(e),
                'theme': theme
            }
    
    def _prepare_context_for_prompt(self, context_docs: List[Dict]) -> str:
        """
        Prepara o contexto dos documentos encontrados para o prompt.
        
        Args:
            context_docs (List[Dict]): Documentos de contexto
            
        Returns:
            str: Contexto formatado para o prompt
        """
        context_parts = []
        
        for doc in context_docs[:5]:  # Usar apenas os 5 mais relevantes
            title = doc.get('title', 'Sem título')
            content = doc.get('content', '')[:500]  # Limitar tamanho
            
            context_parts.append(f"Título: {title}\nConteúdo: {content}\n")
        
        return "\n---\n".join(context_parts)
    
    def _generate_text_with_model(self, theme: str, context: str, model: str) -> str:
        """
        Gera texto usando modelo de IA (simulado).
        
        Args:
            theme (str): Tema do texto
            context (str): Contexto relevante
            model (str): Modelo a ser usado
            
        Returns:
            str: Texto gerado
        """
        # TODO: Implementar integração real com OpenAI/Claude
        # Por agora, retorna texto simulado
        
        prompt = f"""
        Com base no contexto fornecido abaixo, escreva um texto sobre: {theme}
        
        CONTEXTO:
        {context}
        
        TEMA: {theme}
        
        Escreva um texto informativo e bem estruturado sobre o tema, 
        usando as informações do contexto quando relevante.
        """
        
        # Simulação de texto gerado
        simulated_text = f"""
        # {theme}
        
        Com base nas informações disponíveis sobre {theme}, podemos compreender que este é um tópico 
        de grande relevância no contexto atual.
        
        ## Principais Aspectos
        
        O tema {theme} abrange diversos aspectos importantes que merecem atenção especial. 
        As informações coletadas indicam que há múltiplas perspectivas a serem consideradas.
        
        ## Conclusão
        
        Em conclusão, {theme} representa um assunto que requer análise cuidadosa e 
        consideração dos diversos fatores envolvidos. O contexto apresentado oferece 
        insights valiosos para uma compreensão mais profunda do tema.
        
        ---
        
        *Texto gerado automaticamente usando modelo: {model}*
        *Contexto utilizado: {len(context.split())} palavras*
        """
        
        logger.info(f"Texto gerado para tema: {theme} usando modelo: {model}")
        return simulated_text.strip()