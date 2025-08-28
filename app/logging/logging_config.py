"""
Logging Configuration for AI-AdaptLearn
Provides centralized logging configuration and utilities.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Log file paths
app_log_file = logs_dir / "app.log"
error_log_file = logs_dir / "errors.log"
access_log_file = logs_dir / "access.log"

def setup_logging(
    log_level: str = "INFO",
    enable_file_logging: bool = True,
    enable_console_logging: bool = True
) -> None:
    """
    Setup application logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_file_logging: Enable logging to files
        enable_console_logging: Enable logging to console
    """
    
    # Convert string to logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Clear any existing handlers
    logging.getLogger().handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    if enable_console_logging:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
    
    if enable_file_logging:
        # Application log handler (rotating file)
        app_handler = logging.handlers.RotatingFileHandler(
            app_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        app_handler.setLevel(numeric_level)
        app_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(app_handler)
        
        # Error log handler (errors only)
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
    
    # Set specific logger levels
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('fastapi').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

def log_startup_info() -> None:
    """Log application startup information."""
    logger = get_logger("startup")
    
    logger.info("=" * 60)
    logger.info("🚀 AI-AdaptLearn Application Starting")
    logger.info("=" * 60)
    logger.info(f"Startup Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Python Version: {os.sys.version}")
    logger.info(f"Working Directory: {os.getcwd()}")
    logger.info(f"Logs Directory: {logs_dir.absolute()}")
    
    # Log environment info
    env_vars = ['DEBUG', 'HOST', 'PORT', 'DATABASE_URL']
    for var in env_vars:
        value = os.getenv(var, 'Not Set')
        logger.info(f"Environment Variable {var}: {value}")
    
    logger.info("=" * 60)

def log_shutdown_info() -> None:
    """Log application shutdown information."""
    logger = get_logger("shutdown")
    logger.info("=" * 60)
    logger.info("🛑 AI-AdaptLearn Application Shutting Down")
    logger.info(f"Shutdown Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

# Logging decorators for performance monitoring
def log_function_call(func_name: str = None):
    """
    Decorator to log function calls with timing.
    
    Args:
        func_name: Optional custom function name for logging
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            name = func_name or func.__name__
            
            start_time = datetime.now()
            logger.debug(f"🔄 Calling function: {name}")
            
            try:
                result = func(*args, **kwargs)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.debug(f"✅ Function {name} completed in {duration:.3f}s")
                return result
            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.error(f"❌ Function {name} failed after {duration:.3f}s: {str(e)}")
                raise
        
        return wrapper
    return decorator

def log_api_request(endpoint: str, method: str = "GET", user_id: str = None):
    """
    Decorator to log API request details.
    
    Args:
        endpoint: API endpoint path
        method: HTTP method
        user_id: Optional user identifier
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger("api")
            start_time = datetime.now()
            
            user_info = f" (User: {user_id})" if user_id else ""
            logger.info(f"🌐 {method} {endpoint}{user_info}")
            
            try:
                result = func(*args, **kwargs)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.info(f"✅ {method} {endpoint} completed in {duration:.3f}s{user_info}")
                return result
            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.error(f"❌ {method} {endpoint} failed after {duration:.3f}s{user_info}: {str(e)}")
                raise
        
        return wrapper
    return decorator
