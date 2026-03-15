import requests
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Pegamos a chave de ambiente e default
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
# Configura o LLM que usaremos no OpenRouter (como gemma, llama, mistral - de preferência grátis ou o que estiver pagando)
LLM_MODEL = os.environ.get("LLM_MODEL", "meta-llama/llama-3.3-70b-instruct:free") 

def call_openrouter(messages: list) -> str:
    """Função base que converte a lista de messages num request HTTP pro OpenRouter"""
    if not OPENROUTER_API_KEY:
        return "Estou passando por problemas técnicos no momento. Por favor, entre em contato pelo WhatsApp presente no site."
        
    url = os.environ.get("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000", # Will be updated safely when deployed
        "X-Title": "IA_Por_AI"
    }
    
    data = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 500
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        return "Desculpe, não consegui processar a resposta neste momento."
    except Exception as e:
        logger.error(f"Error calling OpenRouter: {e}")
        return "Desculpe, houve um erro ao tentar conectar ao meu cérebro virtual no momento. Você poderia tentar novamente em alguns instantes?"

def summarize_text_with_llm(text: str) -> str:
    """
    Recebe um texto longo (como o body de uma notícia) e usa um LLM via OpenRouter
    para retornar um resumo conciso.
    """
    if not text or len(str(text)) < 50:
        return str(text)
        
    # Prepara o prompt (se o texto for gigante, evitamos mandar tudo pra economizar tokens/evitar erro limit)
    safe_text = str(text)
    cutoff_text = safe_text[:8000] # +- 2000 words limit
    
    system_prompt = "Você é um jornalista de tecnologia sênior. Sua tarefa é ler notícias e retornar um resumo OBRIGATORIAMENTE em Português do Brasil (PT-BR). Se o texto fornecido estiver em inglês ou outro idioma, você DEVE traduzir para o Português. NUNCA responda em inglês."
    
    user_prompt = f"Resuma as informações principais da notícia a seguir em um único parágrafo conciso em Português (máximo 40 palavras). Não comece com 'A notícia diz' ou 'O resumo é'. Entregue direto o fato:\n\nNOTÍCIA:\n{cutoff_text}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    resumo = call_openrouter(messages)
    
    # Se bater no erro amigável criado pela API Base, disfarçamos cortando via local-fallback
    if "Desculpe, houve um erro" in resumo or "Estou passando por problemas técnicos" in resumo:
        return text[:250] + "..."
    
    return resumo.strip()
