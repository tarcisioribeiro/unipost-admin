#!/usr/bin/env python3
"""
Dataset download and index script for UniPOST Elasticsearch.

This script downloads marketing and social media content datasets
and indexes them into Elasticsearch for context retrieval.
"""

import json
import time
import requests
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
from typing import List, Dict, Any
import os
import sys


def get_elasticsearch_client() -> Elasticsearch:
    """Get Elasticsearch client with authentication."""
    es_password = os.environ.get('ELASTIC_PASSWORD', 'changeme')
    return Elasticsearch(
        'http://localhost:9200',
        basic_auth=('elastic', es_password),
        verify_certs=False,
        ssl_show_warn=False
    )


def wait_for_elasticsearch(client: Elasticsearch, max_retries: int = 30) -> bool:
    """Wait for Elasticsearch to be ready."""
    print("Waiting for Elasticsearch to be ready...")
    
    for i in range(max_retries):
        try:
            if client.ping():
                print("Elasticsearch is ready!")
                return True
        except Exception as e:
            print(f"Attempt {i+1}/{max_retries}: Elasticsearch not ready yet - {e}")
            time.sleep(10)
    
    print("Elasticsearch failed to become ready")
    return False


def create_index_if_not_exists(client: Elasticsearch, index_name: str) -> bool:
    """Create index with proper mappings if it doesn't exist."""
    if client.indices.exists(index=index_name):
        print(f"Index {index_name} already exists")
        return True
    
    mapping = {
        "mappings": {
            "properties": {
                "title": {
                    "type": "text",
                    "analyzer": "portuguese"
                },
                "content": {
                    "type": "text",
                    "analyzer": "portuguese"
                },
                "tags": {
                    "type": "keyword"
                },
                "timestamp": {
                    "type": "date"
                },
                "source": {
                    "type": "keyword"
                },
                "category": {
                    "type": "keyword"
                },
                "content_vector": {
                    "type": "dense_vector",
                    "dims": 384
                }
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "portuguese": {
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "portuguese_stop",
                            "portuguese_stemmer"
                        ]
                    }
                },
                "filter": {
                    "portuguese_stop": {
                        "type": "stop",
                        "stopwords": "_portuguese_"
                    },
                    "portuguese_stemmer": {
                        "type": "stemmer",
                        "language": "portuguese"
                    }
                }
            }
        }
    }
    
    try:
        client.indices.create(index=index_name, body=mapping)
        print(f"Index {index_name} created successfully")
        return True
    except Exception as e:
        print(f"Error creating index: {e}")
        return False


def generate_marketing_content() -> List[Dict[str, Any]]:
    """Generate a comprehensive marketing content dataset."""
    base_date = datetime.now() - timedelta(days=30)
    
    content_data = [
        {
            "title": "Estratégias de Marketing Digital para 2024",
            "content": "O marketing digital em 2024 será dominado por inteligência artificial, personalização em massa e experiências omnicanal. As empresas devem focar em automação inteligente, análise preditiva e engajamento em tempo real para se manterem competitivas.",
            "tags": ["marketing digital", "ia", "automação", "2024"],
            "category": "estratégia",
            "source": "blog"
        },
        {
            "title": "Como Criar Conteúdo Viral nas Redes Sociais",
            "content": "Conteúdo viral combina timing perfeito, emoções fortes e relevância cultural. Use storytelling autêntico, visuais impactantes e hashtags estratégicas. Monitore tendências e responda rapidamente aos momentos oportunos.",
            "tags": ["redes sociais", "viral", "conteúdo", "engagement"],
            "category": "social media",
            "source": "guia"
        },
        {
            "title": "ROI em Campanhas de Influencer Marketing",
            "content": "Medir ROI em campanhas de influencers requer tracking de métricas específicas: reach, engagement, conversões e brand awareness. Use códigos promocionais exclusivos, UTMs e ferramentas de analytics especializadas.",
            "tags": ["influencer", "roi", "métricas", "campanhas"],
            "category": "analytics",
            "source": "estudo"
        },
        {
            "title": "Email Marketing: Segmentação e Personalização",
            "content": "Email marketing eficaz depende de segmentação precisa e personalização dinâmica. Use dados comportamentais, preferências e histórico de compras para criar campanhas relevantes que geram conversões.",
            "tags": ["email marketing", "segmentação", "personalização"],
            "category": "email",
            "source": "tutorial"
        },
        {
            "title": "SEO Local para Pequenas Empresas",
            "content": "SEO local ajuda pequenas empresas a competir digitalmente. Otimize Google My Business, colete reviews, use palavras-chave locais e crie conteúdo relevante para sua região geográfica.",
            "tags": ["seo", "local", "pequenas empresas", "google"],
            "category": "seo",
            "source": "guia"
        },
        {
            "title": "Marketing de Conteúdo B2B: Melhores Práticas",
            "content": "Marketing de conteúdo B2B foca em educação, autoridade e confiança. Produza whitepapers, webinars, case studies e artigos técnicos que demonstrem expertise e ajudem na jornada de compra.",
            "tags": ["b2b", "conteúdo", "autoridade", "educação"],
            "category": "b2b",
            "source": "artigo"
        },
        {
            "title": "Chatbots e Atendimento Automatizado",
            "content": "Chatbots melhoram experiência do cliente e reduzem custos operacionais. Implemente fluxos inteligentes, integre com CRM e mantenha opção de escalação para atendimento humano quando necessário.",
            "tags": ["chatbots", "automação", "atendimento", "ai"],
            "category": "automação",
            "source": "tecnologia"
        },
        {
            "title": "Video Marketing: Tendências e Estratégias",
            "content": "Vídeo é o formato de conteúdo mais consumido. Explore vídeos curtos, lives, stories e conteúdo educacional. Otimize para mobile, use legendas e CTAs claros para maximizar engajamento.",
            "tags": ["video", "marketing", "mobile", "engagement"],
            "category": "conteúdo",
            "source": "tendências"
        },
        {
            "title": "Marketing Omnichannel: Integrando Canais",
            "content": "Estratégia omnichannel unifica experiência do cliente em todos os pontos de contato. Sincronize dados, mensagens e ofertas entre online e offline para criar jornadas fluidas.",
            "tags": ["omnichannel", "integração", "experiência", "cliente"],
            "category": "estratégia",
            "source": "framework"
        },
        {
            "title": "Growth Hacking para Startups",
            "content": "Growth hacking combina marketing, produto e dados para crescimento rápido. Experimente, meça, aprenda e escale táticas de baixo custo que geram alto impacto no crescimento.",
            "tags": ["growth hacking", "startups", "crescimento", "experimentos"],
            "category": "growth",
            "source": "metodologia"
        },
        {
            "title": "Marketing de Afiliados: Como Estruturar",
            "content": "Programas de afiliados ampliam alcance com investimento baseado em performance. Defina comissões atrativas, forneça materiais de marketing e use plataformas especializadas para gestão.",
            "tags": ["afiliados", "performance", "comissões", "parcerias"],
            "category": "afiliados",
            "source": "programa"
        },
        {
            "title": "Marketing Conversacional: Engajamento em Tempo Real",
            "content": "Marketing conversacional usa mensagens personalizadas e interações em tempo real. Implemente chat ao vivo, bots inteligentes e marketing por mensagens para acelerar conversões.",
            "tags": ["conversacional", "tempo real", "chat", "personalização"],
            "category": "conversação",
            "source": "estratégia"
        },
        {
            "title": "Análise de Concorrência Digital",
            "content": "Análise de concorrência revela oportunidades e ameaças. Monitore palavras-chave, backlinks, conteúdo, redes sociais e estratégias de advertising dos concorrentes usando ferramentas especializadas.",
            "tags": ["análise", "concorrência", "monitoramento", "inteligência"],
            "category": "analytics",
            "source": "pesquisa"
        },
        {
            "title": "Marketing Automation: Workflows Eficientes",
            "content": "Automação de marketing nutre leads e acelera conversões. Crie workflows baseados em comportamento, segmente audiências e personalize comunicações para maximizar ROI.",
            "tags": ["automação", "workflows", "leads", "nurturing"],
            "category": "automação",
            "source": "implementação"
        },
        {
            "title": "Branded Content: Storytelling de Marca",
            "content": "Branded content conecta marcas com audiências através de histórias autênticas. Crie narrativas envolventes que transmitam valores da marca sem ser promocional demais.",
            "tags": ["branded content", "storytelling", "autenticidade", "marca"],
            "category": "branding",
            "source": "criativo"
        }
    ]
    
    # Add timestamps
    for i, item in enumerate(content_data):
        item['timestamp'] = (base_date + timedelta(days=i*2)).isoformat()
    
    return content_data


def index_documents(client: Elasticsearch, index_name: str, documents: List[Dict[str, Any]]) -> bool:
    """Index documents into Elasticsearch."""
    try:
        for i, doc in enumerate(documents):
            response = client.index(index=index_name, document=doc)
            print(f"Indexed document {i+1}/{len(documents)}: {doc['title'][:50]}...")
        
        # Refresh index
        client.indices.refresh(index=index_name)
        print(f"Successfully indexed {len(documents)} documents")
        return True
        
    except Exception as e:
        print(f"Error indexing documents: {e}")
        return False


def main():
    """Main execution function."""
    print("Starting dataset download and indexing...")
    
    # Get Elasticsearch client
    client = get_elasticsearch_client()
    
    # Wait for Elasticsearch to be ready
    if not wait_for_elasticsearch(client):
        print("Failed to connect to Elasticsearch")
        sys.exit(1)
    
    # Create index
    index_name = "unipost_content"
    if not create_index_if_not_exists(client, index_name):
        print("Failed to create index")
        sys.exit(1)
    
    # Generate and index content
    print("Generating marketing content dataset...")
    content_data = generate_marketing_content()
    
    print(f"Indexing {len(content_data)} documents...")
    if index_documents(client, index_name, content_data):
        print("Dataset indexing completed successfully!")
    else:
        print("Failed to index dataset")
        sys.exit(1)


if __name__ == "__main__":
    main()