#!/usr/bin/env python3
"""
Test script to verify Elasticsearch connection and functionality.
"""

import sys
import os

# Add the current directory to Python path
sys.path.append('/app')

try:
    from services.elasticsearch_service import ElasticsearchService
    from config.settings import settings
    
    print("Testing Elasticsearch connection...")
    print(f"Elasticsearch URL: {settings.elasticsearch_url}")
    print(f"Username: {settings.elasticsearch_username}")
    
    # Create service instance
    es_service = ElasticsearchService()
    
    # Test connection
    if es_service.check_connection():
        print("✅ Elasticsearch connection: SUCCESS")
    else:
        print("❌ Elasticsearch connection: FAILED")
        sys.exit(1)
    
    # Test search functionality
    print("\nTesting search functionality...")
    results = es_service.search_content("marketing digital", size=3)
    
    if results:
        print(f"✅ Search results: Found {len(results)} results")
        for i, result in enumerate(results, 1):
            title = result["source"].get("title", "No title")
            score = result.get("score", 0)
            print(f"  {i}. {title} (score: {score:.2f})")
    else:
        print("❌ Search results: No results found")
    
    # Test context retrieval
    print("\nTesting context retrieval...")
    context = es_service.get_context_for_topic("redes sociais")
    
    if context:
        print("✅ Context retrieval: SUCCESS")
        print(f"   Context length: {len(context)} characters")
        print(f"   Preview: {context[:100]}...")
    else:
        print("❌ Context retrieval: FAILED")
    
    print("\n🎉 All tests completed successfully!")
    
except Exception as e:
    print(f"❌ Test failed with error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)