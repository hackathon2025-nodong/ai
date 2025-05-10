import os
from typing import List, Dict
import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
COLLECTION_NAME = "foreign_worker_guide"
DIMENSION = 1024  # KURE-v1 고려대 개발 모델의 정확한.
BATCH_SIZE = 100

def load_text_files(directory: str) -> List[str]:
    """Load all text files from the directory and return their contents."""
    texts = []
    for filename in os.listdir(directory):
        if filename.endswith('.txt'):
            with open(os.path.join(directory, filename), 'r', encoding='utf-8') as f:
                texts.append(f.read())
    return texts

def split_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip(): 
            chunks.append(chunk)
    
    return chunks

def create_collection():
    """Create Milvus collection if it doesn't exist."""
    if utility.has_collection(COLLECTION_NAME):
        utility.drop_collection(COLLECTION_NAME)
    
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=DIMENSION)
    ]
    
    schema = CollectionSchema(fields=fields, description="Foreign worker guide text chunks")
    collection = Collection(name=COLLECTION_NAME, schema=schema)
    
    # 인덱스 생성
    index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 4096}
    }
    collection.create_index(field_name="vector", index_params=index_params)
    
    return collection

def main():
    #milvus 연결
    connections.connect(
        alias="default",
        uri=os.getenv("MILVUS_URI"),
        token=os.getenv("MILVUS_TOKEN")
    )
    
    #모델 로드
    print("Loading embedding model (KURE-v1)...")
    # KURE-v1 모델 로드 - 한국어에 최적화된 모델
    model = SentenceTransformer('nlpai-lab/KURE-v1')
    
    #컬렉션 생성
    print("Creating collection...")
    collection = create_collection()
    
    print("Loading text files...")
    texts = load_text_files("ocr_results")
    
    #텍스트 청크 분할
    print("Splitting texts into chunks...")
    chunks = []
    for text in texts:
        chunks.extend(split_text(text))
    
    print("Generating embeddings and inserting into Milvus...")
    for i in tqdm(range(0, len(chunks), BATCH_SIZE)):
        batch_chunks = chunks[i:i + BATCH_SIZE]
        
        embeddings = model.encode(batch_chunks, normalize_embeddings=True)
        
        entities = [
            {"text": chunk, "vector": embedding.tolist()}
            for chunk, embedding in zip(batch_chunks, embeddings)
        ]
        
        #milvus에 삽입
        collection.insert(entities)
    
    collection.load()
    print("Data ingestion completed!")

if __name__ == "__main__":
    main() 