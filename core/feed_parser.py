import feedparser
import requests
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fontes atualizadas com os 9 sites + originais
DEFAULT_FEEDS = [
    {
        "url": "https://techcrunch.com/feed",
        "name": "TechCrunch"
    },
    {
        "url": "https://feeds.arstechnica.com/arstechnica",
        "name": "Ars Technica"
    },
    {
        "url": "https://feeds.businessinsider.com/rss",
        "name": "Business Insider"
    },
    {
        "url": "https://theguardian.com/technology/artificialintelligence/rss",
        "name": "The Guardian AI"
    },
    {
        "url": "https://fortune.com/rss",
        "name": "Fortune"
    },
    {
        "url": "https://the-decoder.com/feed/",
        "name": "The Decoder"
    },
    {
        "url": "https://feeds.bloomberg.com/technology/news.rss",
        "name": "Bloomberg Tech"
    }
]

def resolve_url(url: str) -> str:
    """Resolve os redirecionamentos do Google News para a URL final."""
    return url

import re

AI_KEYWORDS = [
    r'\bai\b', r'artificial intelligence', r'inteligência artificial', r'\bllm\b', r'chatgpt',
    r'openai', r'gemini', r'anthropic', r'claude', r'machine learning', r'deep learning', r'midjourney'
]
AI_PATTERN = re.compile('|'.join(AI_KEYWORDS), re.IGNORECASE)

def is_ai_related(text: str) -> bool:
    if not text:
        return False
    return bool(AI_PATTERN.search(text))

def fetch_rss_links(feeds: Optional[List[Dict]]=None, max_per_feed: int = 3) -> List[Dict]:
    """
    Lista iterativa que varre as URLs RSS fornecidas,
    coletando os dados cruéis básicos das notícias (título e URL).
    Filtra os resultados para apenas retornarem notícias de IA.
    """
    if feeds is None:
        feeds = DEFAULT_FEEDS
        
    articles_base = []
    
    for feed_source in feeds:
        try:
            feed = feedparser.parse(feed_source["url"])
            if getattr(feed, "bozo", 0):
                logger.warning(f"Aviso ao parsear o feed {feed_source['name']}")
                
            count = 0
            for entry in getattr(feed, "entries", []):
                if count >= max_per_feed:
                    break
                    
                title = getattr(entry, "title", "")
                description = getattr(entry, "summary", getattr(entry, "description", ""))
                
                # Filtra as notícias para o tema de Inteligência Artificial
                if not (is_ai_related(title) or is_ai_related(description)):
                    continue

                articles_base.append({
                    "title": title,
                    "url": getattr(entry, "link", ""),
                    "source": feed_source["name"],
                    "published": getattr(entry, "published", ""),
                    "description_rss": description
                })
                count += 1
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