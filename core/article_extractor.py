import newspaper
from newspaper import Article
import logging
import concurrent.futures
import os

logger = logging.getLogger(__name__)

def extract_article_content(url: str, lang: str = 'pt') -> dict:
    """
    Conecta num site através da biblioteca newspaper3k e extrai
    o corpo textual principal e resumo.
    """
    try:
        from core.newspaper_config import Config
    except ImportError:
        from newspaper import Config
    
    try:
        config = Config()
        config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        config.request_timeout = 10
        # Bloomberg and others often block with 403s.
        
        article = Article(url, language=lang, config=config)
        article.download()
        
        if article.download_state != 2:
            return {"success": False, "error": f"Scraping bloqueado ou falhou: state={article.download_state}"}
            
        article.parse()
        
        try:
            from core.llm_processor import summarize_text_with_llm
            # Tenta gerar o resumo limpo pela IA do OpenRouter!
            summary = summarize_text_with_llm(article.text)
            
            # Se a IA não fez muita coisa e limitou, tentamos fallback do próprio library se for vazio
            if not summary or str(summary).strip() == "" or "erro" in str(summary).lower():
                 if article.summary and str(article.summary).strip():
                      summary = article.summary
                 elif article.text:
                      summary = article.text[:250] + "..."
                 else:
                      summary = "Resumo indisponível."
            
        except ImportError:
             # Fallback caso não encontrem o lllm_processor.py por qualquer motivo (ainda que criei)
             try:
                 article.nlp()
                 summary = article.summary
             except Exception:
                 summary = article.text[:250] + "..." if article.text else "Resumo indisponível."
            
        return {
            "title": article.title,
            "text": article.text,
            "summary": summary,
            "top_image": getattr(article, "top_image", ""),
            "success": True
        }
    except Exception as e:
        logger.warning(f"Erro extraindo {url}: {e.__class__.__name__} - {str(e)[:100]}")
        return {"success": False, "error": "Artigo protegido por paywall ou Cloudflare"}

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
                        "description": extraction.get("summary", ""),
                        "original_text": extraction.get("text", "")
                    })
                else:
                    # TENTA PEGAR O CONTEÚDO ORIGINAL DO RSS SE NÃO DEU CERTO BAIXAR
                    rss_desc = base_item.get("description_rss", "")
                    if rss_desc:
                         import re
                         clean_desc = re.sub('<[^<]+?>', '', rss_desc) # remove tags HTML
                         fallback_desc = f"{clean_desc[:250]}..."
                    else:
                         fallback_desc = "Sem resumo disponível. Link direto para o artigo."

                    base_item.update({
                        "summary": fallback_desc,
                        "description": fallback_desc
                    })
                
                
                # ADIÇÃO: TRADUÇÃO PARA O PORTUGUÊS DA MANCHETE E DO RESUMO FINAL (se habilitado)
                use_translation = os.environ.get("USE_TRANSLATION", "true").lower() == "true"
                
                if use_translation:
                    try:
                         from deep_translator import GoogleTranslator
                         translator = GoogleTranslator(source='auto', target='pt')
                         
                         # Traduz o título original
                         if base_item.get("title"):
                              try:
                                  base_item["title"] = translator.translate(base_item["title"])
                              except Exception:
                                  pass
                                  
                         # Se o summary foi gerado por fallback do RSS ou Newspaper, usamos tradutor.
                         # O LLM natural (OpenRouter) já está com prompt para retornar 'Português-BR', mas
                         # para garantir uniformidade, se não usarmos limite caro, podemos só rodar em tudo se faltou pt
                         if base_item.get("summary") and "Sem resumo" not in base_item["summary"]:
                              try:
                                  # Só para assegurar o summary no payload.
                                  translated_sum = translator.translate(base_item["summary"])
                                  base_item["summary"] = translated_sum
                                  base_item["description"] = translated_sum
                              except Exception:
                                  pass
                    except Exception as ex:
                         logger.error(f"Erro no módulo de tradução opcional: {ex}")
                
                extracted_data.append(base_item)
                    
            except Exception as e:
                logger.error(f"Worker reportou falha ao processar {base_item.get('url')}: {e}")
                # CAIU NUM ERRO GRAVE NO WORKER: NÃO PERCA A NOTÍCIA. FAÇA FALLBACK PARA O RSS:
                rss_desc = base_item.get("description_rss", "")
                if rss_desc:
                    import re
                    clean_desc = re.sub('<[^<]+?>', '', str(rss_desc)) # remove tags HTML
                    fallback_desc = f"{clean_desc[:250]}..."
                else:
                    fallback_desc = "Sem resumo disponível. Link direto para o artigo."
                base_item.update({
                    "summary": fallback_desc,
                    "description": fallback_desc
                })
                extracted_data.append(base_item)
                
    return extracted_data
