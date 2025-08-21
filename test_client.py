#!/usr/bin/env python3
"""
Qwen Image Generator API 테스트 클라이언트

사용법:
    python test_client.py "a beautiful sunset over mountains"
    python test_client.py --help
"""

import requests
import json
import base64
import argparse
import time
import os

def test_health(base_url: str) -> bool:
    """헬스체크 테스트"""
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"헬스체크 상태: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"서비스 상태: {data.get('status')}")
            print(f"메시지: {data.get('message')}")
            return True
        elif response.status_code == 202:
            data = response.json()
            print(f"서비스 상태: {data.get('status')} - {data.get('message')}")
            return False
        else:
            print(f"헬스체크 실패: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"헬스체크 연결 실패: {e}")
        return False

def generate_image(base_url: str, prompt: str, **kwargs) -> bool:
    """이미지 생성 테스트"""
    payload = {
        "prompt": prompt,
        "save_image": kwargs.get('save_image', True),
        "width": kwargs.get('width', 1024),
        "height": kwargs.get('height', 1024),
        "num_inference_steps": kwargs.get('steps', 20),
        "guidance_scale": kwargs.get('guidance', 7.5)
    }
    
    if kwargs.get('negative_prompt'):
        payload["negative_prompt"] = kwargs['negative_prompt']
    
    if kwargs.get('seed'):
        payload["seed"] = kwargs['seed']
    
    try:
        print(f"이미지 생성 요청 중...")
        print(f"프롬프트: {prompt}")
        print(f"설정: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            f"{base_url}/generate",
            json=payload,
            timeout=300  # 5분 타임아웃
        )
        
        print(f"응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print("✅ 이미지 생성 성공!")
                print(f"프롬프트: {data.get('prompt')}")
                print(f"크기: {data.get('width')}x{data.get('height')}")
                print(f"시드: {data.get('seed')}")
                
                # 이미지 저장
                if data.get('image_base64'):
                    output_dir = "test_outputs"
                    os.makedirs(output_dir, exist_ok=True)
                    
                    timestamp = int(time.time())
                    filename = f"generated_{timestamp}.png"
                    filepath = os.path.join(output_dir, filename)
                    
                    # base64 디코딩 및 저장
                    image_data = base64.b64decode(data['image_base64'])
                    with open(filepath, 'wb') as f:
                        f.write(image_data)
                    
                    print(f"이미지 저장됨: {filepath}")
                
                if data.get('saved_path'):
                    print(f"서버에 저장된 경로: {data.get('saved_path')}")
                
                return True
            else:
                print(f"❌ 이미지 생성 실패: {data.get('error')}")
                return False
        else:
            print(f"❌ 요청 실패: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 요청 타임아웃 (5분)")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 오류: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Qwen Image Generator API 테스트 클라이언트")
    parser.add_argument("prompt", help="이미지 생성을 위한 텍스트 프롬프트")
    parser.add_argument("--url", default="http://localhost:5000", help="API 서버 URL")
    parser.add_argument("--negative", help="네거티브 프롬프트")
    parser.add_argument("--width", type=int, default=1024, help="이미지 너비")
    parser.add_argument("--height", type=int, default=1024, help="이미지 높이")
    parser.add_argument("--steps", type=int, default=20, help="추론 단계 수")
    parser.add_argument("--guidance", type=float, default=7.5, help="가이던스 스케일")
    parser.add_argument("--seed", type=int, help="랜덤 시드")
    parser.add_argument("--no-save", action="store_true", help="서버에 이미지 저장하지 않음")
    parser.add_argument("--wait", action="store_true", help="서비스가 준비될 때까지 대기")
    
    args = parser.parse_args()
    
    print("🧪 Qwen Image Generator API 테스트 클라이언트")
    print(f"🌐 서버 URL: {args.url}")
    print()
    
    # 서비스 준비 대기
    if args.wait:
        print("⏳ 서비스가 준비될 때까지 대기 중...")
        max_attempts = 60  # 5분 대기
        attempt = 1
        
        while attempt <= max_attempts:
            if test_health(args.url):
                print("✅ 서비스가 준비되었습니다!")
                break
            
            print(f"⏳ 대기 중... ({attempt}/{max_attempts})")
            time.sleep(5)
            attempt += 1
        else:
            print("❌ 서비스 준비 타임아웃")
            return False
    else:
        # 헬스체크
        print("🔍 헬스체크 중...")
        if not test_health(args.url):
            print("❌ 서비스가 준비되지 않았습니다. --wait 옵션을 사용하거나 나중에 다시 시도하세요.")
            return False
    
    print()
    
    # 이미지 생성
    print("🎨 이미지 생성 중...")
    kwargs = {
        'negative_prompt': args.negative,
        'width': args.width,
        'height': args.height,
        'steps': args.steps,
        'guidance': args.guidance,
        'seed': args.seed,
        'save_image': not args.no_save
    }
    
    success = generate_image(args.url, args.prompt, **kwargs)
    
    if success:
        print("\n🎉 테스트 완료!")
        return True
    else:
        print("\n❌ 테스트 실패!")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
