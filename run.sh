#!/bin/bash
fuser -k 5000/tcp >/dev/null 2>&1

echo "🚀 Flask 서버 실행 중..."
python3 app.py &

# 서버가 완전히 뜰 때까지 기다림 (3초)
sleep 3

echo "🌍 ngrok 연결 중..."
ngrok http 5000
