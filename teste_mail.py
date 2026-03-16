import os
from dotenv import load_dotenv

# Carrega as credenciais e senhas do arquivo .env
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)

from core.email_util import send_newsletter_email

if __name__ == "__main__":
    email_destino = "richardjalgarve@gmail.com" # Altere para o seu e-mail de destino
    
    print("="*50)
    print(f"Testando envio via SMTP (Zoho)...")
    print(f"Remetente (FROM): {os.environ.get('SMTP_FROM', 'noticias@ia.por.ai')}")
    print("="*50)
    
    # Mockando uma notícia fake amigável só pra testar o layout renderizado!
    noticias_teste = [
        {
            "title": "Teste Bem-Sucedido: Seu app já sabe mandar e-mail pelo Zoho!",
            "url": "https://zoho.com/",
            "source": "Sistema IA por AI",
            "description": "Se você está lendo isso na sua caixa de entrada, significa que as credenciais do Zoho Mail informadas no seu arquivo .env estão perfeitas. O fluxo automático do Cron também vai dar certo! 🚀"
        }
    ]
    
    print(f"📡 Tentando disparar e-mail teste para: {email_destino} ...")
    
    sucesso = send_newsletter_email([email_destino], noticias_teste)
    
    print("="*50)
    if sucesso:
        print(f"✅ GOLAÇO! O E-mail teste foi enviado!")
        print(f"Vá no provedor do e-mail {email_destino} (pode cair no spam/lixo eletrônico no 1º disparo) e confira a Newsletter!")
    else:
        print(f"❌ DEU RUIM. O envio falhou!")
        print("Dicas pro Zoho Mail:")
        print("1. Verifique se o SMTP_USER e SMTP_PASSWORD estão corretos no arquivo .env;")
        print("2. Verifique se a porta é a apropriada (465 SSL ou 587 STARTTLS) e se o servidor é smtp.zoho.com;")
        print("3. Algumas contas podem precisar gerar uma 'Senha de Aplicativo' no painel de segurança do Zoho.")
        print("="*50)
