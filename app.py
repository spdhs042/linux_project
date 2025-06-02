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

# 슬라이드 데이터를 JSON 파일에 저장하는 함수
def save_slides(slides, slide_type):
    data = {"slides": slides, "slide_type": slide_type}
    with open(SLIDES_FILE, 'w') as f:
        json.dump(data, f)

# JSON에서 슬라이드 목록 및 유형을 불러오는 함수
def load_slides():
    if os.path.exists(SLIDES_FILE):
        with open(SLIDES_FILE, 'r') as f:
            return json.load(f)
    return {"slides": [], "slide_type": "image"}  # 기본값 반환


# 서버 시작 시 업로드 및 슬라이드 폴더 초기화
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

              # 📌 새로운 PDF 업로드 시 responses.json 초기화
            with open(RESPONSES_FILE, "w") as f:
                json.dump({}, f)  # JSON 파일을 빈 리스트로 초기화
        else:
            return "❌ 지원하지 않는 파일 형식입니다.", 400  # PDF 외 파일 업로드 방지

        save_slides(slides, slide_type)  # JSON 파일에 슬라이드 목록 저장

        return redirect(url_for('stats'))  # 첫 번째 슬라이드 페이지로 동

    return render_template('upload.html')  # 파일 업로드 페이지 렌더링

# 📌 슬라이드를 표시하고 O/X 응답을 받는 기능
@app.route('/slides/<int:index>', methods=['GET', 'POST'])
def slide(index):
    slides_data = load_slides()  # JSON에서 슬라이드 목록 불러오기
    slides = slides_data["slides"]
    slide_type = slides_data["slide_type"]
    
    if not slides:
        return "❗ 슬라이드가 준비되지 않았습니다.", 400

    is_first = (index == 1)
    is_last = (index == len(slides))

    # POST 요청: 응답 저장
    if request.method == 'POST':
        answer = request.form.get('answer')
        if 1 < index < len(slides)  and answer:
            user_id = session.get('user_id')
            slide_index = str(index)

            # responses.json 파일 불러오기
            if os.path.exists(RESPONSES_FILE):
                with open(RESPONSES_FILE, 'r') as f:
                    data = json.load(f)
            else:
                data = {}

            # 사용자별 응답 딕셔너리 초기화
            if user_id not in data:
                data[user_id] = {}

            # 해당 슬라이드 응답 덮어쓰기
            data[user_id][slide_index] = answer

            # 파일에 다시 저장
            with open(RESPONSES_FILE, 'w') as f:
                json.dump(data, f, indent=2)

            # 세션에도 추가
            answers = session.get('answers', [])
            answers.append(answer)
            session['answers'] = answers
            session['current_idx'] = index + 1

            return redirect(url_for('slide',index=index+1))

    return render_template('slide.html',
                           index=index,
                           slide_count=len(slides),
                           image_url=slides[index - 1],  # 현재 슬라이드 이미지 URL
                           is_first=is_first,
                           is_last=is_last)

# 📌 학생들의 응답 결과를 분석하여 통계 제공
@app.route('/stats')
def stats():
    stats_data = {}  #슬라이드 통계를 저장할 딕셔너리
    slide_labels = [] # 슬라이즈 라벨 목록
    o_counts = [] # 'o'선택 횟수 목록
    x_counts = [] # 'x'선택 횟수 목록

    try:
        if os.path.exists(RESPONSES_FILE):   # 응답 데이터 파일이 존재하는지 확인
            with open(RESPONSES_FILE, "r") as f:  # 파일을 읽기 모드로 열기
                responses = json.load(f)  # JSON 데이터를 파싱하여 딕셔너리에 저장 

            slides_data = load_slides() # 슬라이드 데이터 불러오기
            slides = slides_data["slides"] # 슬라이드 리스트 가져오기
            last_index = len(slides) # 마지막 슬라이드의 인덱스 계산


            grouped = {} # 통계를 저장할 딕셔너리

 # 사용자별 응답을 반복
            for user_id, answers in responses.items():
                for slide_idx_str, answer in answers.items():
                    slide_idx = int(slide_idx_str) # 문자열 인덱스를 정수로 변환

                    if slide_idx == 1 or slide_idx == last_index:
                        continue  # 첫/마지막 슬라이드는 통계 제외

                    if slide_idx not in grouped: # 해당 슬라이드가 통계에 없으면 초기화
                        grouped[slide_idx] = {"O": 0, "X": 0}
                    grouped[slide_idx][answer] += 1 # 선택된 답변 수 증가

        stats_data = grouped # 통계 데이터를 업데이트

 # 슬라이드 인덱스를 정렬하여 통계 데이터를 리스트로 변환
        for slide_idx in sorted(stats_data.keys()):
            slide_labels.append(f"Slide {slide_idx}") # 슬라이드 라벨 추가
            o_counts.append(stats_data[slide_idx].get("O", 0))  # "O" 선택 수 추가
            x_counts.append(stats_data[slide_idx].get("X", 0)) # "X" 선택 수 추가

    except Exception as e: # 예외 발생 시 오류 메시지 출력
        print("❌ 관리자 통계 에러:", e)

    return render_template("stats.html",
                           stats=stats_data,
                           labels=slide_labels,
                           o_counts=o_counts,
                           x_counts=x_counts)

# 📌 Flask 서버 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Flask 애플리케이션 실행
