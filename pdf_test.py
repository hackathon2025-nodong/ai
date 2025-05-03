import ocrmypdf

# OCR 처리: 이미지 PDF → 텍스트 PDF로 변환
input_pdf = "200617 외국인근로자 고용관리 가이드북_최종본.pdf"     # 원본 PDF 경로
output_pdf = "외국인근로자_ocr.pdf"  # OCR 결과 저장 경로

# 기본 설정으로 처리 (일부 페이지만)
ocrmypdf.ocr(
    input_pdf, 
    output_pdf, 
    language="kor",        # 한국어 설정
    force_ocr=True,        # 기존 텍스트가 있어도 OCR 진행
    pages="1-10",          # 처음 10페이지만 처리
    output_type="pdf",     # PDF/A 변환을 건너뛰고 원본 색상 공간 유지
)

print("OCR 변환 완료! 텍스트가 포함된 PDF가 생성되었습니다.")
