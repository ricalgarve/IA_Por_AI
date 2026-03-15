import os
from fastapi import FastAPI, Request, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from core.news_service import get_latest_news
from core.db_util import load_news_from_json, save_news_to_json

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



from dateutil.parser import parse as date_parse
from datetime import datetime
from typing import Optional

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, date: Optional[str] = None):
    # Agora o site principal NUNCA acessa a internet. Ele apenas lê o JSON de cache super rápido!
    cached_news = load_news_from_json()
    
    # Processar datas
    available_dates = set()
    parsed_news = []
    
    for item in cached_news:
        pub_str = item.get("published", "")
        extracted_date_str = None
        if pub_str:
            try:
                # Extraindo o objeto data do string RFC ou qualquer que for o RSS
                dt = date_parse(pub_str)
                extracted_date_str = dt.strftime("%Y-%m-%d")
                
                # Ignorar notícias antes de 14/03/2026
                if extracted_date_str < "2026-03-14":
                    continue
                    
                available_dates.add(extracted_date_str)
            except Exception:
                pass
        
        # Guardaremos a string no próprio objeto pelo menos pra facilitar a UI
        item["extracted_date"] = extracted_date_str
        parsed_news.append(item)
        
    dates_list = sorted(list(available_dates), reverse=True)
    
    # Se na barra de pesquisa for passada uma query ?date=...
    if date and date in dates_list:
        selected_date = date
    elif dates_list:
        selected_date = dates_list[0] # Default é o dia mais novo
    else:
        selected_date = None
        
    # Filtrar o payload pras noticias apenas do Selected Date
    if selected_date:
        filtered_news = [n for n in parsed_news if n.get("extracted_date") == selected_date]
    else:
        filtered_news = parsed_news
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "news": filtered_news,
        "available_dates": dates_list,
        "selected_date": selected_date
    })

@app.get("/api/cron/update-news")
async def force_update_news(api_key: str = Depends(verify_cron_secret)):
    """
    Rota a ser chamada via CRON JOB (ex: Vercel Cron, Github Actions, Cron-job.org) 
    toda meia-noite. Ela sim faz o scraping bruto assíncrono.
    """
    try:
        # A API roda o maestro demorado aqui embaixo dos panos
        new_articles = get_latest_news()
        
        # O Maestro retornou? Salva por cima no JSON
        if new_articles:
            save_news_to_json(new_articles)
            return {"status": "success", "message": f"{len(new_articles)} notícias atualizadas de forma offline."}
        else:
            return {"status": "error", "message": "Nenhuma notícia foi extraída das fontes."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
