import feedparser
import requests
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fontes atualizadas com os 9 sites + originais
DEFAULT_FEEDS = [
    # {
    #     "url": "https://feeds.feedburner.com/TechCrunch",
    #     "name": "TechCrunch"
    # },
    # {
    #     "url": "https://venturebeat.com/category/ai/feed/",
    #     "name": "VentureBeat AI"
    # },
    # {
    #     "url": "https://canaltech.com.br/rss/ia/",
    #     "name": "Canaltech"
    # },
    # # ✅ NOVOS SITES COM RSS
    # {
    #     "url": "https://feeds.businessinsider.com/rss",
    #     "name": "Business Insider"
    # },
    # {
    #     "url": "https://techcrunch.com/feed",  # TechCrunch geral (melhor que categoria)
    #     "name": "TechCrunch"
    # },
    # {
    #     "url": "https://theguardian.com/technology/artificialintelligence/rss",
    #     "name": "The Guardian AI"
    # },
    # {
    #     "url": "fortune.com/rss",
    #     "name": "Fortune"
    # },
    # {
    #     "url": "https://feeds.arstechnica.com/arstechnica",
    #     "name": "Ars Technica"
    # },
    # {
    #     "url": "https://the-decoder.com/feed/",
    #     "name": "The Decoder"
    # },
    # 🔄 FALLBACKS (sem RSS nativo)
    {
        "url": "https://feeds.bloomberg.com/technology/news.rss",  # Community RSS
        "name": "Bloomberg Tech"
    }
    # Backnotprop sem RSS - pulado (pequeno demais)
]

def resolve_url(url: str) -> str:
    """Resolve os redirecionamentos do Google News para a URL final."""
    return url

def fetch_rss_links(feeds: Optional[List[Dict]]=None, max_per_feed: int = 3) -> List[Dict]:
    """
    Lista iterativa que varre as URLs RSS fornecidas,
    coletando os dados cruéis básicos das notícias (título e URL).
    """
    if feeds is None:
        feeds = DEFAULT_FEEDS
        
    articles_base = []
    
    for feed_source in feeds:
        try:
            feed = feedparser.parse(feed_source["url"])
            if feed.bozo:
                logger.warning(f"Aviso ao parsear o feed {feed_source['name']}")
                
            for entry in feed.entries[:max_per_feed]:
                articles_base.append({
                    "title": entry.title,
                    "url": entry.link,
                    "source": feed_source["name"],
                    "published": getattr(entry, "published", "")
                })
        except Exception as e:
            logger.error(f"Erro ao extrair do feed {feed_source['name']}: {e}")
            
    return articles_base

def fetch_google_news_top(query: str = "inteligência artificial", max_results: int = 5) -> List[Dict]:
    """
    Puxa notícias trending globais pelo Google News focado em IA.
    Depende da biblioteca pygooglenews.
    """
    try:
        from pygooglenews import GoogleNews
        gn = GoogleNews(lang='pt', country='BR')
        search_results = gn.search(query, when='1d')
        
        articles = []
        for item in search_results['entries'][:max_results]:
            final_url = resolve_url(item['link'])
            articles.append({
                "title": item['title'],
                "url": final_url,
                "source": item.get('source', {}).get('title', "Google News"),
                "published": getattr(item, 'published', "")
            })
        return articles
    except Exception as e:
        logger.error(f"Erro no módulo pygooglenews: {e}")
        return []