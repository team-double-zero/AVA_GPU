#!/bin/bash

# vast.ai 환경용 Docker 데몬 시작 스크립트

echo "🐳 Docker 데몬 시작 스크립트"

# 이미 실행 중인지 확인
if docker ps &> /dev/null; then
    echo "✅ Docker 데몬이 이미 실행 중입니다"
    docker version
    exit 0
fi

echo "🚀 Docker 데몬을 시작합니다..."

# 기존 Docker 데몬 프로세스 종료 (있는 경우)
sudo pkill -f dockerd 2>/dev/null || true

# Docker 데몬 시작
echo "Docker 데몬 백그라운드 시작 중..."
sudo dockerd --host=unix:///var/run/docker.sock --host=tcp://127.0.0.1:2376 &> /tmp/dockerd.log &

# 데몬 PID 저장
DOCKERD_PID=$!
echo "Docker 데몬 PID: $DOCKERD_PID"

# Docker 데몬이 준비될 때까지 대기
echo "Docker 데몬 준비 대기 중..."
for i in {1..60}; do
    if docker ps &> /dev/null; then
        echo "✅ Docker 데몬이 성공적으로 시작되었습니다!"
        docker version
        
        # Docker Compose 테스트
        if docker compose version &> /dev/null; then
            echo "✅ Docker Compose도 사용 가능합니다"
            docker compose version
        fi
        
        echo ""
        echo "🎉 이제 ./start.sh를 실행할 수 있습니다!"
        exit 0
    fi
    
    if [ $((i % 10)) -eq 0 ]; then
        echo "대기 중... ($i/60초)"
    fi
    sleep 1
done

echo "❌ Docker 데몬 시작에 실패했습니다"
echo ""
echo "로그 확인:"
tail -20 /tmp/dockerd.log

echo ""
echo "문제 해결 방법:"
echo "1. 권한 확인: sudo docker ps"
echo "2. 수동 시작: sudo dockerd"
echo "3. 로그 전체 보기: cat /tmp/dockerd.log"

exit 1
