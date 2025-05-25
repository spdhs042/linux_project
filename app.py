
from flask import Flask, render_template, request, redirect, url_for, session 
import csv #csv 파일 처리 모듈
import uuid #사용자 고유 ID 생성 모듈
import os #파일 및 폴더 관리 모듈
import pandas as pd
from utils.convert_pdf_to_images import convert_pdf_to_images

# Flask 애플리케이션 초기화
app = Flask(__name__)
app.secret_key = 'your-secret-key'  # 세션 관리를 위한 secret key 설정

# 파일 업로드 및 변환된 이미지 저장 폴더 설정
UPLOAD_FOLDER = 'uploads'
IMAGE_FOLDER = 'static/slides'

# 폴더가 없으면 생성
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# 📌 각 사용자에게 고유 ID를 할당하는 함수
@app.before_request
def assign_user_id():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())[:8]  # 8자리 UUID 생성

 # 📌 index.html을 기본 페이지로
@app.route('/')
def index():
    return render_template('index.html')

# 📌 파일 업로드 및 슬라이드 생성 함수
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':  # 사용자가 파일을 업로드했을 때 실행
        file = request.files['file']  # 업로드된 파일 가져오기
        filename = file.filename  # 파일 이름 가져오기
        filepath = os.path.join(UPLOAD_FOLDER, filename)  # 파일 저장 경로 설정
        file.save(filepath)  # 파일을 지정된 경로에 저장

        # 📌 responses.csv 초기화 (파일 업로드 시마다 새롭게 생성됨)
        with open('responses.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['user_id', 'slide_index', 'answer'])  # CSV 파일 헤더 추가 (사용자 ID, 슬라이드 번호, 응답)

        slides = []  # 슬라이드 리스트 초기화
        slide_type = ''  # 슬라이드 타입 ('image' 지정 예정)

        if filename.endswith('.pdf'):  # 업로드된 파일이 PDF인지 확인
            image_paths = convert_pdf_to_images(filepath, IMAGE_FOLDER)  # PDF를 이미지로 변환
            slides = [f"/{path}" for path in image_paths]  # 변환된 이미지 경로 생성 (웹에서 접근 가능하게)
            slide_type = 'image'  # 슬라이드 타입을 'image'로 설정
        else:
            return "지원하지 않는 파일 형식입니다."  # PDF 외 파일 업로드 방지

        # 📌 세션을 활용해 슬라이드 목록 및 초기 상태 저장
        session['slides'] = slides  # 변환된 슬라이드 이미지 목록 저장
        session['slide_type'] = slide_type  # 슬라이드 타입 저장 ('image')
        session['answers'] = []  # 학생들의 O/X 응답을 저장할 리스트 초기화
        session['current_idx'] = 0  # 현재 슬라이드 인덱스 초기화

        return redirect(url_for('slide'))  # 슬라이드 페이지로 이동

    return render_template('upload.html')  # 파일 업로드 페이지 렌더링

    
# 📌 O/X 응답을 받아 슬라이드를 표시하는 기능
@app.route('/slide', methods=['GET', 'POST'])
def slide():
    slides = session.get('slides')  # 세션에서 슬라이드 목록 가져오기
    slide_type = session.get('slide_type')  # 슬라이드 타입 (image)
    answers = session.get('answers')  # 학생 응답 리스트 가져오기
    idx = session.get('current_idx', 0)  # 현재 슬라이드 번호 가져오기

    if not slides:
        return redirect(url_for('upload'))  # 슬라이드가 없으면 업로드 페이지로 이동

    if request.method == 'POST':  # 학생이 O/X 응답을 클릭했을 때
        answer = request.form.get('answer')  # 응답 값 가져오기
        if 0 < idx < len(slides) - 1 and answer:  # 첫 페이지 제외하고 응답 저장
            user_id = session.get('user_id')  # 사용자 ID 가져오기
            with open('responses.csv', 'a', newline='') as f:  # CSV 파일에 응답 저장
                writer = csv.writer(f)
                writer.writerow([user_id, idx, answer])  # 사용자 ID, 슬라이드 번호, 응답 저장
            answers.append(answer)

        session['answers'] = answers  # 세션에 응답 저장
        session['current_idx'] = idx + 1  # 다음 슬라이드로 이동
        return redirect(url_for('slide'))  # 새 슬라이드를 표시

    if idx >= len(slides):  # 모든 슬라이드를 다 봤으면 결과 페이지로 이동
        return redirect(url_for('stats'))  # 관리자 통계 페이지로 이동

    is_first = (idx == 0)  # 첫 슬라이드 여부 확인
    is_last = (idx == len(slides) - 1)  # 마지막 슬라이드 여부 확인

    image_url = slides[idx]  # 현재 슬라이드 이미지 URL 가져오기
    return render_template('slide.html',  # 📌 렌더링할 HTML 파일 (슬라이드 화면)
                           idx=idx+1,
                           total=len(slides),
                           image_url=image_url,
                           is_first=is_first,
                           is_last=is_last)

# 📌 학생들의 응답 결과를 분석하여 통계 제공
@app.route('/stats')
def admin_stats():
    stats = {}
    slide_labels = []
    o_counts = []
    x_counts = []

    try:
        df = pd.read_csv('responses.csv', names=['user_id', 'slide_index', 'answer'])

        slides = session.get('slides', [])
        last_index = len(slides) - 1

        # 📌 첫 번째(0)와 마지막 슬라이드 제외
        df = df[(df['slide_index'] != 0) & (df['slide_index'] != last_index)]

        grouped = df.groupby(['slide_index', 'answer']).size().unstack(fill_value=0)
        stats = grouped.to_dict(orient='index')

        for slide_idx in sorted(stats.keys()):
            slide_labels.append(f"Slide {slide_idx}")
            o_counts.append(stats[slide_idx].get('O', 0))
            x_counts.append(stats[slide_idx].get('X', 0))

    except Exception as e:
        print("❌ 관리자 통계 에러:", e)

    return render_template("stats.html",
                           stats=stats,
                           labels=slide_labels,
                           o_counts=o_counts,
                           x_counts=x_counts)


# 📌 Flask 서버 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
