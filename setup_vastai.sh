#!/bin/bash

# vast.ai GPU 서버 초기 설정 스크립트

echo "🚀 vast.ai GPU 서버 초기 설정 시작..."

# 시스템 정보 확인
echo "📊 시스템 정보:"
echo "운영체제: $(lsb_release -d 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "GPU 정보:"
nvidia-smi 2>/dev/null || echo "⚠️  NVIDIA GPU 드라이버를 확인해주세요"

echo ""

# Docker 설치 상태 확인
echo "🔍 Docker 설치 상태 확인 중..."

if command -v docker &> /dev/null; then
    echo "✅ Docker가 설치되어 있습니다"
    docker --version
else
    echo "❌ Docker가 설치되지 않았습니다. 설치를 시작합니다..."
    
    # Ubuntu/Debian용 Docker 설치
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
    
    # Docker GPG 키 추가
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Docker 리포지토리 추가
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Docker 설치
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    echo "✅ Docker 설치 완료"
fi

# Docker 서비스 시작
echo "🔄 Docker 서비스 상태 확인 및 시작..."

# Docker 데몬이 이미 실행 중인지 확인
if docker ps &> /dev/null; then
    echo "✅ Docker 서비스가 이미 실행 중입니다"
else
    echo "🚀 Docker 서비스를 시작합니다..."
    
    # systemd 사용 가능한지 확인
    if command -v systemctl &> /dev/null && systemctl is-system-running &> /dev/null; then
        echo "systemd 환경에서 Docker 시작..."
        sudo systemctl start docker
        sudo systemctl enable docker
    else
        echo "non-systemd 환경 (vast.ai 컨테이너)에서 Docker 시작..."
        
        # Docker 데몬을 백그라운드에서 시작
        sudo dockerd &> /tmp/dockerd.log &
        
        # Docker 데몬이 시작될 때까지 대기
        echo "Docker 데몬 시작 대기 중..."
        for i in {1..30}; do
            if docker ps &> /dev/null; then
                echo "✅ Docker 데몬이 성공적으로 시작되었습니다"
                break
            fi
            echo "대기 중... ($i/30)"
            sleep 2
        done
        
        if ! docker ps &> /dev/null; then
            echo "❌ Docker 데몬 시작에 실패했습니다"
            echo "로그 확인:"
            tail -20 /tmp/dockerd.log
            exit 1
        fi
    fi
fi

# 현재 사용자를 docker 그룹에 추가
echo "👤 사용자 권한 설정 중..."
sudo usermod -aG docker $USER

# NVIDIA Container Toolkit 설치 (GPU 지원용)
echo "🔧 NVIDIA Container Toolkit 설치 중..."

if ! command -v nvidia-container-runtime &> /dev/null; then
    # NVIDIA GPG 키 및 리포지토리 추가
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
    curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
    
    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
    
    # Docker 재시작
    sudo systemctl restart docker
    
    echo "✅ NVIDIA Container Toolkit 설치 완료"
else
    echo "✅ NVIDIA Container Toolkit이 이미 설치되어 있습니다"
fi

# Docker 연결 테스트
echo "🧪 Docker 연결 테스트 중..."
if docker ps &> /dev/null; then
    echo "✅ Docker가 정상적으로 작동합니다"
else
    echo "⚠️  Docker 권한 문제가 있을 수 있습니다. 다음 명령어를 실행하고 재로그인하세요:"
    echo "   newgrp docker"
    echo "   또는 서버를 재시작하세요."
fi

# GPU 컨테이너 테스트
echo "🎮 GPU 컨테이너 테스트 중..."
if docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi &> /dev/null; then
    echo "✅ GPU 컨테이너가 정상적으로 작동합니다"
else
    echo "⚠️  GPU 컨테이너 설정을 확인해주세요"
fi

echo ""
echo "🎉 vast.ai 서버 설정이 완료되었습니다!"
echo ""
echo "다음 단계:"
echo "1. 서버 재시작 (권장): sudo reboot"
echo "2. 또는 Docker 그룹 적용: newgrp docker"
echo "3. 프로젝트 실행: ./start.sh"
