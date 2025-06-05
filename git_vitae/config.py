"""Configuration management for Git Vitae."""

import os
import yaml
from pathlib import Path
from typing import Optional

from .models import Config


class ConfigManager:
    """Manages configuration loading and saving."""
    
    DEFAULT_CONFIG_PATH = Path.home() / ".git-vitae" / "config.yaml"
    
    @classmethod
    def load_config(cls, config_path: Optional[Path] = None) -> Config:
        """Load configuration from file or create default."""
        if config_path is None:
            config_path = cls.DEFAULT_CONFIG_PATH
            
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}
        else:
            config_data = {}
            
        # Environment variables take precedence over config file
        if os.getenv('OPENAI_API_KEY'):
            config_data['ai_api_key'] = os.getenv('OPENAI_API_KEY')
        elif os.getenv('ANTHROPIC_API_KEY'):
            config_data['ai_api_key'] = os.getenv('ANTHROPIC_API_KEY')
            
        return Config(**config_data)
    
    @classmethod
    def save_config(cls, config: Config, config_path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        if config_path is None:
            config_path = cls.DEFAULT_CONFIG_PATH
            
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = {
            'ai_provider': config.ai_provider,
            'ai_model': config.ai_model,
            'ai_api_key': config.ai_api_key,
            'scan_path': config.scan_path,
            'max_depth': config.max_depth,
            'include_hidden': config.include_hidden,
            'include_private': config.include_private,
            'ignore_patterns': config.ignore_patterns,
            'default_format': config.default_format,
            'default_template': config.default_template,
            'default_style': config.default_style,
            'include_metrics': config.include_metrics,
            'include_timeline': config.include_timeline,
            'group_by_language': config.group_by_language,
            'anonymize_data': config.anonymize_data,
            'allow_sensitive_data': config.allow_sensitive_data,
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False)
    
    @classmethod
    def create_default_config(cls) -> str:
        """Create default configuration file."""
        default_config = Config()
        cls.save_config(default_config)
        return str(cls.DEFAULT_CONFIG_PATH)