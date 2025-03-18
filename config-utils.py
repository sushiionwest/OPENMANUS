# desktop/utils/config.py
import os
import json
import logging
from PyQt6.QtCore import QSettings

# Default configuration
DEFAULT_CONFIG = {
    "appearance": {
        "theme": "light",
        "font_size": 12,
        "enable_animations": True
    },
    "editor": {
        "auto_save": True,
        "line_numbers": True,
        "spellcheck": True,
        "tab_size": 4
    },
    "api": {
        "timeout": 60,
        "retry_count": 3
    },
    "preferences": {
        "startup_session": "last",  # Options: "last", "new", "none"
        "save_prompt_on_run": True,
        "auto_detect_language": True
    },
    "advanced": {
        "log_level": "INFO",
        "max_history": 100,
        "sessions_path": ""  # Empty for default location
    }
}


def get_config_path():
    """Get the path to the config file"""
    config_dir = os.path.join(os.path.expanduser("~"), ".openmanus")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "config.json")


def load_config():
    """Load configuration from file, falling back to defaults for missing values"""
    config_path = get_config_path()
    config = DEFAULT_CONFIG.copy()
    
    # Also check QSettings for overrides
    settings = QSettings("OpenManus", "OpenManusRedo")
    
    try:
        # If config file exists, load it
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                
                # Update config with user values, preserving defaults for missing keys
                deep_update(config, user_config)
        
        # Check QSettings for overrides
        if settings.contains("appearance/theme"):
            config["appearance"]["theme"] = settings.value("appearance/theme")
        
        # Validate configuration
        validate_config(config)
        
        return config
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        # Fall back to default config
        return DEFAULT_CONFIG


def save_config(config):
    """Save configuration to file"""
    config_path = get_config_path()
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logging.error(f"Error saving configuration: {e}")
        return False


def get_setting(key, default=None):
    """Get a setting value with dot notation (e.g., 'appearance.theme')"""
    config = load_config()
    keys = key.split('.')
    
    try:
        value = config
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError):
        return default


def update_setting(key, value):
    """Update a setting value with dot notation"""
    config = load_config()
    keys = key.split('.')
    
    try:
        # Navigate to the correct nested dict
        target = config
        for k in keys[:-1]:
            target = target[k]
        
        # Update the value
        target[keys[-1]] = value
        
        # Save the updated config
        return save_config(config)
    except (KeyError, TypeError) as e:
        logging.error(f"Error updating setting {key}: {e}")
        return False


def deep_update(target, source):
    """Recursively update a nested dictionary"""
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            deep_update(target[key], value)
        else:
            target[key] = value


def validate_config(config):
    """Validate configuration values and fix any issues"""
    # Example validation: ensure theme is valid
    if config["appearance"]["theme"] not in ["light", "dark"]:
        config["appearance"]["theme"] = "light"
    
    # Ensure font size is reasonable
    if not 8 <= config["appearance"]["font_size"] <= 24:
        config["appearance"]["font_size"] = 12
    
    # Ensure log level is valid
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if config["advanced"]["log_level"] not in valid_log_levels:
        config["advanced"]["log_level"] = "INFO"
    
    # Set up custom sessions path if specified
    if config["advanced"]["sessions_path"]:
        # Ensure the directory exists
        os.makedirs(config["advanced"]["sessions_path"], exist_ok=True)


def reset_to_defaults():
    """Reset configuration to defaults"""
    return save_config(DEFAULT_CONFIG)
