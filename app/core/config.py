"""
Configuration settings for Qwen Image Generator
"""
import os

class Config:
    """Base configuration class"""
    
    # Server settings
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Model settings
    MODEL_NAME = os.environ.get('MODEL_NAME', 'Qwen/Qwen2-VL-7B-Instruct')
    FALLBACK_MODEL = os.environ.get('FALLBACK_MODEL', 'stabilityai/stable-diffusion-xl-base-1.0')
    
    # Cache directories
    TORCH_HOME = os.environ.get('TORCH_HOME', '/app/torch_cache')
    HF_HOME = os.environ.get('HF_HOME', '/app/huggingface_cache')
    
    # Image generation defaults
    DEFAULT_WIDTH = int(os.environ.get('DEFAULT_WIDTH', 1024))
    DEFAULT_HEIGHT = int(os.environ.get('DEFAULT_HEIGHT', 1024))
    DEFAULT_STEPS = int(os.environ.get('DEFAULT_STEPS', 20))
    DEFAULT_GUIDANCE = float(os.environ.get('DEFAULT_GUIDANCE', 7.5))
    
    # Limits
    MAX_WIDTH = int(os.environ.get('MAX_WIDTH', 2048))
    MAX_HEIGHT = int(os.environ.get('MAX_HEIGHT', 2048))
    MAX_STEPS = int(os.environ.get('MAX_STEPS', 100))
    MIN_DIMENSION = int(os.environ.get('MIN_DIMENSION', 64))
    
    # File settings
    OUTPUT_DIR = os.environ.get('OUTPUT_DIR', 'generated_images')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # GPU settings
    USE_CUDA = os.environ.get('USE_CUDA', 'True').lower() == 'true'
    TORCH_DTYPE = os.environ.get('TORCH_DTYPE', 'float16')
    
    @classmethod
    def init_directories(cls):
        """Initialize required directories"""
        os.makedirs(cls.TORCH_HOME, exist_ok=True)
        os.makedirs(cls.HF_HOME, exist_ok=True)
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
