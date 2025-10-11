#!/usr/bin/env python3
import os
import time
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection, utility
import google.generativeai as genai

# 환경변수 로드
load_dotenv()

# Milvus 연결 정보
MILVUS_URI = os.getenv("MILVUS_URI")
MILVUS_TOKEN = os.getenv("MILVUS_TOKEN")
COLLECTION_NAME = "foreign_worker_guide"

# Gemini API 키
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# API 키 확인
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

if not MILVUS_URI or not MILVUS_TOKEN:
    raise ValueError("MILVUS_URI 또는 MILVUS_TOKEN이 설정되지 않았습니다. .env 파일을 확인하세요.")

# Gemini API 초기화
print("Gemini API 초기화 중...")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# Milvus 연결
print(f"Milvus 연결 중... (URI: {MILVUS_URI})")
connections.connect(
    alias="default",
    uri=MILVUS_URI,
    token=MILVUS_TOKEN
)

# 임베딩 모델 로드
print("임베딩 모델 로드 중...")
embedding_model = SentenceTransformer('nlpai-lab/KURE-v1')

def vector_search(query, top_k=5):
    """
    벡터 검색을 수행합니다.
    
    Args:
        query: 검색 쿼리
        top_k: 반환할 결과 수
        
    Returns:
        검색 결과 목록 (텍스트와 점수)
    """
    print(f"\n쿼리: '{query}' 검색 중...")
    
    # 컬렉션 로드
    if not utility.has_collection(COLLECTION_NAME):
        print(f"컬렉션 '{COLLECTION_NAME}'이 존재하지 않습니다!")
        return []
    
    collection = Collection(COLLECTION_NAME)
    
    try:
        collection.load()
        print("컬렉션 로드 완료")
    except Exception as e:
        print(f"컬렉션 로드 오류: {e}")
        return []
    
    # 쿼리 임베딩
    query_vector = embedding_model.encode(query, normalize_embeddings=True)
    
    # 검색 실행
    search_params = {
        "metric_type": "COSINE",
        "params": {"nprobe": 10}
    }
    
    try:
        results = collection.search(
            data=[query_vector.tolist()],
            anns_field="vector",
            param=search_params,
            limit=top_k,
            output_fields=["text"]
        )
        
        # 결과 포맷팅
        search_results = []
        for hits in results:
            for hit in hits:
                search_results.append({
                    "text": hit.entity.get("text"),
                    "score": hit.score
                })
        
        print(f"검색 결과: {len(search_results)}개 찾음")
        return search_results
    
    except Exception as e:
        print(f"검색 오류: {e}")
        return []

def generate_rag_response(query, search_results):
    """
    검색 결과를 기반으로 Gemini를 사용해 응답을 생성합니다.
    
    Args:
        query: 사용자 질문
        search_results: 벡터 검색 결과
        
    Returns:
        생성된 응답
    """
    if not search_results:
        return "관련 정보를 찾을 수 없습니다."
    
    # 검색 결과 통합
    context = ""
    for i, result in enumerate(search_results):
        context += f"문서 {i+1} (유사도: {result['score']:.4f}):\n{result['text']}\n\n"
    
    # Gemini 프롬프트 작성
    prompt = f"""
다음은 외국인 근로자 고용 가이드에서 검색한 정보입니다:

{context}

위 정보를 바탕으로 다음 질문에 답변해주세요:
{query}

가이드에 없는 내용이라면 "제공된 문서에서 해당 정보를 찾을 수 없습니다"라고 말하세요.
답변은 간결하고 정확하게 작성해주세요.
"""
    
    print("Gemini API 호출 중...")
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API 오류: {e}")
        return f"오류가 발생했습니다: {str(e)}"

def rag_qa(query):
    """
    벡터 검색 결과를 기반으로 질의응답을 수행합니다.
    
    Args:
        query: 사용자 질문
        
    Returns:
        생성된 응답
    """
    print(f"\n[질문] {query}")
    print("-" * 80)
    
    # 벡터 검색 수행
    start_time = time.time()
    search_results = vector_search(query)
    search_time = time.time() - start_time
    
    if not search_results:
        return "검색 결과가 없습니다."
    
    # 검색 결과 출력
    print("\n검색 결과 미리보기:")
    for i, result in enumerate(search_results[:2]):  # 상위 2개만 표시
        text_preview = result["text"][:150] + "..." if len(result["text"]) > 150 else result["text"]
        print(f"{i+1}. 유사도: {result['score']:.4f}, 내용: {text_preview}")
    
    # Gemini로 응답 생성
    start_time = time.time()
    response = generate_rag_response(query, search_results)
    generation_time = time.time() - start_time
    
    print(f"\n검색 시간: {search_time:.2f}초, 생성 시간: {generation_time:.2f}초")
    print("-" * 80)
    print("[응답]\n", response)
    
    return response

if __name__ == "__main__":
    # 테스트 질문 목록
    test_questions = [
        "농약 중독의 증상은 무엇이며 대처방법은?",
        "트랙터 안전 운전을 위해 어떤 조치를 취해야 하나요?",
        "외국인 근로자 고용허가제란 무엇인가요?",
        "어업 작업 안전사고는 언제 많이 발생하나요?",
        "예초기 사용 시 안전 수칙은?"
    ]
    
    print("=" * 80)
    print("외국인 근로자 고용 가이드 RAG 테스트")
    print("=" * 80)
    
    # 각 질문에 대한 RAG 테스트
    for i, question in enumerate(test_questions, 1):
        print(f"\n테스트 {i}/{len(test_questions)}")
        rag_qa(question)
        
        # 마지막 질문이 아니면 잠시 대기
        if i < len(test_questions):
            print("\n3초 후 다음 질문으로 넘어갑니다...")
            time.sleep(3)
    
    print("\n모든 테스트가 완료되었습니다!") 