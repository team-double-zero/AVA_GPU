# CUDA 지원 PyTorch 기반 이미지 사용
FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-devel

# 작업 디렉토리 설정
WORKDIR /app

# 비대화형 설치 설정
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Seoul

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Python 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TORCH_HOME=/app/torch_cache
ENV HF_HOME=/app/huggingface_cache
ENV FLASK_ENV=production

# requirements.txt 복사 및 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY app/ ./app/

# 캐시 및 출력 디렉토리 생성
RUN mkdir -p /app/torch_cache /app/huggingface_cache /app/generated_images

# 포트 노출
EXPOSE 5000

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 컨테이너 시작 명령
CMD ["python", "-m", "app.main"]
