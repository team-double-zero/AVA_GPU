"""
API Routes for Qwen Image Generator
"""
from flask import Blueprint, request, jsonify, send_file
from werkzeug.exceptions import BadRequest
import logging
import os
import uuid
from datetime import datetime
from ..core.model import QwenImageGenerator
from ..core.config import Config

logger = logging.getLogger(__name__)

# Create Blueprint
api_bp = Blueprint('api', __name__)

# Global variables
image_generator = None
model_loading = False

def init_model(config: Config):
    """Initialize the image generator model"""
    global image_generator, model_loading
    
    try:
        model_loading = True
        logger.info("모델 초기화 시작...")
        
        image_generator = QwenImageGenerator(config)
        image_generator.load_model()
        
        model_loading = False
        logger.info("모델 초기화 완료!")
        
    except Exception as e:
        model_loading = False
        logger.error(f"모델 초기화 실패: {str(e)}")
        raise

@api_bp.route('/health', methods=['GET'])
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

@api_bp.route('/generate', methods=['POST'])
def generate_image():
    """이미지 생성 엔드포인트"""
    global image_generator
    
    # Check model loading status
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
        # Parse request data
        if not request.is_json:
            raise BadRequest("JSON 형식의 데이터가 필요합니다")
        
        data = request.get_json()
        
        # Validate required parameters
        prompt = data.get('prompt')
        if not prompt or not prompt.strip():
            return jsonify({
                "success": False,
                "error": "프롬프트가 필요합니다"
            }), 400
        
        # Extract optional parameters
        negative_prompt = data.get('negative_prompt')
        width = data.get('width')
        height = data.get('height')
        num_inference_steps = data.get('num_inference_steps')
        guidance_scale = data.get('guidance_scale')
        seed = data.get('seed')
        save_image = data.get('save_image', False)
        
        # Validate parameters
        config = image_generator.config
        
        if width is not None:
            if not isinstance(width, int) or width < config.MIN_DIMENSION or width > config.MAX_WIDTH:
                return jsonify({
                    "success": False,
                    "error": f"width는 {config.MIN_DIMENSION}-{config.MAX_WIDTH} 사이의 정수여야 합니다"
                }), 400
        
        if height is not None:
            if not isinstance(height, int) or height < config.MIN_DIMENSION or height > config.MAX_HEIGHT:
                return jsonify({
                    "success": False,
                    "error": f"height는 {config.MIN_DIMENSION}-{config.MAX_HEIGHT} 사이의 정수여야 합니다"
                }), 400
        
        if num_inference_steps is not None:
            if not isinstance(num_inference_steps, int) or num_inference_steps < 1 or num_inference_steps > config.MAX_STEPS:
                return jsonify({
                    "success": False,
                    "error": f"num_inference_steps는 1-{config.MAX_STEPS} 사이의 정수여야 합니다"
                }), 400
        
        logger.info(f"이미지 생성 요청: {prompt[:100]}...")
        
        # Generate image
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
            "num_inference_steps": result["num_inference_steps"],
            "guidance_scale": result["guidance_scale"],
            "seed": result["seed"],
            "timestamp": datetime.now().isoformat()
        }
        
        # Save image option
        if save_image:
            filename = f"generated_{uuid.uuid4().hex[:8]}.png"
            filepath = image_generator.save_image(result["image_base64"], filename)
            response_data["saved_path"] = filepath
            response_data["filename"] = filename
        
        # Include base64 image
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

@api_bp.route('/model-info', methods=['GET'])
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

@api_bp.route('/images/<filename>', methods=['GET'])
def get_saved_image(filename):
    """저장된 이미지 파일 제공 엔드포인트"""
    try:
        # Get config from the global image_generator
        if image_generator is None:
            return jsonify({
                "success": False,
                "error": "서비스가 초기화되지 않았습니다"
            }), 503
        
        image_path = os.path.join(image_generator.config.OUTPUT_DIR, filename)
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

@api_bp.errorhandler(413)
def request_entity_too_large(error):
    """파일 크기 초과 오류 핸들러"""
    return jsonify({
        "success": False,
        "error": "요청 크기가 너무 큽니다 (최대 16MB)"
    }), 413

@api_bp.errorhandler(500)
def internal_server_error(error):
    """내부 서버 오류 핸들러"""
    return jsonify({
        "success": False,
        "error": "내부 서버 오류가 발생했습니다"
    }), 500
