import os
from dotenv import load_dotenv
from pymilvus import connections, Collection, utility

# Load environment variables
load_dotenv()

# Connect to Milvus
print("Milvus에 연결 중...")
connections.connect(
    alias="default",
    uri=os.getenv("MILVUS_URI"),
    token=os.getenv("MILVUS_TOKEN")
)

# Collection name
COLLECTION_NAME = "foreign_worker_guide"

# Check if collection exists
if not utility.has_collection(COLLECTION_NAME):
    print(f"Collection '{COLLECTION_NAME}'이 존재하지 않습니다!")
    exit(1)

print(f"Collection '{COLLECTION_NAME}' 존재 확인 ✓")

# Get collection stats
collection = Collection(COLLECTION_NAME)

# Try to load the collection
try:
    collection.load()
    print(f"Collection '{COLLECTION_NAME}' 로드 완료 ✓")
except Exception as e:
    try:
        # Alternative approach
        print(f"첫 번째 로드 방법 실패: {e}")
        print("다른 방식으로 시도...")
        collection = Collection(name=COLLECTION_NAME)
        print(f"Collection '{COLLECTION_NAME}' 액세스 완료 ✓")
    except Exception as e2:
        print(f"Collection 로드 중 오류 발생: {e2}")

# Try to get entity count using search
try:
    # Test search to check if the collection has data
    print("\n컬렉션 데이터 확인 중...")
    # Create a dummy vector with the right dimension
    dummy_vector = [0.0] * 1024  # KURE-v1 dimension
    
    search_params = {
        "metric_type": "COSINE",
        "params": {"nprobe": 10}
    }
    
    results = collection.search(
        data=[dummy_vector],
        anns_field="vector",
        param=search_params,
        limit=1,
        output_fields=["text"]
    )
    
    # If we got here, the collection has entities
    print("컬렉션에 데이터가 있습니다 ✓")
    
    # Check OCR files
    print("\n[OCR 파일 확인]")
    ocr_files = []
    for filename in os.listdir("ocr_results"):
        if filename.endswith(".txt"):
            file_size = os.path.getsize(os.path.join("ocr_results", filename))
            with open(os.path.join("ocr_results", filename), 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
            ocr_files.append((filename, file_size, lines))
    
    # Sort by filename
    ocr_files.sort()
    
    # Print information
    total_files = len(ocr_files)
    empty_files = 0
    total_lines = 0
    
    for filename, size, lines in ocr_files:
        status = "✓" if size > 0 and lines > 0 else "✗ (비어있음)"
        if size == 0 or lines == 0:
            empty_files += 1
        total_lines += lines
        print(f"파일: {filename}, 크기: {size/1024:.1f} KB, 라인 수: {lines} {status}")
    
    print(f"\n총 파일 수: {total_files}")
    print(f"비어있는 파일 수: {empty_files}")
    print(f"총 라인 수: {total_lines}")
    
    # Try to estimate entity count
    try:
        # Try another approach to get entity count
        import random
        import string
        
        # Generate a random query to see how many results we can get
        random_query = ''.join(random.choices(string.ascii_letters, k=10))
        print(f"\n랜덤 쿼리로 엔티티 수 추정 중: {random_query}")
        
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('nlpai-lab/KURE-v1')
        query_vector = model.encode(random_query, normalize_embeddings=True)
        
        # Try with maximum limit to estimate total count
        max_limit = 16384  # Maximum allowed by Milvus
        
        results = collection.search(
            data=[query_vector.tolist()],
            anns_field="vector",
            param=search_params,
            limit=max_limit,
            output_fields=["text"]
        )
        
        result_count = len(results[0])
        print(f"최대 {max_limit}개 중 가져온 결과 수: {result_count}")
        
        # Check a few random results
        if result_count > 0:
            print("\n무작위 결과 샘플 (5개 이하):")
            samples = min(5, result_count)
            for i in range(samples):
                idx = random.randint(0, result_count-1)
                hit = results[0][idx]
                text_sample = hit.entity.get("text")
                if text_sample and len(text_sample) > 100:
                    text_sample = text_sample[:100] + "..."
                print(f"{i+1}. ID: {hit.id}, 점수: {hit.score:.4f}, 텍스트: {text_sample}")
        
    except Exception as e:
        print(f"엔티티 수 추정 중 오류 발생: {e}")
    
except Exception as e:
    print(f"데이터 확인 중 오류 발생: {e}")
    print("데이터가 아직 임베딩되지 않았거나, API 접근 방식에 문제가 있습니다.") 