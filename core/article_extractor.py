import newspaper
from newspaper import Article
import logging
import concurrent.futures

logger = logging.getLogger(__name__)

def extract_article_content(url: str, lang: str = 'pt') -> dict:
    """
    Conecta num site através da biblioteca newspaper3k e extrai
    o corpo textual principal e resumo.
    """
    try:
        article = Article(url, language=lang)
        article.download()
        article.parse()
        
        # Como o Vercel não tem NTLK instalado como global sem requirements dificeis,
        # Nós usamos processamento de slice se o NLP.summary() der erro.
        try:
            article.nlp()
            summary = article.summary
        except Exception:
            # Fallback para extrair um pedaço do texto em vez da biblioteca pesada de NLP
            summary = article.text[:250] + "..." if article.text else ""
            
        return {
            "title": article.title,
            "text": article.text,
            "summary": summary,
            "top_image": getattr(article, "top_image", ""),
            "success": True
        }
    except Exception as e:
        logger.error(f"Erro extraindo {url}: {e}")
        return {"success": False, "error": str(e)}

def bulk_extract_articles(articles_base: list, max_workers: int = 3) -> list:
    """
    Roda um mapeamento em paralelo para vários links buscando ganhar tempo.
    Pode causar erro de timeout do Vercel se os sites bloquearem Scraping.
    No futuro, se passarmos para um LLM seria feito passo a passo aqui.
    """
    extracted_data = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Preparamos os jobs baseados na propriedade URL de cada dict base de nossos RSS
        future_to_article = {
            executor.submit(extract_article_content, item["url"]): item 
            for item in articles_base
        }
        
        for future in concurrent.futures.as_completed(future_to_article):
            base_item = future_to_article[future]
            try:
                extraction = future.result()
                if extraction.get("success"):
                    # Aqui teríamos o lugar certinho que enviariámos:
                    # 'extraction["text"]' para sua Key de LLM (GPT, Gemini, Claude)
                    # para ele retornar um parágrafo perfeitinho no lugar do summary
                    
                    base_item.update({
                        "extracted_title": extraction.get("title", ""),
                        "summary": extraction.get("summary", ""),
                        "original_text": extraction.get("text", "")
                    })
                else:
                    base_item.update({"summary": "Sem resumo disponível. Link direto para o artigo."})
                
                extracted_data.append(base_item)
                    
            except Exception as e:
                logger.error(f"Worker reportou falha: {e}")
                
    return extracted_data
