#!/bin/bash

# vast.ai 포트 설정 스크립트

echo "🔧 Qwen Image Generator 포트 설정"

# 현재 디렉토리를 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

# 현재 설정된 포트 확인
current_port=$(grep "^PORT=" config.env 2>/dev/null | cut -d'=' -f2)
if [ -z "$current_port" ]; then
    current_port="5000"
fi

echo "현재 설정된 포트: $current_port"
echo ""

# 사용자로부터 새 포트 입력받기
while true; do
    read -p "새로운 포트 번호를 입력하세요 (1024-65535, 엔터=기본값 유지): " new_port
    
    # 엔터만 눌렀을 경우 기본값 유지
    if [ -z "$new_port" ]; then
        new_port=$current_port
        echo "기본값 유지: $new_port"
        break
    fi
    
    # 숫자인지 확인
    if ! [[ "$new_port" =~ ^[0-9]+$ ]]; then
        echo "❌ 숫자만 입력해주세요."
        continue
    fi
    
    # 포트 범위 확인
    if [ "$new_port" -lt 1024 ] || [ "$new_port" -gt 65535 ]; then
        echo "❌ 포트 번호는 1024-65535 범위여야 합니다."
        continue
    fi
    
    break
done

echo ""
echo "포트를 $new_port(으)로 설정합니다..."

# config.env 파일에서 포트 업데이트
if [ -f "config.env" ]; then
    # 기존 PORT 라인 교체
    if grep -q "^PORT=" config.env; then
        sed -i.bak "s/^PORT=.*/PORT=$new_port/" config.env
    else
        # PORT 라인이 없으면 추가
        echo "PORT=$new_port" >> config.env
    fi
else
    echo "❌ config.env 파일을 찾을 수 없습니다."
    exit 1
fi

echo "✅ 포트가 $new_port(으)로 설정되었습니다."
echo ""

# Docker 컨테이너가 실행 중인지 확인
if docker ps --format "table {{.Names}}" | grep -q "qwen-image-generator"; then
    echo "⚠️  현재 Docker 컨테이너가 실행 중입니다."
    read -p "컨테이너를 재시작하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔄 컨테이너 재시작 중..."
        docker compose down
        docker compose up -d
        
        echo "⏳ 서비스 시작 대기 중..."
        sleep 10
        
        # 헬스체크
        if curl -f http://localhost:$new_port/health &> /dev/null; then
            echo "✅ 서비스가 포트 $new_port에서 정상 작동 중입니다!"
        else
            echo "⚠️  서비스 시작을 확인해주세요: http://localhost:$new_port/health"
        fi
    fi
else
    echo "💡 다음 명령어로 서비스를 시작할 수 있습니다:"
    echo "   ./scripts/run_docker.sh"
    echo "   또는"
    echo "   docker compose up -d"
fi

echo ""
echo "🌐 새로운 접속 주소:"
echo "   - API: http://localhost:$new_port"
echo "   - 헬스체크: http://localhost:$new_port/health"
echo "   - 모델 정보: http://localhost:$new_port/model-info"
echo ""
echo "📝 테스트 명령어:"
echo "   curl -X POST http://localhost:$new_port/generate \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"prompt\": \"a beautiful sunset\"}'"
