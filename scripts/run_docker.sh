#!/bin/bash

# Docker 빌드 및 실행 스크립트 (vast.ai 환경용)

echo "🐳 Qwen Image Generator Docker 실행"

# 현재 디렉토리를 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

# 현재 설정된 포트 확인
current_port=$(grep "^PORT=" config.env 2>/dev/null | cut -d'=' -f2)
if [ -z "$current_port" ]; then
    current_port="5000"
fi

echo "📌 현재 설정된 포트: $current_port"
echo "💡 포트 변경: ./scripts/set_port.sh"

# Docker 상태 확인
if ! docker ps &> /dev/null; then
    echo "❌ Docker가 실행되지 않고 있습니다."
    echo "vast.ai에서는 일반적으로 Docker가 이미 실행 중이어야 합니다."
    exit 1
fi

echo "✅ Docker가 실행 중입니다"

# 사용자 선택
echo ""
echo "실행할 작업을 선택하세요:"
echo "1) 빌드 및 실행 (권장)"
echo "2) 실행만 (이미 빌드된 경우)"
echo "3) 빌드만"
echo "4) 중지"
echo "5) 로그 보기"
echo "6) 상태 확인"

read -p "선택 (1-6): " choice

case $choice in
    1)
        echo "🏗️  이미지 빌드 및 컨테이너 실행 중..."
        docker compose up --build -d
        ;;
    2)
        echo "🚀 컨테이너 실행 중..."
        docker compose up -d
        ;;
    3)
        echo "🏗️  이미지 빌드 중..."
        docker compose build
        ;;
    4)
        echo "⏹️  컨테이너 중지 중..."
        docker compose down
        echo "✅ 컨테이너가 중지되었습니다"
        exit 0
        ;;
    5)
        echo "📋 로그 보기..."
        docker compose logs -f
        exit 0
        ;;
    6)
        echo "📊 상태 확인..."
        docker compose ps
        echo ""
        echo "🔍 헬스체크..."
        sleep 2
        curl -s http://localhost:$current_port/health | python3 -m json.tool 2>/dev/null || echo "서비스가 아직 준비되지 않았습니다."
        exit 0
        ;;
    *)
        echo "❌ 잘못된 선택입니다."
        exit 1
        ;;
esac

# 서비스 시작 확인
if [ "$choice" = "1" ] || [ "$choice" = "2" ]; then
    echo ""
    echo "⏳ 서비스 시작 대기 중..."
    
    # 최대 60초 대기
    for i in {1..12}; do
        if curl -f http://localhost:$current_port/health &> /dev/null; then
            echo "✅ 서비스가 성공적으로 시작되었습니다!"
            echo ""
            echo "🌐 서비스 주소:"
            echo "  - API: http://localhost:$current_port"
            echo "  - 헬스체크: http://localhost:$current_port/health"
            echo "  - 모델 정보: http://localhost:$current_port/model-info"
            echo ""
            echo "📝 사용법:"
            echo "  curl -X POST http://localhost:$current_port/generate \\"
            echo "    -H 'Content-Type: application/json' \\"
            echo "    -d '{\"prompt\": \"a beautiful sunset\"}'"
            echo ""
            echo "📊 현재 상태:"
            curl -s http://localhost:$current_port/health | python3 -m json.tool 2>/dev/null
            exit 0
        fi
        
        echo "대기 중... ($i/12)"
        sleep 5
    done
    
    echo "⚠️  서비스 시작에 시간이 걸리고 있습니다."
    echo "로그를 확인하세요: docker compose logs -f"
fi

echo "✅ 작업 완료!"
