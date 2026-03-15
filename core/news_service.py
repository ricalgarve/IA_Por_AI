from typing import List, Dict
import random
from . import feed_parser
from . import article_extractor

def get_latest_news() -> List[Dict]:
    """
    Atua como maestro. Orquestra as requisições RSS do TechCrunch, Canaltech, etc,
    une com o que está trending no Google News e então opcionalmente
    chama ou simula a extração de resumos com o Newspaper3k/LLM.
    """
    
    # 1. Pega do Google News
    google_hot = feed_parser.fetch_google_news_top("Inteligência Artificial", max_results=4)
    # Define tudo vindo do Google como "hot" e veloz.
    for n in google_hot:
        n["temperature"] = "hot"
        
    # 2. Pega dos sites de base customizáveis
    rss_news = feed_parser.fetch_rss_links(max_per_feed=2)
    # Define de forma genérica/random por enquanto para dar cara legal no dashboard
    for n in rss_news:
        n["temperature"] = random.choice(["warm", "cold"])
        
    # 3. Une todas as listas e prepara para extração
    combined_base_news = google_hot + rss_news
    
    # 4. Chama a extração pesada (Resumos de cada site)
    # Obs: Estamos desabilitando (comentando) o bulk_extract temporariamente para evitar o peso do NLP do newspaper3k!
    # No Vercel, faremos de forma mais amena abaixo, gerando resumos mockados caso precisemos de velocidade.

    detailed_news = article_extractor.bulk_extract_articles(combined_base_news)

    
    # SIMULAÇÃO DE RESUMO PARA VELOCIDADE EXTREMA DE DEMONSTRAÇÃO DO LAYOUT
    # Assim podemos integrar aos poucos sem o timeout na tela.
    # detailed_news = []
    
    # for idx, item in enumerate(combined_base_news):
    #     # A API na sua estrutura de UI requer um ID numérico pra tratar a lógica de expand/collapse do accordion no javascript!
    #     item["id"] = idx + 1
        
    #     # O feedparser chama o titulo original dele. O newspaper as vezes chama de "extracted_title"
    #     # Vamos usar a var.description que voce usava nos MOCKs
    #     item["description"] = f"Resumo extraído da notícia original focada em Inteligência artificial da fonte: {item['source']}. Para ler a manchete inteira acesso os links originais, nós resumimos tudo. Você está lendo o resumo em formato de extração."
        
    #     detailed_news.append(item)
        
    # # Mistura tudo randomicamente pro dashboard ficar fluído
    # random.shuffle(detailed_news)
    
    # Consertar os IDs de UI depois do Shuffle de indices
    for index, d_item in enumerate(detailed_news):
         d_item["id"] = index + 1
         
    return detailed_news
