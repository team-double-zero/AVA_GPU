from flask import Flask, request, jsonify, send_file
from werkzeug.exceptions import BadRequest
import logging
import os
import threading
import time
from datetime import datetime
from image_generator import QwenImageGenerator
import uuid

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask 앱 초기화
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB 최대 요청 크기

# 글로벌 변수
image_generator = None
model_loading = False

def initialize_model():
    """백그라운드에서 모델을 초기화합니다"""
    global image_generator, model_loading
    
    try:
        model_loading = True
        logger.info("모델 초기화 시작...")
        
        image_generator = QwenImageGenerator()
        image_generator.load_model()
        
        model_loading = False
        logger.info("모델 초기화 완료!")
        
    except Exception as e:
        model_loading = False
        logger.error(f"모델 초기화 실패: {str(e)}")

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크 엔드포인트"""
    global image_generator, model_loading
    
    if model_loading:
        return jsonify({
            "status": "loading",
            "message": "모델을 로딩 중입니다...",
            "timestamp": datetime.now().isoformat()
        }), 202
    
    if image_generator is None:
        return jsonify({
            "status": "error",
            "message": "모델이 로드되지 않았습니다",
            "timestamp": datetime.now().isoformat()
        }), 503
    
    return jsonify({
        "status": "ready",
        "message": "서비스가 준비되었습니다",
        "model_info": image_generator.get_model_info(),
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/generate', methods=['POST'])
def generate_image():
    """이미지 생성 엔드포인트"""
    global image_generator
    
    # 모델 로딩 상태 확인
    if model_loading:
        return jsonify({
            "success": False,
            "error": "모델을 로딩 중입니다. 잠시 후 다시 시도하세요.",
            "status": "loading"
        }), 202
    
    if image_generator is None:
        return jsonify({
            "success": False,
            "error": "모델이 로드되지 않았습니다. 서버를 재시작하세요.",
            "status": "error"
        }), 503
    
    try:
        # 요청 데이터 파싱
        if not request.is_json:
            raise BadRequest("JSON 형식의 데이터가 필요합니다")
        
        data = request.get_json()
        
        # 필수 파라미터 검증
        prompt = data.get('prompt')
        if not prompt or not prompt.strip():
            return jsonify({
                "success": False,
                "error": "프롬프트가 필요합니다"
            }), 400
        
        # 선택적 파라미터
        negative_prompt = data.get('negative_prompt', None)
        width = data.get('width', 1024)
        height = data.get('height', 1024)
        num_inference_steps = data.get('num_inference_steps', 20)
        guidance_scale = data.get('guidance_scale', 7.5)
        seed = data.get('seed', None)
        save_image = data.get('save_image', False)
        
        # 파라미터 검증
        if not isinstance(width, int) or width < 64 or width > 2048:
            return jsonify({
                "success": False,
                "error": "width는 64-2048 사이의 정수여야 합니다"
            }), 400
        
        if not isinstance(height, int) or height < 64 or height > 2048:
            return jsonify({
                "success": False,
                "error": "height는 64-2048 사이의 정수여야 합니다"
            }), 400
        
        if not isinstance(num_inference_steps, int) or num_inference_steps < 1 or num_inference_steps > 100:
            return jsonify({
                "success": False,
                "error": "num_inference_steps는 1-100 사이의 정수여야 합니다"
            }), 400
        
        logger.info(f"이미지 생성 요청: {prompt[:100]}...")
        
        # 이미지 생성
        result = image_generator.generate_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            seed=seed
        )
        
        if not result["success"]:
            return jsonify(result), 500
        
        response_data = {
            "success": True,
            "prompt": result["prompt"],
            "negative_prompt": result["negative_prompt"],
            "width": result["width"],
            "height": result["height"],
            "seed": result["seed"],
            "timestamp": datetime.now().isoformat()
        }
        
        # 이미지 저장 옵션
        if save_image:
            filename = f"generated_{uuid.uuid4().hex[:8]}.png"
            filepath = image_generator.save_image(result["image_base64"], filename)
            response_data["saved_path"] = filepath
            response_data["filename"] = filename
        
        # base64 이미지 포함
        response_data["image_base64"] = result["image_base64"]
        
        logger.info("이미지 생성 요청 완료")
        return jsonify(response_data), 200
        
    except BadRequest as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        logger.error(f"이미지 생성 중 오류: {str(e)}")
        return jsonify({
            "success": False,
            "error": "내부 서버 오류가 발생했습니다"
        }), 500

@app.route('/model-info', methods=['GET'])
def get_model_info():
    """모델 정보 조회 엔드포인트"""
    global image_generator
    
    if image_generator is None:
        return jsonify({
            "success": False,
            "error": "모델이 로드되지 않았습니다"
        }), 503
    
    try:
        model_info = image_generator.get_model_info()
        return jsonify({
            "success": True,
            "model_info": model_info,
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"모델 정보 조회 중 오류: {str(e)}")
        return jsonify({
            "success": False,
            "error": "모델 정보를 가져올 수 없습니다"
        }), 500

@app.route('/images/<filename>', methods=['GET'])
def get_saved_image(filename):
    """저장된 이미지 파일 제공 엔드포인트"""
    try:
        image_path = os.path.join("generated_images", filename)
        if not os.path.exists(image_path):
            return jsonify({
                "success": False,
                "error": "이미지 파일을 찾을 수 없습니다"
            }), 404
        
        return send_file(image_path, mimetype='image/png')
    except Exception as e:
        logger.error(f"이미지 파일 제공 중 오류: {str(e)}")
        return jsonify({
            "success": False,
            "error": "이미지 파일을 제공할 수 없습니다"
        }), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    """파일 크기 초과 오류 핸들러"""
    return jsonify({
        "success": False,
        "error": "요청 크기가 너무 큽니다 (최대 16MB)"
    }), 413

@app.errorhandler(500)
def internal_server_error(error):
    """내부 서버 오류 핸들러"""
    return jsonify({
        "success": False,
        "error": "내부 서버 오류가 발생했습니다"
    }), 500

if __name__ == '__main__':
    # 출력 디렉토리 생성
    os.makedirs("generated_images", exist_ok=True)
    
    # 백그라운드에서 모델 로드 시작
    model_thread = threading.Thread(target=initialize_model)
    model_thread.daemon = True
    model_thread.start()
    
    # Flask 앱 실행
    logger.info("Flask 서버 시작...")
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=False,
        threaded=True
    )
