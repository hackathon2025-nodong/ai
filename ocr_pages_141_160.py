#!/usr/bin/env python3
import os
import time
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# API 키 설정
API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini API 초기화
genai.configure(api_key=API_KEY)

# Gemini 모델 설정
model = genai.GenerativeModel('gemini-2.0-flash')

def ocr_pdf_with_gemini(pdf_path):
    """
    Gemini API를 사용하여 PDF 파일에서 텍스트를 추출합니다.
    
    Args:
        pdf_path: OCR 처리할 PDF 파일 경로
    
    Returns:
        추출된 텍스트
    """
    print(f"\n처리 중: {pdf_path}")
    
    try:
        # PDF 파일 업로드
        pdf_file = genai.upload_file(path=pdf_path)
        print(f"파일 업로드 완료: {pdf_file.uri}")
        
        # OCR 프롬프트 작성
        prompt = """
        PDF 파일에서 모든 텍스트를 추출해주세요. 
        이미지, 표, 차트 등의 시각적 요소도 모두 텍스트로 설명해주세요.
        레이아웃과 구조를 최대한 보존해주세요.
        한국어 문서이므로 텍스트가 깨지지 않게 주의해주세요.
        """
        
        # Gemini API 호출
        print("Gemini API 호출 중...")
        response = model.generate_content([pdf_file, prompt])
        
        # 응답 처리
        extracted_text = response.text
        print(f"텍스트 추출 완료! 길이: {len(extracted_text)} 자")
        
        return extracted_text
    
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return f"오류: {str(e)}"

def process_specific_pdf(pdf_path, output_dir):
    """
    특정 PDF 파일을 처리합니다.
    
    Args:
        pdf_path: 처리할 PDF 파일 경로
        output_dir: 결과를 저장할 디렉토리
    """
    # 결과를 저장할 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    print(f"결과 저장 디렉토리: {output_dir}")
    
    # PDF 파일명 추출
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    # 결과 저장할 파일 경로
    output_path = os.path.join(output_dir, f"{pdf_name}_ocr.txt")
    
    print(f"\n파일 처리 중: {pdf_name}")
    
    # OCR 처리
    start_time = time.time()
    extracted_text = ocr_pdf_with_gemini(pdf_path)
    elapsed_time = time.time() - start_time
    
    # 결과 저장
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(extracted_text)
    
    print(f"OCR 결과 저장 완료: {output_path}")
    print(f"처리 시간: {elapsed_time:.2f}초")

if __name__ == "__main__":
    # API 키 확인
    if not API_KEY:
        print("오류: GEMINI_API_KEY가 설정되지 않았습니다. .env 파일에 GEMINI_API_KEY를 추가해주세요.")
        exit(1)
        
    # 외국인근로자 가이드 PDF 파일 경로 (141-160 페이지)
    pdf_path = "외국인근로자_ocr_split/외국인근로자_ocr_pages_141-160.pdf"
    
    # 결과 저장 디렉토리
    output_dir = "ocr_results"
    
    # 파일 존재 여부 확인
    if not os.path.exists(pdf_path):
        print(f"오류: PDF 파일 '{pdf_path}'을 찾을 수 없습니다.")
        exit(1)
    
    # PDF 처리 실행
    process_specific_pdf(pdf_path, output_dir)
    
    print("\nPDF 파일 처리 완료!")
    print(f"OCR 결과는 {output_dir} 디렉토리에 저장되었습니다.") 