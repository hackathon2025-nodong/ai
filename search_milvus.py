import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection, utility

# Load environment variables
load_dotenv()

# Connect to Milvus
connections.connect(
    alias="default",
    uri=os.getenv("MILVUS_URI"),
    token=os.getenv("MILVUS_TOKEN")
)

# Collection name
COLLECTION_NAME = "foreign_worker_guide"

def search_similar_texts(query, top_k=5):
    """
    Search for similar texts in Milvus
    """
    # Load the same model used for encoding
    model = SentenceTransformer('nlpai-lab/KURE-v1')
    
    # Check if collection exists
    if not utility.has_collection(COLLECTION_NAME):
        print(f"Collection '{COLLECTION_NAME}' does not exist!")
        return []
    
    # Get collection
    collection = Collection(COLLECTION_NAME)
    
    # Load collection (always try to load it to ensure it's ready for search)
    try:
        utility.load_collection(COLLECTION_NAME)
    except Exception as e:
        print(f"Collection already loaded or error: {e}")
    
    # Encode query
    query_vector = model.encode(query, normalize_embeddings=True)
    
    # Search
    search_params = {
        "metric_type": "COSINE",
        "params": {"nprobe": 10}
    }
    
    results = collection.search(
        data=[query_vector.tolist()],
        anns_field="vector",
        param=search_params,
        limit=top_k,
        output_fields=["text"]
    )
    
    # Format results
    search_results = []
    for hits in results:
        for hit in hits:
            search_results.append({
                "id": hit.id,
                "score": hit.score,
                "text": hit.entity.get("text")
            })
    
    return search_results

if __name__ == "__main__":
    # Test queries
    test_queries = [
        "외국인 근로자 고용허가제란 무엇인가?",
        "외국인 근로자 보험 가입은 어떻게 하나요?",
        "근로계약 기간은 얼마나 되나요?",
        "외국인 근로자 고용 사업주의 의무는 무엇인가요?",
        "주요 유관기관 안내란?"
    ]
    
    for query in test_queries:
        print(f"\n검색어: '{query}'")
        print("=" * 80)
        
        results = search_similar_texts(query)
        
        for i, result in enumerate(results):
            print(f"{i+1}. 유사도 점수: {result['score']:.4f}")
            print(f"내용: {result['text'][:300]}...")  # Show first 300 chars
            print("-" * 80) 