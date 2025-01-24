"""Configuration handling for FNUX XML Parser."""

import logging
from pathlib import Path
from typing import Dict, Any

import yaml

class ConfigurationError(Exception):
    """Raised when there are issues with the configuration."""
    pass

def load_llm_config(config_path: Path | None = None) -> Dict[Any, Any]:
    """Load and validate LLM configuration from YAML.
    
    Args:
        config_path: Optional path to config file. If not provided, looks in default locations.
        
    Returns:
        Dict containing the validated configuration.
        
    Raises:
        ConfigurationError: If config file is missing or invalid.
        FileNotFoundError: If the specified config file doesn't exist.
    """
    if config_path is None:
        # Look in standard locations
        possible_paths = [
            Path.cwd() / "config" / "llm_config.yaml",
            Path.cwd() / "llm_config.yaml",
            Path(__file__).parent.parent.parent / "config" / "llm_config.yaml",
        ]
        
        for path in possible_paths:
            if path.exists():
                config_path = path
                break
        else:
            raise ConfigurationError(
                "LLM configuration file not found in standard locations. "
                "Please provide a valid config file path."
            )
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Validate required configuration
    validate_llm_config(config)
    
    return config

def validate_llm_config(config: Dict[Any, Any]) -> None:
    """Validate the LLM configuration structure and required fields.
    
    Args:
        config: Configuration dictionary to validate.
        
    Raises:
        ConfigurationError: If any required fields are missing or invalid.
    """
    required_fields = [
        ('llm.base_url', lambda c: c['llm']['base_url']),
        ('llm.api_key', lambda c: c['llm']['api_key']),
        ('llm.model', lambda c: c['llm']['model']),
    ]
    
    for field, getter in required_fields:
        try:
            value = getter(config)
            if not value:
                raise ConfigurationError(f"Required field '{field}' is empty")
        except (KeyError, TypeError):
            raise ConfigurationError(f"Required field '{field}' is missing")

def setup_llm_logging(config: Dict[Any, Any]) -> None:
    """Setup logging based on configuration.
    
    Args:
        config: Configuration dictionary containing logging settings.
    """
    if config['llm'].get('logging', {}).get('enabled', False):
        logging_config = config['llm']['logging']
        log_file = Path(logging_config.get('file', 'llm_calls.log'))
        
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            filename=str(log_file),
            level=getattr(logging, logging_config.get('level', 'INFO')),
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
