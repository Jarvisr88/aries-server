"""
Logging Configuration
Version: 2024-12-14_19-07

Configures logging for the application following our guiding principles:
- Consistent logging format
- Proper log levels
- Structured logging
- Performance considerations
"""
import logging
import sys
from datetime import datetime
from typing import Any, Dict

class CustomFormatter(logging.Formatter):
    """Custom formatter adding timestamp and log level color coding"""
    
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self, fmt: str):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        
        # Add timestamp if not present
        if not hasattr(record, 'timestamp'):
            record.timestamp = datetime.utcnow().isoformat()
        
        # Convert record.args to a dict if it's a tuple
        if record.args and isinstance(record.args, tuple):
            record.args = {f'arg{i}': arg for i, arg in enumerate(record.args)}
        
        return formatter.format(record)

class CustomLogger(logging.Logger):
    """Custom logger with additional methods for structured logging"""
    
    def __init__(self, name: str, level: int = logging.NOTSET):
        super().__init__(name, level)
        self.setup_logger()

    def setup_logger(self) -> None:
        """Setup logger with console handler and custom formatter"""
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        # Create formatter
        fmt = "%(timestamp)s | %(levelname)s | %(name)s | %(message)s"
        formatter = CustomFormatter(fmt)
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.addHandler(console_handler)

    def structured_log(
        self,
        level: int,
        message: str,
        data: Dict[str, Any] = None,
        error: Exception = None
    ) -> None:
        """
        Create a structured log entry with additional context
        
        Args:
            level: Log level (e.g., logging.INFO)
            message: Log message
            data: Additional data to log
            error: Exception to log
        """
        log_data = {
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if data:
            log_data['data'] = data
        
        if error:
            log_data['error'] = {
                'type': type(error).__name__,
                'message': str(error),
                'traceback': getattr(error, '__traceback__', None)
            }
        
        self.log(level, str(log_data))

# Create and configure the logger
logging.setLoggerClass(CustomLogger)
logger = logging.getLogger("aries-enterprise")
logger.setLevel(logging.DEBUG)
