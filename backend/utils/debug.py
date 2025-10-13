"""Debug utilities for the LR(1) Parser Visualizer."""

import os
import logging
import sys
from typing import Any, Dict, Optional
from datetime import datetime
from functools import wraps

# Debug flag from environment variable
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

# Configure logging
def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    log_level = logging.DEBUG if DEBUG else getattr(logging, level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    return root_logger

def debug_log(message: str, data: Optional[Dict[str, Any]] = None):
    """Log debug message if debug mode is enabled."""
    if DEBUG:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"🐛 [{timestamp}] {message}")
        if data:
            print(f"   📊 Data: {data}")

def info_log(message: str, data: Optional[Dict[str, Any]] = None):
    """Log info message."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"ℹ️  [{timestamp}] {message}")
    if data:
        print(f"   📊 Data: {data}")

def error_log(message: str, error: Optional[Exception] = None, data: Optional[Dict[str, Any]] = None):
    """Log error message."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"❌ [{timestamp}] {message}")
    if error:
        print(f"   🔥 Error: {error}")
    if data:
        print(f"   📊 Data: {data}")

def success_log(message: str, data: Optional[Dict[str, Any]] = None):
    """Log success message."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"✅ [{timestamp}] {message}")
    if data:
        print(f"   📊 Data: {data}")

def log_function_call(func_name: str, args: tuple = (), kwargs: Dict[str, Any] = None):
    """Log function call with arguments."""
    if DEBUG:
        kwargs = kwargs or {}
        debug_log(f"🔧 Calling {func_name}", {"args": args, "kwargs": kwargs})

def log_function_result(func_name: str, result: Any = None, duration: float = None):
    """Log function result."""
    if DEBUG:
        data = {}
        if result is not None:
            data["result"] = str(result)[:100] + "..." if len(str(result)) > 100 else str(result)
        if duration is not None:
            data["duration_ms"] = f"{duration * 1000:.2f}"
        debug_log(f"🔧 Completed {func_name}", data)

def debug_timer(func):
    """Decorator to time function execution."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not DEBUG:
            return func(*args, **kwargs)
        
        start_time = datetime.now()
        func_name = f"{func.__module__}.{func.__name__}"
        
        log_function_call(func_name, args, kwargs)
        
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            log_function_result(func_name, result, duration)
            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_log(f"🔧 Failed {func_name}", e, {"duration_ms": f"{duration * 1000:.2f}"})
            raise
    
    return wrapper

def log_api_request(method: str, endpoint: str, data: Optional[Dict[str, Any]] = None):
    """Log API request."""
    info_log(f"🌐 {method} {endpoint}", data)

def log_api_response(endpoint: str, status_code: int, data: Optional[Dict[str, Any]] = None):
    """Log API response."""
    if 200 <= status_code < 300:
        success_log(f"🌐 Response {status_code} for {endpoint}", data)
    else:
        error_log(f"🌐 Response {status_code} for {endpoint}", data=data)

# Initialize logging
setup_logging()
