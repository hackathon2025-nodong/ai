import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings

# 1단계: 문서 로드 (PDF 파일 처음 10페이지만)
print("1단계: 문서 로드 중...")
loader = PyMuPDFLoader("외국인근로자_ocr.pdf")
docs = loader.load()[:10]  # 처음 10페이지만 로드
print(f"문서의 페이지 수: {len(docs)}")

# 2단계: 문서 분할
print("2단계: 문서 분할 중...")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
split_documents = text_splitter.split_documents(docs)
print(f"분할된 청크의 수: {len(split_documents)}")

# 3단계: 임베딩 생성 (KURE 모델 사용)
print("3단계: 한국어 검색 특화 KURE 임베딩 모델 로드 중...")
model_name = "nlpai-lab/KURE-v1"  # 고려대학교 NLP & AI 연구실의 한국어 검색 특화 모델
model_kwargs = {'device': 'cpu'}
embeddings = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs
)

# 4단계: 벡터 DB 생성 및 저장
print("4단계: 벡터 DB 생성 중...")
vectorstore = FAISS.from_documents(documents=split_documents, embedding=embeddings)

# 5단계: 검색기 생성
print("5단계: 검색기 생성 중...")
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})  # 상위 4개 문서 검색

# 6단계: 프롬프트 생성
print("6단계: 프롬프트 생성 중...")
prompt = PromptTemplate.from_template(
    """당신은 외국인근로자 고용 관련 질문에 답변하는 전문가입니다.
주어진 컨텍스트 정보를 사용하여 질문에 답변하세요.
컨텍스트에 관련 정보가 없으면 "해당 정보를 찾을 수 없습니다."라고 대답하세요.
한국어로 답변하세요. 검색결과로 얻은 정보만 답변하세요. 

#질문: 
{question} 

#컨텍스트: 
{context} 

#답변:"""
)

# 로컬에서 사용 가능한 모델 설정
try:
    from langchain_community.llms import Ollama
    print("7단계: Ollama 모델 설정 중...")
    llm = Ollama(model="llama3")
except (ImportError, Exception) as e:
    # Ollama를 사용할 수 없는 경우 기본 HuggingFace 모델 사용
    from langchain_community.llms import HuggingFaceHub
    print("7단계: HuggingFace Hub 모델 설정 중...")
    # 이 변수는 입력받거나 환경 변수에서 가져옵니다
    huggingface_api_token = os.environ.get("HUGGINGFACE_API_TOKEN")
    if not huggingface_api_token:
        huggingface_api_token = input("HuggingFace API 토큰을 입력하세요: ")
        os.environ["HUGGINGFACE_API_TOKEN"] = huggingface_api_token
    
    # 무료로 사용 가능한 LLM
    llm = HuggingFaceHub(
        repo_id="google/flan-t5-large",
        model_kwargs={"temperature": 0.1, "max_length": 512}
    )

# 8단계: 체인 생성
print("8단계: 체인 생성 중...")
chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 대화형 검색 시스템 실행
def run_qa_system():
    print("\n외국인근로자 고용 관련 질의응답 시스템이 준비되었습니다.")
    print("종료하려면 'exit' 또는 '종료'를 입력하세요.\n")
    
    while True:
        question = input("\n검색어를 입력하세요: ")
        if question.lower() in ['exit', '종료']:
            print("프로그램을 종료합니다.")
            break
            
        if not question.strip():
            continue
            
        print("답변 생성 중...")
        try:
            response = chain.invoke(question)
            print(f"\n답변: {response}")
        except Exception as e:
            print(f"오류 발생: {e}")

if __name__ == "__main__":
    run_qa_system() 