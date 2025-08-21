#!/bin/bash

# 빠른 시작 스크립트 - Docker Compose 권한 문제 해결
echo "🚀 Qwen Image Generator - 빠른 시작"

# Docker Compose 명령어 확인 및 설정
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
    echo "✅ Docker Compose v2 사용"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
    echo "✅ Docker Compose v1 사용"
else
    echo "❌ Docker Compose를 찾을 수 없습니다."
    exit 1
fi

echo "명령어: $DOCKER_COMPOSE_CMD"
echo ""

# 사용자 선택
echo "원하는 작업을 선택하세요:"
echo "1) 빌드 및 시작"
echo "2) 시작만"
echo "3) 중지"
echo "4) 로그 보기"
echo "5) 상태 확인"

read -p "선택 (1-5): " choice

case $choice in
    1)
        echo "🏗️  빌드 및 시작 중..."
        $DOCKER_COMPOSE_CMD up --build -d
        ;;
    2)
        echo "🚀 시작 중..."
        $DOCKER_COMPOSE_CMD up -d
        ;;
    3)
        echo "⏹️  중지 중..."
        $DOCKER_COMPOSE_CMD down
        ;;
    4)
        echo "📋 로그 보기..."
        $DOCKER_COMPOSE_CMD logs -f
        ;;
    5)
        echo "📊 상태 확인..."
        $DOCKER_COMPOSE_CMD ps
        echo ""
        echo "헬스체크:"
        curl -s http://localhost:5000/health | python -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2, ensure_ascii=False))" 2>/dev/null || echo "서비스가 아직 준비되지 않았습니다."
        ;;
    *)
        echo "❌ 잘못된 선택입니다."
        exit 1
        ;;
esac

echo "✅ 완료!"
