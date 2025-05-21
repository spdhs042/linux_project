from flask import Flask, render_template, request, redirect, url_for, session
import csv
import uuid
import os
import pandas as pd
from utils.convert_pdf_to_images import convert_pdf_to_images

app = Flask(__name__)
app.secret_key = 'your-secret-key'

UPLOAD_FOLDER = 'uploads'
IMAGE_FOLDER = 'static/slides'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)

@app.before_request
def assign_user_id():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())[:8]

@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        slides = []
        slide_type = ''

        if filename.endswith('.pdf'):  # PPT 업로드 기능 제거
            image_paths = convert_pdf_to_images(filepath, IMAGE_FOLDER)
            slides = [f"/{path}" for path in image_paths]
            slide_type = 'image'
        else:
            return "지원하지 않는 파일 형식입니다."

        session['slides'] = slides
        session['slide_type'] = slide_type
        session['answers'] = []
        session['current_idx'] = 0

        return redirect(url_for('slide'))

    return render_template('upload.html')

@app.route('/slide', methods=['GET', 'POST'])
def slide():
    slides = session.get('slides')
    slide_type = session.get('slide_type')
    answers = session.get('answers')
    idx = session.get('current_idx', 0)

    if not slides:
        return redirect(url_for('upload'))

    if request.method == 'POST':
        answer = request.form.get('answer')
        if 0 < idx < len(slides) - 1 and answer:
            user_id = session.get('user_id')
            with open('responses.csv', 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([user_id, idx, answer])
            answers.append(answer)
        session['answers'] = answers
        session['current_idx'] = idx + 1
        return redirect(url_for('slide'))

    if idx >= len(slides):
        return redirect(url_for('admin_stats'))  # 결과 페이지 대신 관리자 통계 페이지로 이동

    is_first = (idx == 0)
    is_last = (idx == len(slides) - 1)

    image_url = slides[idx] if slide_type == 'image' else None
    return render_template('slide.html', idx=idx+1, total=len(slides), image_url=image_url, is_first=is_first, is_last=is_last)

@app.route('/stats')
def admin_stats():
    stats = {}
    slide_labels = []
    o_counts = []
    x_counts = []

    try:
        df = pd.read_csv('responses.csv', names=['user_id', 'slide_index', 'answer'])
        df = df[df['slide_index'] != 0]

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

@app.route('/result')
def result():
    return redirect(url_for('stats'))  # 결과 페이지 대신 관리자 통계 페이지로 이동

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
