# Qwen Image Generator API

vast.ai GPU 서버에서 Qwen 이미지 생성 모델을 활용한 Flask API 서비스입니다.

## 🚀 기능

- **텍스트-이미지 생성**: 텍스트 프롬프트로부터 고품질 이미지 생성
- **GPU 가속**: CUDA를 활용한 빠른 이미지 생성
- **RESTful API**: 간단한 HTTP API 인터페이스
- **Docker 지원**: 컨테이너화된 배포
- **헬스체크**: 서비스 상태 모니터링
- **이미지 저장**: 생성된 이미지 파일 저장 및 제공

## 📋 시스템 요구사항

- NVIDIA GPU (CUDA 지원)
- Docker & Docker Compose
- 최소 8GB GPU 메모리
- Python 3.9+

## 🛠️ 설치 및 실행

### vast.ai 환경에서 실행 (권장)

```bash
# 프로젝트 클론
git clone <repository-url>
cd qwen_project

# Docker 실행 (vast.ai에는 Docker가 이미 설치됨)
./scripts/run_docker.sh
```

### Docker Compose 사용 (권장)

1. **프로젝트 클론**
```bash
git clone <repository-url>
cd AVA_GPU
```

2. **Docker 컨테이너 빌드 및 실행**
```bash
# 최신 Docker Desktop (권장)
docker compose up --build -d

# 또는 기존 docker-compose 명령어
docker-compose up --build -d
```

3. **서비스 상태 확인**
```bash
curl http://localhost:5000/health
```

### 직접 설치

1. **Python 의존성 설치**
```bash
pip install -r requirements.txt
```

2. **서버 실행**
```bash
python app.py
```

## 🔌 API 사용법

### 1. 헬스체크

서비스 상태와 모델 로딩 상태를 확인합니다.

```bash
curl -X GET http://localhost:5000/health
```

**응답 예시:**
```json
{
  "status": "ready",
  "message": "서비스가 준비되었습니다",
  "model_info": {
    "model_name": "Qwen/Qwen2-VL-7B-Instruct",
    "device": "cuda",
    "is_loaded": true
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

### 2. 이미지 생성

텍스트 프롬프트로부터 이미지를 생성합니다.

```bash
curl -X POST http://localhost:5000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a beautiful sunset over mountains",
    "width": 1024,
    "height": 1024,
    "num_inference_steps": 20,
    "guidance_scale": 7.5,
    "save_image": true
  }'
```

**요청 파라미터:**
- `prompt` (필수): 이미지 생성을 위한 텍스트 프롬프트
- `negative_prompt` (선택): 원하지 않는 요소를 명시
- `width` (선택, 기본값: 1024): 이미지 너비 (64-2048)
- `height` (선택, 기본값: 1024): 이미지 높이 (64-2048)
- `num_inference_steps` (선택, 기본값: 20): 추론 단계 수 (1-100)
- `guidance_scale` (선택, 기본값: 7.5): 가이던스 스케일
- `seed` (선택): 재현 가능한 결과를 위한 랜덤 시드
- `save_image` (선택, 기본값: false): 이미지 파일 저장 여부

**응답 예시:**
```json
{
  "success": true,
  "prompt": "a beautiful sunset over mountains",
  "width": 1024,
  "height": 1024,
  "seed": null,
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "saved_path": "generated_images/generated_abc12345.png",
  "timestamp": "2024-01-15T10:35:00"
}
```

### 3. 모델 정보 조회

현재 로드된 모델의 정보를 확인합니다.

```bash
curl -X GET http://localhost:5000/model-info
```

### 4. 저장된 이미지 조회

저장된 이미지 파일을 다운로드합니다.

```bash
curl -X GET http://localhost:5000/images/generated_abc12345.png --output image.png
```

## 🐛 문제 해결

### 모델 로딩 실패

**증상**: `/health` 엔드포인트에서 "loading" 상태가 지속됨

**해결방법**:
1. GPU 메모리 확인: `nvidia-smi`
2. 컨테이너 로그 확인: `docker-compose logs -f`
3. 충분한 디스크 공간 확인 (모델 파일 다운로드용)

### Docker 데몬 연결 오류

**증상**: "Cannot connect to the Docker daemon" 오류

**해결방법 (vast.ai 환경)**:
```bash
# 1. Docker 데몬 시작 (특별 설정 포함)
./start_docker.sh

# 2. 또는 수동으로 Docker 데몬 시작 (Docker-in-Docker용)
sudo dockerd --storage-driver=vfs --iptables=false --bridge=none &

# 3. Docker 데몬 상태 확인
docker ps

# 4. Docker 문제 지속 시 직접 실행
./run_direct.sh

# 5. 사용자 권한 설정 (필요시)
sudo usermod -aG docker $USER
newgrp docker
```

**해결방법 (일반 Linux)**:
```bash
# systemd 환경에서
sudo systemctl start docker
sudo systemctl enable docker
```

### Docker Compose 권한 오류

**증상**: "Permission denied" 오류가 발생하는 경우

**해결방법**:
1. 최신 Docker Desktop 사용 시: `docker compose` (공백 포함) 명령어 사용
2. 기존 버전 사용 시: `docker-compose` 권한 확인
```bash
# 최신 명령어 테스트
docker compose version

# 권한 확인
ls -la /usr/local/bin/docker-compose
```

### CUDA 오류

**증상**: "CUDA out of memory" 또는 CUDA 관련 오류

**해결방법**:
1. GPU 메모리가 충분한지 확인
2. 이미지 크기를 줄여서 시도 (예: 512x512)
3. `num_inference_steps`를 줄여서 시도

### 네트워크 연결 오류

**증상**: 모델 다운로드 실패

**해결방법**:
1. 인터넷 연결 확인
2. Hugging Face Hub 접근 확인
3. 프록시 설정 확인 (필요한 경우)

## 📁 프로젝트 구조

```
qwen_project/             # 프로젝트 최상위 폴더
├── app/                  # 🐍 모든 파이썬 소스 코드
│   ├── __init__.py
│   ├── main.py           # Flask 애플리케이션 진입점
│   ├── api/              # API 엔드포인트 관련 코드
│   │   ├── __init__.py
│   │   └── routes.py     # '/generate' 등 라우트 정의
│   └── core/             # 핵심 비즈니스 로직
│       ├── __init__.py
│       ├── config.py     # 설정 관리
│       └── model.py      # 모델 로딩 및 이미지 생성 로직
├── scripts/              # 📜 자동화 스크립트
│   └── run_docker.sh     # Docker 빌드 및 실행 스크립트
├── docker-compose.yml    # Docker 컨테이너 설정
├── Dockerfile           # Docker 이미지 빌드 설정
├── requirements.txt     # Python 의존성 라이브러리
├── .dockerignore        # Docker 빌드 제외 파일
└── README.md            # 프로젝트 문서
```

## 🔧 고급 설정

### 환경 변수

- `PORT`: 서버 포트 (기본값: 5000)
- `TORCH_HOME`: PyTorch 모델 캐시 디렉토리
- `HF_HOME`: Hugging Face 모델 캐시 디렉토리

### Docker 볼륨

- `model_cache`: Hugging Face 모델 캐시
- `torch_cache`: PyTorch 캐시
- `generated_images`: 생성된 이미지 저장소
- `logs`: 애플리케이션 로그

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 등록해 주세요.

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
