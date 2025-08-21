"""
Main Flask Application Entry Point
"""
from flask import Flask
import logging
import threading
import os
from .core.config import config, Config
from .api.routes import api_bp, init_model

def create_app(config_name='default'):
    """
    Flask 애플리케이션 팩토리 함수
    
    Args:
        config_name: 설정 이름 ('development', 'production', 'default')
    
    Returns:
        Flask 애플리케이션 인스턴스
    """
    app = Flask(__name__)
    
    # Load configuration
    app_config = config[config_name]
    app.config.from_object(app_config)
    
    # Set max content length
    app.config['MAX_CONTENT_LENGTH'] = app_config.MAX_CONTENT_LENGTH
    
    # Initialize logging
    setup_logging(app_config)
    
    # Initialize directories
    app_config.init_directories()
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Initialize model in background thread
    if not app.config.get('TESTING', False):
        model_thread = threading.Thread(target=init_model, args=(app_config,))
        model_thread.daemon = True
        model_thread.start()
    
    return app

def setup_logging(config: Config):
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set specific loggers
    logger = logging.getLogger(__name__)
    logger.info(f"애플리케이션 시작 - 환경: {'개발' if config.DEBUG else '운영'}")

def main():
    """메인 실행 함수"""
    # Get configuration from environment
    config_name = os.environ.get('FLASK_ENV', 'default')
    
    # Create Flask app
    app = create_app(config_name)
    
    # Get config
    app_config = config[config_name]
    
    # Run the application
    logger = logging.getLogger(__name__)
    logger.info(f"Flask 서버 시작...")
    logger.info(f"주소: http://{app_config.HOST}:{app_config.PORT}")
    logger.info(f"헬스체크: http://{app_config.HOST}:{app_config.PORT}/health")
    
    app.run(
        host=app_config.HOST,
        port=app_config.PORT,
        debug=app_config.DEBUG,
        threaded=True
    )

if __name__ == '__main__':
    main()
