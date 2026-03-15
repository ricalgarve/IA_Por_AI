import requests
import os
import logging
from typing import Optional
import warnings

# Suprime os avisos de SyntaxWarning (falsos positivos do log 'error' da Vercel) causados pela biblioteca newspaper3k 
warnings.filterwarnings("ignore", category=SyntaxWarning)

logger = logging.getLogger(__name__)

# Pegamos a chave de ambiente e default
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
# Configura o LLM que usaremos no OpenRouter (como gemma, llama, mistral - de preferência grátis ou o que estiver pagando)
LLM_MODEL = os.environ.get("LLM_MODEL", "meta-llama/llama-3.3-70b-instruct:free") 

# Chave global (boolean flag) para usar o LLM ou apenas os text-truncates brutos
USE_LLM = os.environ.get("USE_LLM", "true").lower() == "true"

def call_openrouter(messages: list) -> str:
    """Função base que converte a lista de messages num request HTTP pro OpenRouter"""
    if not USE_LLM:
        return "Estou passando por problemas técnicos" # O fallback do summarize_text cuida do truncate bruto
        
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
        # O Gemini 2.5 Flash é um modelo gratuito MUITO rápido (diminiu as chances do Read Timed Out da Vercel)
        "model": os.environ.get("LLM_MODEL", "google/gemini-2.5-flash"),
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 500
    }
    
    try:
        # TIMEOUT AUMENTADO para 30 SEGUNDOS
        response = requests.post(url, headers=headers, json=data, timeout=30)
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

def check_semantic_duplicate_with_llm(new_title: str, new_summary: str, existing_titles: list) -> bool:
    """
    Verifica se a nova notícia já existe na base do dia atual, comparando com os títulos 
    das notícias já cadastradas usando um modelo de IA como juiz.
    """
    if not existing_titles or not USE_LLM:
        return False
        
    titles_text = "\n".join([f"- {t}" for t in existing_titles])
    
    system_prompt = "Você é um juiz avaliador de similaridade de textos. O usuário te enviará as manchetes do dia e uma NOVA notícia. Se a NOVA notícia se referir exatamente ao mesmo evento, assunto principal ou lançamento de alguma das manchetes já presentes na lista, você DEVE responder apenas 'SIM'. Caso seja uma notícia genuinamente nova e diferente, responda apenas 'NAO'. Não adicione justificativas."
    
    user_prompt = f"MANCHETES JÁ EXISTENTES DE HOJE:\n{titles_text}\n\nNOVA NOTÍCIA A AVALIAR:\nTítulo: {new_title}\nResumo: {new_summary}\n\nEssa nova notícia retrata o mesmo evento de alguma das manchetes acima? Responda SIM ou NAO."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    response = call_openrouter(messages)
    
    if response and "SIM" in response.upper() and ("NAO" not in response.upper() or response.upper().index("SIM") < response.upper().index("NAO")):
        return True
        
    return False
