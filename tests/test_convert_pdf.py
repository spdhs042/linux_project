import pytest
import os
import sys

# utils 폴더를 찾을 수 있도록 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.convert_pdf_to_images import convert_pdf_to_images  # 중복 제거

def test_convert_pdf():
    sample_pdf = "tests/sample.pdf"
    output_folder = "tests/output"

    image_paths = convert_pdf_to_images(sample_pdf, output_folder)

    assert len(image_paths) > 0  # 변환된 이미지가 1개 이상인지 확인
    assert os.path.exists(image_paths[0])  # 첫 번째 이미지가 정상적으로 생성되었는지 확인
