import os
import logging
import smtplib
from email.message import EmailMessage

SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.zoho.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 465))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", SMTP_USER)
APP_URL = os.environ.get("APP_URL", "http://localhost:8000")

def send_newsletter_email(subscribers: list[dict], news_list: list[dict]):
    """
    Envia a newsletter para os assinantes ativos.
    subscribers: lista de dicts com 'email' e 'user_token'
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        logging.warning("Credenciais SMTP não configuradas. E-mail não enviado.")
        return False

    if not news_list:
        logging.info("Sem notícias para enviar na newsletter.")
        return False
        
    if not subscribers:
        logging.info("Sem assinantes para enviar na newsletter.")
        return False
        
    try:
        # Define se usa SMTP_SSL (porta 465) ou SMTP com starttls (porta 587)
        use_ssl = (SMTP_PORT == 465)
        
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) if use_ssl else smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        
        if not use_ssl:
            server.ehlo()
            server.starttls()
            
        server.login(SMTP_USER, SMTP_PASSWORD)
        
        enviados = 0
        for sub in subscribers:
            email_dest = sub["email"]
            user_token = sub.get("user_token", "")
            
            # Monta o link de cancelamento com o token do usuário
            unsubscribe_url = f"{APP_URL}/newsletter/cancelar?token={user_token}"
            
            # Monta o HTML do email
            html_content = """
            <div style="max-width: 600px; margin: 0 auto; font-family: 'Inter', Arial, sans-serif; background-color: #101822; color: #e2e8f0; padding: 32px; border-radius: 12px;">
                <div style="text-align: center; margin-bottom: 24px; border-bottom: 1px solid #1e293b; padding-bottom: 16px;">
                    <h1 style="color: #1973f0; font-size: 24px; font-weight: 800; text-transform: uppercase; font-style: italic; margin: 0;">IA por AI</h1>
                    <p style="color: #94a3b8; font-size: 12px; margin: 4px 0 0 0;">Seu portal de notícias sobre a IA aí pelo mundo</p>
                </div>
                <h2 style="color: #f1f5f9; font-size: 18px; margin-bottom: 20px;">Confira as principais notícias de IA do dia anterior:</h2>
            """
            
            for n in news_list:
                html_content += f"""
                <div style="margin-bottom: 16px; padding: 16px; background-color: #1e293b; border-radius: 8px; border-left: 3px solid #1973f0;">
                    <h3 style="margin: 0 0 8px 0;"><a href="{n['url']}" style="color: #60a5fa; text-decoration: none; font-size: 15px;">{n['title']}</a></h3>
                    <p style="color: #94a3b8; font-size: 13px; margin: 0 0 6px 0;">{n['description']}</p>
                    <span style="color: #64748b; font-size: 11px;">Fonte: {n['source']}</span>
                </div>
                """
            
            html_content += f"""
                <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #1e293b; text-align: center;">
                    <p style="color: #94a3b8; font-size: 13px;">Obrigado por assinar nossa newsletter!</p>
                    <p style="margin-top: 16px;">
                        <a href="{unsubscribe_url}" style="color: #64748b; font-size: 11px; text-decoration: underline;">
                            Não deseja mais receber estes e-mails? Clique aqui para cancelar
                        </a>
                    </p>
                </div>
            </div>
            """
            
            msg = EmailMessage()
            msg["Subject"] = "Sua Newsletter Diária - IA por AI"
            msg["From"] = f"IA por AI <{SMTP_FROM}>"
            msg["To"] = email_dest
            msg.set_content("Por favor, ative o formato HTML para ver este email.")
            msg.add_alternative(html_content, subtype='html')
            
            try:
                server.send_message(msg)
                enviados += 1
            except Exception as e_send:
                logging.error(f"Erro ao enviar para {email_dest}: {e_send}")
                
        server.quit()
        
        logging.info(f"Newsletter disparada via SMTP para {enviados} de {len(subscribers)} assinantes.")
        return True
    except Exception as e:
        logging.error(f"Erro ao enviar newsletter por SMTP: {e}")
        return False
