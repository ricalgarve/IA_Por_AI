import os
import logging
from fastapi import FastAPI, Request, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from core.news_service import get_latest_news
from core.db_util import load_news_from_db, save_news_to_db

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

CRON_SECRET = os.environ.get("CRON_SECRET", "segredo_local_teste")
security = HTTPBearer()

def verify_cron_secret(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != CRON_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials.credentials

app = FastAPI(title="Notícias Rápidas - IA por AI")

# Define base path to ensure templates are found whether run locally or on Vercel
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=templates_dir)

from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

from dateutil.parser import parse as date_parse
from datetime import datetime
from typing import Optional

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, date: Optional[str] = None):
    # Busca as datas disponíveis (DISTINCT da base de dados)
    from core.db_util import get_available_dates, load_news_by_date
    dates_list = get_available_dates()
    
    # Se uma data foi selecionada, carrega as notícias daquele dia específico
    if date and date in dates_list:
        selected_date = date
        db_news = load_news_by_date(selected_date)
    elif dates_list:
        # Caso contrário, usa o dia mais recente
        selected_date = dates_list[0]
        db_news = load_news_by_date(selected_date)
    else:
        selected_date = None
        db_news = load_news_from_db()
    
    # Processar notícias
    parsed_news = []
    
    for item in db_news:
        pub_str = item.get("published", "")
        extracted_date_str = None
        formatted_date = None
        if pub_str:
            try:
                # Extraindo o objeto data do string RFC ou qualquer que for o RSS
                dt = date_parse(pub_str)
                extracted_date_str = dt.strftime("%Y-%m-%d")
                formatted_date = dt.strftime("%d/%m/%Y %H:%M")
            except Exception as e:
                logging.warning(f"Erro ao parsear data '{pub_str}': {e}")
                # Se não conseguir extrair data, usa a data de hoje
                now = datetime.now()
                extracted_date_str = now.strftime("%Y-%m-%d")
                formatted_date = now.strftime("%d/%m/%Y %H:%M")
        else:
            # Se não tem data publicada, usa a de hoje
            now = datetime.now()
            extracted_date_str = now.strftime("%Y-%m-%d")
            formatted_date = now.strftime("%d/%m/%Y %H:%M")
        
        # Guardaremos a string no próprio objeto pelo menos pra facilitar a UI
        item["extracted_date"] = extracted_date_str
        item["formatted_date"] = formatted_date
        parsed_news.append(item)
    
    # Todas as notícias carregadas são da data selecionada
    filtered_news = parsed_news
        
    try:
        from core.db_util import log_interaction
        client_ip = request.client.host if request.client else "unknown"
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(",")[0].strip()
        acao = "filtro_data" if date else "acesso_home"
        log_interaction(ip=client_ip, acao=acao)
    except Exception:
        pass
    
    try:
        from core.db_util import get_last_successful_update
        last_update_raw = get_last_successful_update()
        if last_update_raw:
            from datetime import timedelta
            dt_update = date_parse(last_update_raw)
            # Ajusta para UTC-3 (Brazil)
            dt_update = dt_update - timedelta(hours=3)
            last_update = dt_update.strftime("%d/%m/%Y às %H:%M")
        else:
            last_update = None
    except Exception:
        last_update = None
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "news": filtered_news,
        "available_dates": dates_list,
        "selected_date": selected_date,
        "last_update": last_update
    })

import traceback
from pydantic import BaseModel

class NewsletterSub(BaseModel):
    email: str

@app.post("/api/newsletter/subscribe")
async def api_subscribe_newsletter(sub: NewsletterSub):
    try:
        from core.db_util import subscribe_newsletter
        success = subscribe_newsletter(sub.email)
        if success:
            return {"status": "success", "message": "Inscrição realizada com sucesso!"}
        else:
            return {"status": "info", "message": "Este e-mail já está inscrito."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news/by-date/{date_str}")
async def api_get_news_by_date(date_str: str):
    """
    Retorna as notícias de uma data específica em formato JSON
    """
    try:
        from core.db_util import load_news_by_date
        news = load_news_by_date(date_str)
        return {"status": "success", "news": news}
    except Exception as e:
        logging.error(f"Erro ao buscar notícias para {date_str}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cron/update-news")
async def force_update_news(api_key: str = Depends(verify_cron_secret)):
    """
    Rota a ser chamada via CRON JOB (ex: Vercel Cron, Github Actions, Cron-job.org) 
    toda meia-noite. Ela sim faz o scraping bruto assíncrono.
    """
    try:
        from core.db_util import log_cron_execution
        
        # A API roda o maestro demorado aqui embaixo dos panos
        new_articles = get_latest_news()
        
        # O Maestro retornou? Salva por cima no DB
        if new_articles:
            inserted_count, warnings = save_news_to_db(new_articles)
            
            detalhes = {
                "message": f"Tentativa de salvar {len(new_articles)} artigos extraídos.",
                "warnings": warnings,
                "inserted_count": inserted_count
            }
            log_cron_execution(total_noticias=inserted_count, sucesso=True, detalhes=detalhes)
            
            return {"status": "success", "message": f"{inserted_count} notícias atualizadas de forma offline."}
        else:
            log_cron_execution(total_noticias=0, sucesso=True, detalhes={"message": "Nenhuma notícia nova foi retornada pelos feeds/LLM."})
            return {"status": "success", "message": "Nenhuma notícia foi extraída das fontes."}
            
    except Exception as e:
        # Pega a linha exata e a causa do erro na Vercel
        error_trace = traceback.format_exc()
        print(f"ERRO CRÍTICO no Cron Job:\n{error_trace}")
        
        try:
            from core.db_util import log_cron_execution
            detalhes_erro = {
                "error": str(e),
                "trace": error_trace
            }
            log_cron_execution(total_noticias=0, sucesso=False, detalhes=detalhes_erro)
        except Exception as log_error:
            print(f"Erro ao tentar gravar o trace na tabela de log: {log_error}")
            
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cron/send-newsletter")
async def send_newsletter_cron(api_key: str = Depends(verify_cron_secret)):
    """
    Rota a ser chamada às 6 da manhã. 
    Busca as pessoas inscritas e dispara as notícias do dia anterior pra elas.
    """
    try:
        from core.db_util import get_subscribers, get_yesterdays_news
        from core.email_util import send_newsletter_email
        
        subs = get_subscribers()
        news = get_yesterdays_news()
        
        success = send_newsletter_email(subs, news)
        if success:
            return {"status": "success", "message": f"Newsletter enviada para {len(subs)} assinantes contendo {len(news)} notícias."}
        else:
            return {"status": "info", "message": "Nenhum disparo realizado. Pode não haver notícias, assinantes, ou credenciais SMTP ausentes."}
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERRO CRÍTICO no envio de Newsletter:\n{error_trace}")
        raise HTTPException(status_code=500, detail=str(e))

class LogInteraction(BaseModel):
    id_noticia: Optional[int] = None
    acao: str

@app.post("/api/log")
async def api_log_interaction(request: Request, log_data: LogInteraction):
    client_ip = request.client.host if request.client else "unknown"
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        client_ip = x_forwarded_for.split(",")[0].strip()

    try:
        from core.db_util import log_interaction
        log_interaction(ip=client_ip, acao=log_data.acao, id_noticia=log_data.id_noticia)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
