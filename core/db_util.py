import os
import logging
from datetime import datetime
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def get_supabase() -> Client | None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def map_temp_to_int(temp: str) -> int:
    mapping = {"hot": 3, "warm": 2, "cold": 1}
    return mapping.get(temp, 1)

def map_int_to_temp(temp: int) -> str:
    mapping = {3: "hot", 2: "warm", 1: "cold"}
    return mapping.get(temp, "cold")

def load_news_from_db() -> list:
    """Carrega as notícias formatadas a partir do Supabase"""
    supabase = get_supabase()
    if not supabase:
        logging.error("Supabase não configurado. Adicione SUPABASE_URL e SUPABASE_KEY.")
        return []
        
    try:
        # Pega as últimas 50 notícias, ordenadas da mais recente
        response = supabase.table("noticias").select("*").order("data_noticia", desc=True).limit(50).execute()
        
        news = []
        for row in response.data:
            dt_str = row.get("data_noticia")
            news.append({
                "id": row.get("id"),
                "title": row.get("titulo"),
                "description": row.get("resumo"),
                "summary": row.get("resumo"), # retrocompatível
                "temperature": map_int_to_temp(row.get("temperatura", 1)),
                "source": row.get("fonte"),
                "url": row.get("url"),
                "published": dt_str
            })
        return news
    except Exception as e:
        logging.error(f"Erro lendo do Supabase: {e}")
        return []

def save_news_to_db(news_list: list) -> tuple[int, list]:
    """Grava as notícias no Supabase, evitando duplicatas por URL e por semântica (LLM) no mesmo dia"""
    supabase = get_supabase()
    if not supabase:
        logging.error("Supabase não configurado. Adicione SUPABASE_URL e SUPABASE_KEY.")
        return 0, ["Supabase não configurado"]
        
    warnings = []
    try:
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        start_of_day = f"{current_date_str}T00:00:00"
        end_of_day = f"{current_date_str}T23:59:59.999999"
        
        # Pega as URLs cadastradas (pra evitar reprocessos óbvios)
        existing_response = supabase.table("noticias").select("url").execute()
        existing_urls = {row["url"] for row in existing_response.data}
        
        # Pega os títulos já salvos DE HOJE para realizar a checagem com a IA
        existing_today_response = supabase.table("noticias").select("titulo").gte("data_noticia", start_of_day).lte("data_noticia", end_of_day).execute()
        existing_titles_today = [row["titulo"] for row in existing_today_response.data if row.get("titulo")]
        
        try:
            from core.llm_processor import check_semantic_duplicate_with_llm
        except ImportError:
            check_semantic_duplicate_with_llm = lambda a, b, c: False
            
        new_records = []
        for item in news_list:
            if item.get("url") in existing_urls:
                continue
                
            pub_str = item.get("published", "")
            data_noticia = None
            skip_old_news = False
            
            if pub_str:
                from dateutil.parser import parse as date_parse
                try:
                    dt = date_parse(pub_str)
                    dt_str = dt.strftime("%Y-%m-%d")
                    # Ignorar notícias de dias anteriores
                    if dt_str < current_date_str:
                        skip_old_news = True
                    data_noticia = dt.isoformat()
                except Exception:
                    pass
            
            if skip_old_news:
                titulo_log = item.get("title", "Sem Título")
                msg = f"Ignorando notícia antiga ({pub_str}): {titulo_log}"
                logging.info(msg)
                warnings.append(msg)
                continue
            
            if not data_noticia:
                data_noticia = datetime.now().isoformat()
                
            titulo_candidato = item.get("title", item.get("extracted_title", "Sem Título"))
            resumo_candidato = item.get("description", item.get("summary", ""))
            
            # Checa duplicidade semântica contra todas as publicadas hoje E as que acabaram de entrar no mesmo Cron
            is_dup = check_semantic_duplicate_with_llm(titulo_candidato, resumo_candidato, existing_titles_today)
            if is_dup:
                msg = f"LLM ignorou por ser duplicada na rodada atual: {titulo_candidato}"
                logging.info(msg)
                warnings.append(msg)
                continue
            
            # Anotamos na variável em memória pra não gravar a mesma notícia de outra fonte nos próximos loopings no mesmo Cron
            existing_titles_today.append(titulo_candidato)
            
            new_records.append({
                "titulo": titulo_candidato,
                "resumo": resumo_candidato,
                "temperatura": map_temp_to_int(item.get("temperature", "cold")),
                "fonte": item.get("source", "Desconhecida"),
                "url": item.get("url", ""),
                "data_noticia": data_noticia
            })
        
        if new_records:
            supabase.table("noticias").insert(new_records).execute()
            return len(new_records), warnings
            
        return 0, warnings
            
    except Exception as e:
        msg = f"Erro gravando no Supabase: {e}"
        logging.error(msg)
        raise e

def log_cron_execution(total_noticias: int, sucesso: bool, detalhes: dict):
    """Grava o log de execução do Cron na tabela log_atualizacoes"""
    supabase = get_supabase()
    if not supabase:
        logging.error("Supabase não configurado. Não foi possível gravar log_atualizacoes.")
        return
    try:
        # A coluna 'created_at' deve ser preenchida automaticamente pelo Supabase
        supabase.table("log_atualizacoes").insert({
            "total_noticias": total_noticias,
            "sucesso": sucesso,
            "detalhes": detalhes
        }).execute()
        logging.info("Log de atualização gravado com sucesso.")
    except Exception as e:
        logging.error(f"Erro gravando log na tabela log_atualizacoes: {e}")

def subscribe_newsletter(email: str) -> bool:
    """Inscreve um email na newsletter no Supabase"""
    supabase = get_supabase()
    if not supabase:
        raise ValueError("Supabase não configurado.")
        
    existing = supabase.table("newsletter").select("*").eq("email", email).execute()
    if not existing.data:
        supabase.table("newsletter").insert({"email": email}).execute()
        return True
    return False

# Apelidos para funções de load/save padrão para não quebrar locais que já usem
load_news_from_json = load_news_from_db
save_news_to_json = save_news_to_db

def log_interaction(ip: str, acao: str, id_noticia: int | None = None):
    """Grava o log de interação na tabela log_interacoes"""
    supabase = get_supabase()
    if not supabase:
        logging.error("Supabase não configurado. Não foi possível gravar log de interação.")
        return
    try:
        from typing import Any
        data: dict[str, Any] = {
            "IP": ip,
            "acao": acao
        }
        if id_noticia is not None:
            data["id_noticia"] = id_noticia
            
        supabase.table("log_interacoes").insert(data).execute()
        logging.info(f"Log de interação gravado: {acao} para IP {ip}")
    except Exception as e:
        logging.error(f"Erro gravando log na tabela log_interacoes: {e}")

def get_last_successful_update() -> str | None:
    supabase = get_supabase()
    if not supabase:
        return None
    try:
        response = supabase.table("log_atualizacoes").select("created_at").eq("sucesso", True).order("created_at", desc=True).limit(1).execute()
        if response.data:
            return response.data[0].get("created_at")
        return None
    except Exception as e:
        logging.error(f"Erro ao buscar última atualização: {e}")
        return None

def get_subscribers() -> list[str]:
    supabase = get_supabase()
    if not supabase:
        return []
    try:
        response = supabase.table("newsletter").select("email").execute()
        return [row["email"] for row in response.data]
    except Exception as e:
        logging.error(f"Erro ao buscar assinantes: {e}")
        return []

def get_yesterdays_news() -> list[dict]:
    supabase = get_supabase()
    if not supabase:
        return []
    try:
        from datetime import timedelta
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        start_of_yesterday = f"{yesterday_str}T00:00:00"
        end_of_yesterday = f"{yesterday_str}T23:59:59.999999"
        
        response = supabase.table("noticias").select("*").gte("data_noticia", start_of_yesterday).lte("data_noticia", end_of_yesterday).order("data_noticia", desc=True).execute()
        news = []
        for row in response.data:
            news.append({
                "title": row.get("titulo"),
                "description": row.get("resumo"),
                "url": row.get("url"),
                "source": row.get("fonte")
            })
        return news
    except Exception as e:
        logging.error(f"Erro ao buscar notícias de ontem: {e}")
        return []
