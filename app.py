# 📌 Flask 및 필요한 모듈 import
from flask import Flask, render_template, request, redirect, url_for, session
import csv  # CSV 파일 처리 모듈
import uuid  # 사용자 고유 ID 생성 모듈
import os  # 파일 및 폴더 관리 모듈
import shutil  # 폴더 정리 모듈
import pandas as pd  # 데이터 분석을 위한 pandas 모듈
from utils.convert_pdf_to_images import convert_pdf_to_images
import json  # JSON 데이터 저장 및 관리

# Flask 애플리케이션 초기화
app = Flask(__name__)
app.secret_key = 'your-secret-key'  # 세션 관리를 위한 secret key 설정

# 파일 저장 폴더 설정
UPLOAD_FOLDER = 'uploads'  # PDF 파일 업로드 폴더
IMAGE_FOLDER = 'static/slides'  # 변환된 슬라이드 이미지 저장 폴더
SLIDES_FILE = 'slides.json'  # 모든 사용자가 공유할 슬라이드 데이터 파일
RESPONSES_FILE = 'responses.json'  # 모든 사용자의 응답을 저장하는 파일

# 🔥 슬라이드 데이터를 JSON 파일에 저장하는 함수
def save_slides(slides, slide_type):
    data = {"slides": slides, "slide_type": slide_type}
    with open(SLIDES_FILE, 'w') as f:
        json.dump(data, f)

# 🔥 JSON에서 슬라이드 목록 및 유형을 불러오는 함수
def load_slides():
    if os.path.exists(SLIDES_FILE):
        with open(SLIDES_FILE, 'r') as f:
            return json.load(f)
    return {"slides": [], "slide_type": "image"}  # 기본값 반환

# 🔥 응답 데이터를 JSON 파일에 저장하는 함수
def save_answers(user_id, index, answer):
    responses = []
    if os.path.exists(RESPONSES_FILE):
        with open(RESPONSES_FILE, "r") as f:
            responses = json.load(f)

    responses.append({"user_id": user_id, "slide_index": index, "answer": answer})

    with open(RESPONSES_FILE, "w") as f:
        json.dump(responses, f)

# 🔥 서버 시작 시 업로드 및 슬라이드 폴더 초기화
def initialize_folders():
    for folder in [UPLOAD_FOLDER, IMAGE_FOLDER]:
        if os.path.exists(folder):
            shutil.rmtree(folder)  # 기존 폴더 삭제
        os.makedirs(folder, exist_ok=True)  # 새 폴더 생성

initialize_folders()  # 서버 시작 시 폴더 정리 실행

# 📌 각 사용자에게 고유 ID를 할당하는 함수
@app.before_request
def assign_user_id():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())[:8]  # 8자리 UUID 생성하여 세션에 저장

# 📌 메인 페이지 (`index.html`) 표시
@app.route('/')
def index():
    return render_template('index.html')

# 📌 파일 업로드 및 슬라이드 생성 함수
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':  # 사용자가 PDF 파일을 업로드했을 때 실행
        initialize_folders()  # 기존 파일 정리 후 폴더 초기화
        file = request.files['file']  # 업로드된 파일 가져오기
        filename = file.filename  # 파일 이름 가져오기
        filepath = os.path.join(UPLOAD_FOLDER, filename)  # 저장 경로 설정
        file.save(filepath)  # 파일을 지정된 폴더에 저장

        slides = []  # 슬라이드 리스트 초기화
        slide_type = "image"  # 기본 슬라이드 타입 설정

        if filename.endswith('.pdf'):  # PDF 파일인지 확인
            image_paths = convert_pdf_to_images(filepath, IMAGE_FOLDER)  # PDF를 이미지로 변환
            slides = [f"/static/slides/{os.path.basename(path)}" for path in image_paths]  # 웹에서 접근 가능한 이미지 경로 생성
        else:
            return "❌ 지원하지 않는 파일 형식입니다.", 400  # PDF 외 파일 업로드 방지

        save_slides(slides, slide_type)  # 🔥 JSON 파일에 슬라이드 목록 저장

        return redirect(url_for('slide', index=1))  # 첫 번째 슬라이드 페이지로 이동

    return render_template('upload.html')  # 파일 업로드 페이지 렌더링

# 📌 슬라이드를 표시하고 O/X 응답을 받는 기능
@app.route('/slides/<int:index>', methods=['GET', 'POST'])
def slide(index):
    slides_data = load_slides()  # 🔥 JSON에서 슬라이드 목록 불러오기
    slides = slides_data["slides"]
    slide_type = slides_data["slide_type"]
    
    if not slides:
        return "❗ 슬라이드가 준비되지 않았습니다.", 400

    is_first = (index == 1)
    is_last = (index == len(slides))

    if request.method == 'POST':  # 학생이 O/X 응답을 클릭했을 때
        answer = request.form.get('answer')
        user_id = session.get('user_id')
        if answer and not is_first and not is_last:
            save_answers(user_id, index, answer)  # 🔥 응답 데이터 JSON 저장

        return redirect(url_for('slide', index=index + 1))  # 다음 슬라이드로 이동

    return render_template('slide.html',
                           index=index,
                           slide_count=len(slides),
                           image_url=slides[index - 1],  # 현재 슬라이드 이미지 URL
                           is_first=is_first,
                           is_last=is_last)

# 📌 학생들의 응답 결과를 분석하여 통계 제공
@app.route('/stats')
def stats():
    stats_data = {}
    slide_labels = []
    o_counts = []
    x_counts = []

    try:
        if os.path.exists(RESPONSES_FILE):
            with open(RESPONSES_FILE, "r") as f:
                responses = json.load(f)
        else:
            responses = []

        slides_data = load_slides()
        slides = slides_data["slides"]
        last_index = len(slides) - 1

        # 📌 첫 번째(1)와 마지막 슬라이드 제외
        filtered_responses = [r for r in responses if r['slide_index'] > 1 and r['slide_index'] < last_index]

        # 📌 응답 데이터 분석
        grouped = {}
        for r in filtered_responses:
            slide_idx = r["slide_index"]
            answer = r["answer"]
            if slide_idx not in grouped:
                grouped[slide_idx] = {"O": 0, "X": 0}
            grouped[slide_idx][answer] += 1

        stats_data = grouped

        for slide_idx in sorted(stats_data.keys()):
            slide_labels.append(f"Slide {slide_idx}")
            o_counts.append(stats_data[slide_idx].get("O", 0))
            x_counts.append(stats_data[slide_idx].get("X", 0))

    except Exception as e:
        print("❌ 관리자 통계 에러:", e)

    return render_template("stats.html",
                           stats=stats_data,
                           labels=slide_labels,
                           o_counts=o_counts,
                           x_counts=x_counts)

# 📌 Flask 서버 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Flask 애플리케이션 실행
