# linux_project
리눅스실습및프로젝트 미니 프로젝트 과제

목표 : 리눅스에 웹서버를 둔 웹사이트를 제작

웹사이트 설명 :

1. 교수님이 pdf 업로드
2. pdf를 이미지로 변환, 각 슬라이드에 대해 학생들이 o, x 버튼을 클릭하여 이해정도 응답
3. 마지막 슬라이드에서 결과보기를 클릭 시, 학생들의 o, x 응답을 각 슬라이드 별로 통계내어 화면에 표시


현재 디렉토리 구조
linux_project/
├── app.py                 # Flask 애플리케이션 코드
├── uploads/               # 업로드된 PDF 파일 저장 폴더
├── static/
│   ├── slides/            # 변환된 이미지 파일 저장 폴더
│   ├── styles.css         # CSS 스타일시트 
├── templates/
│   ├── index.html         # 메인 페이지 : 학생에게 보여주는 페이지(수정 필요)
│   ├── upload.html        # 파일 업로드 페이지
│   ├── slide.html         # 슬라이드 보기 페이지
│   ├── stats.html         # 관리자 통계 페이지
├── responses.csv          # O/X 응답 데이터를 저장하는 CSV 파일(실행 시 생성됨) -> 현재 json 파일로 임시 변경됨
├── utils/
│   ├── convert_pdf_to_images.py  # PDF → 이미지 변환 기능
├── requirements.txt       # 필요한 라이브러리 목록
├── run.sh                 # 다중접속
├── setup.sh               # 실행에 필요한 setup
└── venv/                  # 가상환경 폴더



로컬에 프로젝트 복사 리눅스 명령어
git clone https://github.com/spdhs042/linux_project.git
source venv/bin/activate
cd linux_project
pip install -r requirements.txt
python app.py



동시접속 테스트 방법 : 가상머신에서 프로젝트 디렉토리 안으로 들어와서 아래 명령어 실행
bash setup.sh
./run.sh
