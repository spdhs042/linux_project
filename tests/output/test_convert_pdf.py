import pytest
from utils.convert_pdf_to_images import convert_pdf_to_images
import os

def test_convert_pdf():
    sample_pdf = "tests/sample.pdf"
    output_folder = "tests/output"

    image_paths = convert_pdf_to_images(sample_pdf, output_folder)

    assert len(image_paths) > 0  # 변환된 이미지가 1개 이상인지 확인
    assert os.path.exists(image_paths[0])  # 첫 번째 이미지가 정상적으로 생성되었는지 확인
