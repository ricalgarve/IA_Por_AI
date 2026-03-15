import requests
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Pegamos a chave de ambiente e default
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
# Configura o LLM que usaremos no OpenRouter (como gemma, llama, mistral - de preferência grátis ou o que estiver pagando)
LLM_MODEL = os.environ.get("LLM_MODEL", "meta-llama/llama-3.3-70b-instruct:free") 

def summarize_text_with_llm(text: str) -> str:
    """
    Recebe um texto longo (como o body de uma notícia) e usa um LLM via OpenRouter
    para retornar um resumo conciso.
    """
    if not OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY não configurada. Usando fallback de parse local.")
        return str(text)[:250] + "..." if text else ""
        
    if not text or len(str(text)) < 50:
        return str(text)
        
    # Prepara o prompt (se o texto for gigante, evitamos mandar tudo pra economizar tokens/evitar erro limit)
    safe_text = str(text)
    cutoff_text = safe_text[:8000] # +- 2000 words limit
    
    system_prompt = "Você é um jornalista de tecnologia sênior. Sua tarefa é ler notícias e retornar um resumo OBRIGATORIAMENTE em Português do Brasil (PT-BR). Se o texto fornecido estiver em inglês ou outro idioma, você DEVE traduzir para o Português. NUNCA responda em inglês."
    
    user_prompt = f"Resuma as informações principais da notícia a seguir em um único parágrafo conciso em Português (máximo 40 palavras). Não comece com 'A notícia diz' ou 'O resumo é'. Entregue direto o fato:\n\nNOTÍCIA:\n{cutoff_text}"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000", # Recomendação da OpenRouter
        "X-Title": "IA_Por_AI",
    }
    
    payload = {
        "model": LLM_MODEL, 
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 100
    }
    
    try:
        response = requests.post(
            os.environ.get("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions"), 
            headers=headers,
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        
        choices = data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "").strip()
        else:
            return "Resumo não disponível."
    except Exception as e:
        logger.error(f"Erro chamando OpenRouter LLM: {e}")
        return text[:250] + "..." if text else ""
