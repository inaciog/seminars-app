"""
Comprehensive logging configuration for seminars-app.
Logs everything with 180-day retention for debugging and audit trails.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

# Ensure log directory exists
LOG_DIR = Path("/data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Main application log - rotates daily, keeps 180 days
APP_LOG_FILE = LOG_DIR / "app.log"

# Audit log for security events - rotates daily, keeps 180 days  
AUDIT_LOG_FILE = LOG_DIR / "audit.log"

# Error log - rotates daily, keeps 180 days
ERROR_LOG_FILE = LOG_DIR / "error.log"

# Request log - rotates daily, keeps 180 days
REQUEST_LOG_FILE = LOG_DIR / "requests.log"

# 180 days retention
MAX_DAYS = 180

def setup_logging():
    """Setup comprehensive logging with 180-day retention."""
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    audit_formatter = logging.Formatter(
        '%(asctime)s | AUDIT | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    request_formatter = logging.Formatter(
        '%(asctime)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(console_handler)
    
    # App log - all INFO and above, rotates daily
    app_handler = logging.handlers.TimedRotatingFileHandler(
        APP_LOG_FILE,
        when='midnight',
        interval=1,
        backupCount=MAX_DAYS,
        encoding='utf-8'
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(app_handler)
    
    # Error log - ERROR and above only
    error_handler = logging.handlers.TimedRotatingFileHandler(
        ERROR_LOG_FILE,
        when='midnight',
        interval=1,
        backupCount=MAX_DAYS,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # Audit logger - for security events
    audit_logger = logging.getLogger('audit')
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False  # Don't send to root logger
    
    audit_handler = logging.handlers.TimedRotatingFileHandler(
        AUDIT_LOG_FILE,
        when='midnight',
        interval=1,
        backupCount=MAX_DAYS,
        encoding='utf-8'
    )
    audit_handler.setFormatter(audit_formatter)
    audit_logger.addHandler(audit_handler)
    
    # Request logger - for HTTP requests
    request_logger = logging.getLogger('requests')
    request_logger.setLevel(logging.INFO)
    request_logger.propagate = False
    
    request_handler = logging.handlers.TimedRotatingFileHandler(
        REQUEST_LOG_FILE,
        when='midnight',
        interval=1,
        backupCount=MAX_DAYS,
        encoding='utf-8'
    )
    request_handler.setFormatter(request_formatter)
    request_logger.addHandler(request_handler)
    
    logging.info("Logging system initialized with 180-day retention")
    return audit_logger, request_logger

# Global loggers
audit_log = None
request_log = None

def init_logging():
    """Initialize logging system."""
    global audit_log, request_log
    audit_log, request_log = setup_logging()

def log_audit(event: str, user: str = None, details: dict = None):
    """Log security/audit event."""
    if audit_log:
        details_str = f" | DETAILS: {details}" if details else ""
        user_str = f" | USER: {user}" if user else ""
        audit_log.info(f"{event}{user_str}{details_str}")

def log_request(method: str, path: str, status: int, duration_ms: float, user: str = None, ip: str = None):
    """Log HTTP request."""
    if request_log:
        user_str = f" | USER: {user}" if user else ""
        ip_str = f" | IP: {ip}" if ip else ""
        request_log.info(f"{method} {path} | STATUS: {status} | TIME: {duration_ms:.2f}ms{user_str}{ip_str}")
