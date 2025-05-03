#!/usr/bin/env python3
import argparse, sys
from pathlib import Path
from pdf2image import convert_from_path
import pytesseract

def ocr_pdf_pages(pdf_path: Path, start: int, end: int, dpi: int = 300):
    # 필요한 페이지만 렌더링
    images = convert_from_path(
        pdf_path, dpi=dpi, first_page=start, last_page=end
    )

    results = []
    for idx, img in enumerate(images, start=start):
        text = pytesseract.image_to_string(img, lang="kor+eng", config="--psm 4")
        results.append({"page": idx, "text": text})
    return results

def extract_text_from_pdf(pdf_path: Path):
    # PyPDF 또는 다른 라이브러리를 사용하여 텍스트 추출 시도
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        
        results = []
        for i, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            results.append({"page": i, "text": text})
        
        # 텍스트가 성공적으로 추출되었는지 확인
        has_text = any(len(r["text"].strip()) > 0 for r in results)
        
        if has_text:
            print("✅ PDF에서 텍스트 추출 성공!")
            return results
        else:
            print("⚠️ PDF에서 텍스트를 추출했으나 내용이 없습니다. OCR로 전환합니다.")
            return None
    except Exception as e:
        print(f"⚠️ 직접 텍스트 추출 실패 ({str(e)}). OCR로 전환합니다.")
        return None

def cli():
    ap = argparse.ArgumentParser(description="PDF에서 텍스트 추출")
    ap.add_argument("pdf", type=Path, nargs="?", default=Path("osaka_mission_camp_report.pdf"), 
                   help="PDF 파일 경로 (기본값: osaka_mission_camp_report.pdf)")
    ap.add_argument("--start", type=int, default=1, help="시작 페이지")
    ap.add_argument("--end", type=int, default=5, help="끝 페이지(포함)")
    ap.add_argument("--dpi", type=int, default=300, help="OCR 렌더링 DPI")
    ap.add_argument("--force-ocr", action="store_true", help="OCR 강제 사용")
    args = ap.parse_args()

    if not args.pdf.exists():
        sys.exit(f"❌ 파일이 존재하지 않습니다: {args.pdf}")
    
    # 실행 방법 결정
    if args.force_ocr:
        print(f"OCR 모드로 {args.pdf} 처리 중...")
        results = ocr_pdf_pages(args.pdf, args.start, args.end, args.dpi)
    else:
        # 먼저 직접 텍스트 추출 시도
        print(f"{args.pdf} 에서 텍스트 추출 시도 중...")
        results = extract_text_from_pdf(args.pdf)
        
        # 텍스트 추출 실패 시 OCR 사용
        if results is None:
            print(f"OCR 모드로 {args.pdf} 처리 중...")
            results = ocr_pdf_pages(args.pdf, args.start, args.end, args.dpi)
    
    # 결과 출력
    for page in results:
        print(f"\n=== p.{page['page']} ({len(page['text'])} chars) ===\n")
        print(page["text"][:500], "...\n")  # 500자만 미리보기
    
    # 전체 텍스트 길이 출력
    total_chars = sum(len(p["text"]) for p in results)
    print(f"\n총 {len(results)}페이지, {total_chars}자 추출됨")

if __name__ == "__main__":
    cli()
