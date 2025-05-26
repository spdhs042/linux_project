echo "🔧 [1/3]ngrok 설치 중 ..."
snap install ngrok
echo "🔐 [2/3] ngrok 인증 토큰 등록 중..."
ngrok config add-authtoken 2xSBFg6HICtK0Ghvpmt6T0zkA4Y_6DkrBYZ8MgubVEmeBpPom

echo "✅ [3/3] run.sh 실행 권한 부여 중..."
chmod +x run.sh

echo "🎉 초기 설정 완료! 이제 다음 명령어로 실행하세요:"
echo "./run.sh"
