"""
Qwen Image Generation Model Handler
"""
import torch
import logging
from diffusers import AutoPipelineForText2Image
from PIL import Image
import base64
import io
import os
from typing import Optional, Dict, Any
from .config import Config

logger = logging.getLogger(__name__)

class QwenImageGenerator:
    """Qwen 이미지 생성 모델을 관리하는 클래스"""
    
    def __init__(self, config: Config):
        """
        Initialize the Qwen Image Generator
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.model_name = config.MODEL_NAME
        self.fallback_model = config.FALLBACK_MODEL
        self.pipeline = None
        self.device = "cuda" if torch.cuda.is_available() and config.USE_CUDA else "cpu"
        
        # Set torch dtype based on config and device
        if config.TORCH_DTYPE == "float16" and torch.cuda.is_available():
            self.torch_dtype = torch.float16
        elif config.TORCH_DTYPE == "bfloat16":
            self.torch_dtype = torch.bfloat16
        else:
            self.torch_dtype = torch.float32
        
        logger.info(f"장치: {self.device}")
        logger.info(f"데이터 타입: {self.torch_dtype}")
        
    def load_model(self) -> None:
        """모델을 로드합니다"""
        try:
            logger.info(f"모델 로딩 중: {self.model_name}")
            
            # Try to load the primary model
            self.pipeline = AutoPipelineForText2Image.from_pretrained(
                self.model_name,
                torch_dtype=self.torch_dtype,
                device_map="auto" if torch.cuda.is_available() else None,
                trust_remote_code=True,
                variant="fp16" if self.torch_dtype == torch.float16 else None
            )
            
            # Optimize for GPU
            if torch.cuda.is_available():
                self.pipeline.enable_model_cpu_offload()
                self.pipeline.enable_attention_slicing()
                
            logger.info("모델 로딩 완료")
            
        except Exception as e:
            logger.error(f"모델 로딩 실패: {str(e)}")
            # Try fallback model
            try:
                logger.info(f"대체 모델로 시도 중: {self.fallback_model}")
                self.pipeline = AutoPipelineForText2Image.from_pretrained(
                    self.fallback_model,
                    torch_dtype=self.torch_dtype,
                    device_map="auto" if torch.cuda.is_available() else None,
                    variant="fp16" if self.torch_dtype == torch.float16 else None
                )
                logger.info("대체 모델 로딩 완료")
            except Exception as fallback_error:
                logger.error(f"대체 모델 로딩도 실패: {str(fallback_error)}")
                raise
    
    def generate_image(
        self, 
        prompt: str, 
        negative_prompt: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        num_inference_steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        텍스트 프롬프트로부터 이미지를 생성합니다
        
        Args:
            prompt: 이미지 생성을 위한 텍스트 프롬프트
            negative_prompt: 원하지 않는 요소를 명시하는 네거티브 프롬프트
            width: 생성할 이미지의 너비
            height: 생성할 이미지의 높이
            num_inference_steps: 추론 단계 수
            guidance_scale: 가이던스 스케일
            seed: 랜덤 시드
            
        Returns:
            생성된 이미지 정보가 담긴 딕셔너리
        """
        if self.pipeline is None:
            raise RuntimeError("모델이 로드되지 않았습니다. load_model()을 먼저 호출하세요.")
        
        # Use config defaults if not provided
        width = width or self.config.DEFAULT_WIDTH
        height = height or self.config.DEFAULT_HEIGHT
        num_inference_steps = num_inference_steps or self.config.DEFAULT_STEPS
        guidance_scale = guidance_scale or self.config.DEFAULT_GUIDANCE
        
        try:
            logger.info(f"이미지 생성 시작: {prompt[:50]}...")
            
            # Set random seed if provided
            if seed is not None:
                torch.manual_seed(seed)
                if torch.cuda.is_available():
                    torch.cuda.manual_seed(seed)
            
            # Generate image
            result = self.pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                generator=torch.Generator(device=self.device).manual_seed(seed) if seed else None
            )
            
            image = result.images[0]
            
            # Convert image to base64
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            logger.info("이미지 생성 완료")
            
            return {
                "success": True,
                "image_base64": img_base64,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "num_inference_steps": num_inference_steps,
                "guidance_scale": guidance_scale,
                "seed": seed
            }
            
        except Exception as e:
            logger.error(f"이미지 생성 실패: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "prompt": prompt
            }
    
    def save_image(self, image_base64: str, filename: str) -> str:
        """Base64 인코딩된 이미지를 파일로 저장합니다"""
        try:
            # Decode base64 image
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))
            
            # Ensure output directory exists
            os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)
            filepath = os.path.join(self.config.OUTPUT_DIR, filename)
            
            # Save image
            image.save(filepath)
            logger.info(f"이미지 저장됨: {filepath}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"이미지 저장 실패: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보를 반환합니다"""
        return {
            "model_name": self.model_name,
            "fallback_model": self.fallback_model,
            "device": self.device,
            "torch_dtype": str(self.torch_dtype),
            "is_loaded": self.pipeline is not None,
            "cuda_available": torch.cuda.is_available(),
            "cuda_memory": torch.cuda.get_device_properties(0).total_memory if torch.cuda.is_available() else None,
            "config": {
                "default_width": self.config.DEFAULT_WIDTH,
                "default_height": self.config.DEFAULT_HEIGHT,
                "default_steps": self.config.DEFAULT_STEPS,
                "default_guidance": self.config.DEFAULT_GUIDANCE
            }
        }
