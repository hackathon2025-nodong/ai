#!/usr/bin/env python3
import os
import argparse
from PyPDF2 import PdfReader, PdfWriter

def split_pdf(input_path, pages_per_chunk=20):
    """
    PDF 파일을 지정된 페이지 수만큼 분할합니다.
    
    Args:
        input_path: 분할할 PDF 파일 경로
        pages_per_chunk: 각 분할 파일에 포함될 페이지 수
    """
    
    print(f"PDF 파일 '{input_path}' 분할을 시작합니다...")
    
    pdf = PdfReader(input_path)
    total_pages = len(pdf.pages)
    
    
    base_name = os.path.basename(input_path)
    file_name = os.path.splitext(base_name)[0]
    output_dir = f"{file_name}_split"
    
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"출력 디렉토리 '{output_dir}'를 생성했습니다.")
    
    
    for i in range(0, total_pages, pages_per_chunk):
        output = PdfWriter()
        
       
        start_page = i
        end_page = min(i + pages_per_chunk, total_pages)
        
       
        for page_num in range(start_page, end_page):
            output.add_page(pdf.pages[page_num])
        
       
        output_filename = f"{output_dir}/{file_name}_pages_{start_page+1}-{end_page}.pdf"
        
       
        with open(output_filename, "wb") as output_file:
            output.write(output_file)
        
        print(f"생성됨: {output_filename} (페이지 {start_page+1}~{end_page}, 총 {end_page-start_page} 페이지)")
    
    print(f"\n분할 완료! 총 {total_pages} 페이지가 {output_dir} 폴더에 분할되었습니다.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDF 파일을 여러 개의 작은 PDF로 분할합니다.")
    parser.add_argument("input_pdf", help="분할할 PDF 파일의 경로")
    parser.add_argument("-p", "--pages", type=int, default=20, help="각 출력 파일의 페이지 수 (기본값: 20)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_pdf):
        print(f"오류: 파일 '{args.input_pdf}'를 찾을 수 없습니다.")
    else:
        split_pdf(args.input_pdf, args.pages) 