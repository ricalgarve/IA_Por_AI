import os
import logging
import smtplib
from email.message import EmailMessage

SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.zoho.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 465))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("SMTP_FROM", SMTP_USER)

def send_newsletter_email(to_emails: list[str], news_list: list[dict]):
    if not SMTP_USER or not SMTP_PASSWORD:
        logging.warning("Credenciais SMTP não configuradas. E-mail não enviado.")
        return False

    if not news_list:
        logging.info("Sem notícias para enviar na newsletter.")
        return False
        
    if not to_emails:
        logging.info("Sem assinantes para enviar na newsletter.")
        return False
        
    try:
        # O html do email
        html_content = "<h2>Confira as principais notícias de IA do dia anterior:</h2><br>"
        for n in news_list:
            html_content += f"<h3><a href='{n['url']}'>{n['title']}</a> ({n['source']})</h3>"
            html_content += f"<p>{n['description']}</p><br><hr>"
            
        html_content += "<br><p>Obrigado por assinar nossa newsletter!</p>"
        
        # Define se usa SMTP_SSL (porta 465) ou SMTP com starttls (porta 587)
        use_ssl = (SMTP_PORT == 465)
        
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) if use_ssl else smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        
        if not use_ssl:
            server.ehlo()
            server.starttls()
            
        server.login(SMTP_USER, SMTP_PASSWORD)
        
        enviados = 0
        for email_dest in to_emails:
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
        
        logging.info(f"Newsletter disparada via SMTP para {enviados} de {len(to_emails)} assinantes.")
        return True
    except Exception as e:
        logging.error(f"Erro ao enviar newsletter por SMTP: {e}")
        return False
