import os
import json
from datetime import datetime

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
NEWS_JSON_FILE = os.path.join(DATA_PATH, "news.json")

def ensure_data_dir():
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

def load_news_from_json() -> list:
    """Carrega as notícias formatadas a partir do arquivo JSON"""
    if not os.path.exists(NEWS_JSON_FILE):
        return []
    try:
        with open(NEWS_JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("news", [])
    except Exception as e:
        import logging
        logging.error(f"Erro lendo JSON: {e}")
        return []

def save_news_to_json(news_list: list):
    """Grava as notícias e a hora de atualização num JSON"""
    ensure_data_dir()
    data = {
        "last_updated": datetime.now().isoformat(),
        "news": news_list
    }
    with open(NEWS_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
