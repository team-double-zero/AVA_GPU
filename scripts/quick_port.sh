#!/bin/bash

# 빠른 포트 변경 및 재시작 스크립트

if [ -z "$1" ]; then
    echo "사용법: $0 <포트번호>"
    echo "예시: $0 8080"
    exit 1
fi

NEW_PORT=$1

# 현재 디렉토리를 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

echo "🔄 포트를 $NEW_PORT로 변경하고 서비스를 재시작합니다..."

# 포트 설정
sed -i.bak "s/^PORT=.*/PORT=$NEW_PORT/" config.env 2>/dev/null || echo "PORT=$NEW_PORT" > config.env

# 기존 컨테이너 중지
docker compose down 2>/dev/null

# 새 포트로 시작
docker compose up -d

echo "⏳ 서비스 시작 대기 중..."
sleep 10

# 헬스체크
if curl -f http://localhost:$NEW_PORT/health &> /dev/null; then
    echo "✅ 서비스가 포트 $NEW_PORT에서 시작되었습니다!"
    echo "🌐 접속: http://localhost:$NEW_PORT"
else
    echo "⚠️  서비스 시작을 확인해주세요: http://localhost:$NEW_PORT/health"
fi
