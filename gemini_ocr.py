#!/usr/bin/env python3
import os
import glob
import time
import google.generativeai as genai
from pathlib import Path

# API 키 설정
API_KEY = "api key" 

# Gemini API 초기화
genai.configure(api_key=API_KEY)


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

def process_pdf_directory(directory_path):
    """
    디렉토리 내의 모든 PDF 파일을 처리합니다.
    
    Args:
        directory_path: PDF 파일이 있는 디렉토리 경로
    """
    # 결과를 저장할 디렉토리 생성
    results_dir = os.path.join(os.path.dirname(directory_path), "ocr_results")
    os.makedirs(results_dir, exist_ok=True)
    print(f"결과 저장 디렉토리: {results_dir}")
    
    # PDF 파일 목록 가져오기
    pdf_files = sorted(glob.glob(os.path.join(directory_path, "*.pdf")))
    print(f"처리할 PDF 파일 수: {len(pdf_files)}")
    
    for i, pdf_path in enumerate(pdf_files, 1):
        # PDF 파일명 추출
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        # 결과 저장할 파일 경로
        output_path = os.path.join(results_dir, f"{pdf_name}_ocr.txt")
        
        print(f"\n[{i}/{len(pdf_files)}] 파일 처리 중: {pdf_name}")
        
        # 이미 처리된 파일이면 건너뛰기
        if os.path.exists(output_path):
            print(f"이미 처리된 파일입니다. 건너뜁니다: {output_path}")
            continue
        
        # OCR 처리
        start_time = time.time()
        extracted_text = ocr_pdf_with_gemini(pdf_path)
        elapsed_time = time.time() - start_time
        
        # 결과 저장
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(extracted_text)
        
        print(f"OCR 결과 저장 완료: {output_path}")
        print(f"처리 시간: {elapsed_time:.2f}초")
        
        # API 호출 제한을 위한 딜레이 (필요한 경우)
        if i < len(pdf_files):
            print("다음 파일 처리 전 5초 대기...")
            time.sleep(5)
    
    print("\n모든 PDF 파일 처리 완료!")
    print(f"OCR 결과는 {results_dir} 디렉토리에 저장되었습니다.")

if __name__ == "__main__":
    # 분할된 PDF 파일이 있는 디렉토리 경로
    pdf_directory = "외국인근로자_ocr_split"
    
    # 경로가 존재하는지 확인
    if not os.path.exists(pdf_directory):
        print(f"오류: 디렉토리 '{pdf_directory}'를 찾을 수 없습니다.")
    else:
        process_pdf_directory(pdf_directory) 