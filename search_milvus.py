import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection, utility
import time

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
    
    # Explicitly load collection and retry if needed
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            print(f"Loading collection '{COLLECTION_NAME}'...")
            collection.load()
            print(f"Collection loaded successfully.")
            break
        except Exception as e:
            print(f"Load attempt {retry_count+1} failed: {e}")
            retry_count += 1
            if retry_count >= max_retries:
                print(f"Failed to load collection after {max_retries} attempts.")
                return []
            print(f"Retrying in 2 seconds...")
            time.sleep(2)
    
    # Encode query
    query_vector = model.encode(query, normalize_embeddings=True)
    
    # Search
    search_params = {
        "metric_type": "COSINE",
        "params": {"nprobe": 10}
    }
    
    try:
        print("Executing search...")
        results = collection.search(
            data=[query_vector.tolist()],
            anns_field="vector",
            param=search_params,
            limit=top_k,
            output_fields=["text"]
        )
        print(f"Search completed, found {len(results[0])} results.")
        
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
    except Exception as e:
        print(f"Search error: {e}")
        return []

if __name__ == "__main__":
    # Test queries
    test_queries = [
        "농약 중독의 증상은 무엇인가?",
        "예초기 사용 시 재해 예방 방법은?",
        "트랙터 안전 운전을 위한 조치사항은?"
    ]
    
    for query in test_queries:
        print(f"\n검색어: '{query}'")
        print("=" * 80)
        
        results = search_similar_texts(query)
        
        for i, result in enumerate(results):
            print(f"{i+1}. 유사도 점수: {result['score']:.4f}")
            print(f"내용: {result['text'][:300]}...")  # Show first 300 chars
            print("-" * 80) 