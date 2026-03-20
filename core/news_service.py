from typing import List, Dict
import random
from . import feed_parser
from . import article_extractor
import logging

logger = logging.getLogger(__name__)

def get_latest_news() -> List[Dict]:
    """
    Atua como maestro. Orquestra as requisições RSS do TechCrunch, Canaltech, etc,
    une com o que está trending no Google News e então opcionalmente
    chama ou simula a extração de resumos com o Newspaper3k/LLM.
    """
    
    # 1. Pega do Google News
    # google_hot = feed_parser.fetch_google_news_top("Inteligência Artificial", max_results=4)
    # # Define tudo vindo do Google como "hot" e veloz.
    # for n in google_hot:
    #     n["temperature"] = "hot"
        
    # 2. Pega dos sites de base customizáveis
    rss_news = feed_parser.fetch_rss_links(max_per_feed=2)
    
    # 3. Classifica a temperatura das notícias usando IA
    try:
        from .llm_processor import classify_temperature_with_llm
        titles = [n.get("title", "") for n in rss_news]
        temperatures = classify_temperature_with_llm(titles)
        for n, temp in zip(rss_news, temperatures):
            n["temperature"] = temp
    except Exception as e:
        logger.warning(f"Erro ao classificar temperaturas com IA, usando 'cold' como padrão: {e}")
        for n in rss_news:
            n["temperature"] = "cold"
        
    # 3. Une todas as listas e prepara para extração
    combined_base_news = rss_news
    
    # 4. Chama a extração pesada (Resumos de cada site)
    detailed_news = article_extractor.bulk_extract_articles(combined_base_news)

    # Mistura tudo randomicamente pro dashboard ficar fluído
    random.shuffle(detailed_news)
    
    # Consertar os IDs de UI depois do Shuffle de indices (se aplicável para javascript expand/collapse)
    for index, d_item in enumerate(detailed_news):
         d_item["id"] = index + 1
         
    return detailed_news
