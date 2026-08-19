#!/usr/bin/env python3
import json
import os

DEFAULT_CONFIG = {
    "work_dir": "C:\\Users\\lenovo\\Desktop\\create接口\\app",
    "old_api_url": "https://support-daily.udeer.ai/api/workItem/appCreate",
    "new_api_url": "https://support-daily.udeer.ai/api/v2/internal/tickets/appCreate",
    "detail_url": "https://support-daily.udeer.ai/api/workItem/detail",
    "token": "",
    "detail_cookies": {}
}

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    config = load_config()
    print(json.dumps(config, ensure_ascii=False, indent=2))
