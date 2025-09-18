import os
import yaml
from logger_config import logger

# Load client configs
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'clients.yml')

def load_client_configs():
    """Load client configurations from YAML file"""
    try:
        with open(CONFIG_PATH, 'r') as f:
            client_configs = yaml.safe_load(f)
        logger.info(f"Loaded client configs: {list(client_configs.keys())}")
        return client_configs
    except Exception as e:
        logger.error(f"Failed to load client configs: {e}")
        raise

def get_client_config(client_configs, client_id='default'):
    """Get configuration for a specific client or default if not found"""
    return client_configs.get(client_id, client_configs['default']) 