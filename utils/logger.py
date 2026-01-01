"""
Centralized Logging System for LLM-Driven Dynamic Replanning
Production-grade observability with console and file output.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
import sys
from datetime import datetime


class ExperimentLogger:
    """
    Centralized logger for the LLM-driven dynamic replanning system.

    Features:
    - Console output (INFO level and above)
    - File output (DEBUG level and above) to trace.log
    - Structured format: [TIMESTAMP] [COMPONENT] [LEVEL] Message
    - Component-based logging for easy filtering
    - Automatic log rotation for long experiments
    """

    def __init__(self, log_file: str = "trace.log", log_level: int = logging.DEBUG):
        """
        Initialize the experiment logger.

        Args:
            log_file: Path to the log file (default: trace.log)
            log_level: Minimum log level for file output
        """
        self.log_file = Path(log_file)
        self.log_level = log_level

        # Create logger
        self.logger = logging.getLogger("llm_replanning")
        self.logger.setLevel(logging.DEBUG)

        # Remove any existing handlers
        self.logger.handlers.clear()

        # Create formatters
        console_formatter = logging.Formatter(
            '%(asctime)s [%(component)s] %(levelname)s %(message)s',
            datefmt='%H:%M:%S'
        )

        file_formatter = logging.Formatter(
            '%(asctime)s [%(component)s] %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler (INFO and above)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(self._console_filter)
        self.logger.addHandler(console_handler)

        # File handler (DEBUG and above) with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # Log initialization
        self.info("SYSTEM", "Experiment logger initialized")
        self.debug("SYSTEM", f"Log file: {self.log_file.absolute()}")
        self.debug("SYSTEM", f"Log level: {logging.getLevelName(log_level)}")

    def _console_filter(self, record):
        """Filter to control what goes to console."""
        # Only show INFO, WARNING, ERROR, CRITICAL to console
        return record.levelno >= logging.INFO

    def _log(self, component: str, level: int, message: str, *args, **kwargs):
        """Internal logging method with component context."""
        # Add component to the log record
        extra = kwargs.get('extra', {})
        extra['component'] = component
        kwargs['extra'] = extra

        self.logger.log(level, message, *args, **kwargs)

    def debug(self, component: str, message: str):
        """Log debug message."""
        self._log(component, logging.DEBUG, message)

    def info(self, component: str, message: str):
        """Log info message."""
        self._log(component, logging.INFO, message)

    def warning(self, component: str, message: str):
        """Log warning message."""
        self._log(component, logging.WARNING, message)

    def error(self, component: str, message: str):
        """Log error message."""
        self._log(component, logging.ERROR, message)

    def critical(self, component: str, message: str):
        """Log critical message."""
        self._log(component, logging.CRITICAL, message)

    def log_experiment_start(self, scenario_name: str, parameters: dict):
        """Log the start of an experiment."""
        self.info("EXPERIMENT", f"--- EXPERIMENT START: {scenario_name} ---")
        for key, value in parameters.items():
            self.info("EXPERIMENT", f"Parameter {key}: {value}")

    def log_experiment_end(self, scenario_name: str, success: bool, duration: float):
        """Log the end of an experiment."""
        status = "SUCCESS" if success else "FAILED"
        self.info("EXPERIMENT", f"--- EXPERIMENT END: {scenario_name} ({status}) ---")
        self.info("EXPERIMENT", ".2f")

    def log_pddl_content(self, component: str, pddl_type: str, filename: str, content: str):
        """Log full PDDL content for debugging."""
        self.debug(component, f"=== {pddl_type.upper()} PDDL CONTENT ({filename}) ===")
        # Split content into lines and log each line
        for line_num, line in enumerate(content.split('\n'), 1):
            if line.strip():  # Only log non-empty lines
                self.debug(component, f"{line_num:3d}: {line}")
        self.debug(component, f"=== END {pddl_type.upper()} PDDL CONTENT ===")

    def log_llm_interaction(self, prompt: str, response: dict):
        """Log LLM interactions for analysis."""
        self.debug("LLM", "=== LLM PROMPT ===")
        # Log prompt in chunks to avoid line length issues
        for i, chunk in enumerate(self._chunk_text(prompt, 500)):
            self.debug("LLM", f"Prompt part {i+1}: {chunk}")
        self.debug("LLM", "=== LLM RESPONSE ===")
        self.debug("LLM", f"Decision: {response.get('replan_needed', 'UNKNOWN')}")
        self.debug("LLM", f"Reasoning: {response.get('reasoning', 'NO REASONING')}")
        if response.get('new_entity'):
            self.debug("LLM", f"New Entity: {response['new_entity']}")

    def log_visualization(self, step: int, filename: str):
        """Log visualization captures."""
        self.debug("VISUALIZATION", f"Step {step:03d} rendered to {filename}")

    def _chunk_text(self, text: str, chunk_size: int) -> list:
        """Split text into chunks for logging."""
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    def get_log_path(self) -> Path:
        """Get the path to the current log file."""
        return self.log_file


# Global logger instance
_logger_instance = None

def get_logger() -> ExperimentLogger:
    """Get the global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ExperimentLogger()
    return _logger_instance

def setup_logger(log_file: str = "trace.log", log_level: int = logging.DEBUG) -> ExperimentLogger:
    """Alias for init_logger for backward compatibility."""
    return init_logger(log_file, log_level)

def init_logger(log_file: str = "trace.log", log_level: int = logging.DEBUG) -> ExperimentLogger:
    """Initialize the global logger."""
    global _logger_instance
    _logger_instance = ExperimentLogger(log_file, log_level)
    return _logger_instance

# Convenience functions for easy access
def debug(component: str, message: str):
    """Convenience function for debug logging."""
    get_logger().debug(component, message)

def info(component: str, message: str):
    """Convenience function for info logging."""
    get_logger().info(component, message)

def warning(component: str, message: str):
    """Convenience function for warning logging."""
    get_logger().warning(component, message)

def error(component: str, message: str):
    """Convenience function for error logging."""
    get_logger().error(component, message)

def critical(component: str, message: str):
    """Convenience function for critical logging."""
    get_logger().critical(component, message)


# Test the logger
if __name__ == "__main__":
    logger = init_logger("test_trace.log")

    logger.info("SYSTEM", "Logger test started")

    # Test different components
    debug("PLANNER", "This is a debug message")
    info("ENVIRONMENT", "This is an info message")
    warning("LLM", "This is a warning message")
    error("SIMULATION", "This is an error message")

    # Test PDDL logging
    sample_pddl = """(define (problem test)
  (:domain test-domain)
  (:goal (done))
)"""
    logger.log_pddl_content("PLANNER", "problem", "test.pddl", sample_pddl)

    # Test LLM interaction logging
    sample_prompt = "You are an AI assistant. Please decide whether to replan."
    sample_response = {
        "replan_needed": True,
        "reasoning": "The new store offers better prices",
        "new_entity": {"name": "store1", "type": "shop"}
    }
    logger.log_llm_interaction(sample_prompt, sample_response)

    logger.info("SYSTEM", "Logger test completed")
    print(f"Logs written to: {logger.get_log_path()}")
