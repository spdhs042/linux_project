
# 📌 Flask 및 필요한 모듈 import
from flask import Flask, render_template, request, redirect, url_for, session
import csv  # CSV 파일 처리 모듈
import uuid  # 사용자 고유 ID 생성 모듈
import os  # 파일 및 폴더 관리 모듈
import shutil  # 폴더 정리 모듈
import pandas as pd  # 데이터 분석을 위한 pandas 모듈
from utils.convert_pdf_to_images import convert_pdf_to_images  # PDF를 이미지로 변환하는 유틸 함수

# 📌 Flask 애플리케이션 초기화
app = Flask(__name__)
app.secret_key = 'your-secret-key'  # 세션 관리를 위한 secret key 설정

# 📌 파일 저장 폴더 설정
UPLOAD_FOLDER = 'uploads'  # PDF 파일 업로드 폴더
IMAGE_FOLDER = 'static/slides'  # 변환된 슬라이드 이미지 저장 폴더

# 📌 서버 시작 시 업로드 및 슬라이드 폴더 초기화 함수
def initialize_folders():
    for folder in [UPLOAD_FOLDER, IMAGE_FOLDER]:
        if os.path.exists(folder):
            shutil.rmtree(folder)  # 기존 폴더 삭제
        os.makedirs(folder, exist_ok=True)  # 새 폴더 생성

initialize_folders()  # 서버 시작 시 폴더 정리 실행

# 📌 각 사용자에게 고유한 ID를 부여하는 함수
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

        # 📌 responses.csv 초기화 (파일 업로드 시마다 새롭게 생성됨)
        with open('responses.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['user_id', 'slide_index', 'answer'])  # CSV 파일 헤더 추가

        slides = []  # 슬라이드 리스트 초기화
        slide_type = ''  # 슬라이드 타입 ('image' 지정 예정)

        if filename.endswith('.pdf'):  # PDF 파일인지 확인
            image_paths = convert_pdf_to_images(filepath, IMAGE_FOLDER)  # PDF를 이미지로 변환
            slides = [f"/{path}" for path in image_paths]  # 웹에서 접근 가능한 이미지 경로 생성
            slide_type = 'image'  # 슬라이드 타입을 'image'로 설정
        else:
            return "❌ 지원하지 않는 파일 형식입니다.", 400  # PDF 외 파일 업로드 방지

        # 📌 세션을 활용해 슬라이드 데이터 저장
        session['slides'] = slides  # 변환된 슬라이드 이미지 목록 저장
        session['slide_type'] = slide_type  # 슬라이드 타입 저장 ('image')
        session['answers'] = []  # 학생들의 O/X 응답을 저장할 리스트 초기화
        session['current_idx'] = 0  # 현재 슬라이드 인덱스 초기화

        return redirect(url_for('slide', index=1))  # 첫 번째 슬라이드 페이지로 이동

    return render_template('upload.html')  # 파일 업로드 페이지 렌더링

# 📌 슬라이드를 표시하고 O/X 응답을 받는 기능
@app.route('/slides/<int:index>', methods=['GET', 'POST'])
def slide(index):
    slides = session.get('slides', [])  # 세션에서 슬라이드 목록 가져오기
    slide_type = session.get('slide_type', 'image')
    answers = session.get('answers', [])

    if not slides or len(slides) == 0:  # 슬라이드가 없을 경우 안내 메시지 표시
        return "❗ 슬라이드가 준비되지 않았습니다. 교수님께 문의하세요.", 400

    is_first = (index == 1)  # 첫 슬라이드 여부 확인
    is_last = (index == len(slides))  # 마지막 슬라이드 여부 확인

    if request.method == 'POST':  # 학생이 O/X 응답을 클릭했을 때
        answer = request.form.get('answer')  # 응답 값 가져오기
        user_id = session.get('user_id')  # 사용자 ID 가져오기
        if answer and not is_first and not is_last:  # 첫 번째, 마지막 슬라이드는 응답 저장 제외
            with open('responses.csv', 'a', newline='') as f:  # 응답을 CSV 파일에 저장
                writer = csv.writer(f)
                writer.writerow([user_id, index, answer])  # 사용자 ID, 슬라이드 번호, 응답 기록
            answers.append(answer)
            session['answers'] = answers  # 세션에 응답 저장

        return redirect(url_for('slide', index=index + 1))  # 다음 슬라이드로 이동

    return render_template('slide.html',
                           index=index,
                           slide_count=len(slides),
                           image_url=slides[index - 1],  # 현재 슬라이드 이미지 URL 가져오기
                           is_first=is_first,
                           is_last=is_last)

# 📌 학생들의 응답 결과를 분석하여 통계를 제공하는 기능
@app.route('/stats')
def admin_stats():
    stats = {}  # O/X 응답 통계를 저장할 딕셔너리
    slide_labels = []  # 슬라이드 번호 목록
    o_counts = []  # O 응답 개수 저장 리스트
    x_counts = []  # X 응답 개수 저장 리스트

    try:
        df = pd.read_csv('responses.csv', names=['user_id', 'slide_index', 'answer'])  # CSV 파일 읽기
        slides = session.get('slides', [])  # 슬라이드 목록 가져오기
        last_index = len(slides) - 1  # 마지막 슬라이드 인덱스 확인

        # 📌 첫 번째(0)와 마지막 슬라이드는 제외
        df = df[(df['slide_index'] != 0) & (df['slide_index'] != last_index)]

        grouped = df.groupby(['slide_index', 'answer']).size().unstack(fill_value=0)  # 응답 개수 그룹화
        stats = grouped.to_dict(orient='index')  # 딕셔너리 형태로 변환

        # 📌 슬라이드별 O/X 개수 정리
        for slide_idx in sorted(stats.keys()):
            slide_labels.append(f"Slide {slide_idx}")
            o_counts.append(stats[slide_idx].get('O', 0))  # O 응답 개수 저장
            x_counts.append(stats[slide_idx].get('X', 0))  # X 응답 개수 저장

    except Exception as e:
        print("❌ 관리자 통계 에러:", e)  # 오류 발생 시 출력

    return render_template("stats.html",
                           stats=stats,
                           labels=slide_labels,
                           o_counts=o_counts,
                           x_counts=x_counts)

# 📌 Flask 서버 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # Flask 애플리케이션 실행
