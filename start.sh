#!/bin/bash

# Qwen Image Generator API 시작 스크립트

echo "🚀 Qwen Image Generator API 시작 중..."

# GPU 확인
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU 감지됨"
    nvidia-smi
else
    echo "⚠️  경고: NVIDIA GPU가 감지되지 않았습니다. CPU 모드로 실행됩니다."
fi

# Docker 및 Docker Compose 확인
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되지 않았습니다. setup_vastai.sh를 실행해주세요."
    exit 1
fi

# Docker 데몬 상태 확인
echo "🔍 Docker 데몬 상태 확인 중..."
if ! docker ps &> /dev/null; then
    echo "❌ Docker 데몬이 실행되지 않고 있습니다."
    echo "해결 방법:"
    echo "1. 서비스 시작: sudo systemctl start docker"
    echo "2. 권한 문제: newgrp docker 또는 sudo usermod -aG docker \$USER"
    echo "3. vast.ai 초기 설정: ./setup_vastai.sh"
    exit 1
fi
echo "✅ Docker 데몬이 정상적으로 실행 중입니다"

# Docker Compose 명령어 확인 (최신 버전 우선)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
    echo "✅ Docker Compose (v2) 확인됨"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
    echo "✅ Docker Compose (v1) 확인됨"
else
    echo "❌ Docker Compose가 설치되지 않았습니다. Docker Compose를 설치해주세요."
    exit 1
fi

# 기존 컨테이너 정리 (선택사항)
read -p "기존 컨테이너를 정리하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 기존 컨테이너 정리 중..."
    $DOCKER_COMPOSE_CMD down -v
fi

# 컨테이너 빌드 및 실행
echo "🏗️  컨테이너 빌드 중..."
$DOCKER_COMPOSE_CMD build

echo "🚀 서비스 시작 중..."
$DOCKER_COMPOSE_CMD up -d

# 서비스 상태 확인
echo "⏳ 서비스 시작 대기 중..."
sleep 10

# 헬스 체크
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:5000/health &> /dev/null; then
        echo "✅ 서비스가 성공적으로 시작되었습니다!"
        echo "🌐 API 주소: http://localhost:5000"
        echo "📊 헬스체크: http://localhost:5000/health"
        echo "📝 API 문서는 README.md를 참조하세요."
        
        # 서비스 상태 표시
        echo ""
        echo "📈 현재 서비스 상태:"
        curl -s http://localhost:5000/health | python -m json.tool
        
        exit 0
    fi
    
    echo "⏳ 서비스 시작 대기 중... ($attempt/$max_attempts)"
    sleep 5
    ((attempt++))
done

echo "❌ 서비스 시작에 실패했습니다. 로그를 확인해주세요:"
echo "$DOCKER_COMPOSE_CMD logs -f"

exit 1
