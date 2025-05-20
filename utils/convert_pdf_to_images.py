import fitz  # PyMuPDF 라이브러리 (PDF 처리용)
import os    # 파일 및 디렉토리 관리를 위한 os 모듈

def convert_pdf_to_images(pdf_path, output_folder):
    """PDF를 여러 개의 이미지로 변환하는 함수"""

    # PDF 파일 열기
    doc = fitz.open(pdf_path)

    # 변환된 이미지를 저장할 폴더가 없으면 생성
    os.makedirs(output_folder, exist_ok=True)

    image_paths = []  # 이미지 파일 경로를 저장할 리스트

    # PDF의 각 페이지를 이미지로 변환
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=150)  # 각 페이지를 150 DPI 해상도로 이미지로 변환

        # 변환된 이미지를 저장할 파일 이름 설정 (slide_1.png, slide_2.png ...)
        image_name = f"slide_{i+1}.png"
        image_path = os.path.join(output_folder, image_name)

        # 이미지 파일 저장
        pix.save(image_path)

        # 저장된 이미지 경로 리스트에 추가
        image_paths.append(image_path)

    return image_paths  # 변환된 이미지 경로 리스트 반환
