from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from utils.convert_pdf_to_images import convert_pdf_to_images
import os

# Flask 애플리케이션 초기화
app = Flask(__name__)
app.secret_key = 'your-secret-key'  # 세션 관리를 위한 secret key 설정

# 파일 업로드 및 변환된 이미지 저장 폴더 설정
UPLOAD_FOLDER = 'uploads'
IMAGE_FOLDER = 'static/slides'

# 폴더가 없으면 생성
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# 📌 파일 업로드 및 변환 처리
@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':  # 사용자가 파일을 업로드했을 때
        file = request.files['file']  # 업로드된 파일 가져오기
        filename = secure_filename(file.filename)  # 파일 이름을 안전하게 처리
        filepath = os.path.join(UPLOAD_FOLDER, filename)  # 저장 경로 설정
        file.save(filepath)  # 파일 저장

        # PDF 파일이라면 이미지로 변환
        if filename.endswith('.pdf'):
            image_paths = convert_pdf_to_images(filepath, IMAGE_FOLDER)  # 변환 실행
            slides = [f"/{path}" for path in image_paths]  # 웹에서 접근 가능한 이미지 경로 생성
        else:
            return "지원하지 않는 파일 형식입니다."  # PDF 외의 파일 업로드 제한

        # 세션을 활용해 슬라이드 목록 및 초기 상태 저장
        session['slides'] = slides
        session['answers'] = []  # 학생들의 O/X 응답 저장 리스트
        session['current_idx'] = 0  # 현재 슬라이드 인덱스 초기화
        return redirect(url_for('slide'))  # 슬라이드 페이지로 이동

    return render_template('upload.html')  # 파일 업로드 페이지 렌더링

# 📌 O/X 응답을 받아 슬라이드를 표시하는 기능
@app.route('/slide', methods=['GET', 'POST'])
def slide():
    slides = session.get('slides')  # 세션에서 슬라이드 목록 가져오기
    answers = session.get('answers')  # 학생 응답 리스트 가져오기
    idx = session.get('current_idx', 0)  # 현재 슬라이드 번호 가져오기

    if not slides:
        return redirect(url_for('upload'))  # 슬라이드가 없으면 업로드 페이지로 이동

    if request.method == 'POST':  # 학생이 O/X 응답을 클릭했을 때
        answer = request.form.get('answer')  # 응답 값 가져오기
        if answer:  # 응답이 있으면 리스트에 추가
            answers.append(answer)
            session['answers'] = answers  # 세션에 응답 저장
            session['current_idx'] = idx + 1  # 다음 슬라이드로 이동
        return redirect(url_for('slide'))  # 새 슬라이드를 표시

    if idx >= len(slides):  # 모든 슬라이드를 다 봤으면 결과 페이지로 이동
        return redirect(url_for('result'))

    # 현재 슬라이드 이미지 URL 가져오기
    image_url = slides[idx]
    is_last = (idx == len(slides) - 1)  # 마지막 슬라이드 여부 확인

    return render_template('slide.html',
                           idx=idx+1,
                           total=len(slides),
                           image_url=image_url,
                           is_last=is_last)  # 슬라이드 페이지 렌더링

# 📌 학생들의 응답 결과를 분석하여 점수 계산
@app.route('/result')
def result():
    slides = session.get('slides', [])  # 세션에서 슬라이드 목록 가져오기
    answers = session.get('answers', [])  # 학생 응답 리스트 가져오기

    # O 선택 비율을 백분율로 계산 (슬라이드 수 대비 O 선택 수)
    score = answers.count('O') / len(slides) * 100 if slides else 0

    return render_template('result.html',
                           slides=slides,
                           answers=answers,
                           score=score)  # 결과 페이지 렌더링

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
