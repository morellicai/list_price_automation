import smtplib
import os
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from email.message import EmailMessage

load_dotenv()

class NotificadorEmail:
    def __init__(self):
        self.host = os.getenv("EMAIL_HOST")
        self.port = int(os.getenv("EMAIL_PORT", 587))
        self.user = os.getenv("EMAIL_USER")
        self.password = os.getenv("EMAIL_PASS")

    def enviar(
        self, destinatarios, assunto, corpo_html, caminhos_anexos=None, copias=None
    ):
        msg = EmailMessage()
        msg["Subject"] = assunto
        msg["From"] = self.user
        if isinstance(destinatarios, list):
            msg["To"] = ", ".join(destinatarios)
        else:
            msg["To"] = destinatarios

        # Define o conteúdo do e-mail como HTML
        msg.set_content(corpo_html, subtype="html")

        # Adicionar arquivos em anexo (planilhas, PDFs, etc.)
        if caminhos_anexos:
            for caminho in caminhos_anexos:
                if os.path.exists(caminho):
                    with open(caminho, "rb") as f:
                        dados_arquivo = f.read()
                        nome_arquivo = os.path.basename(caminho)

                    # Adiciona o anexo de forma genérica (octet-stream)
                    msg.add_attachment(
                        dados_arquivo,
                        maintype="application",
                        subtype="octet-stream",
                        filename=nome_arquivo,
                    )
                else:
                    print(f"Aviso: O anexo {caminho} não foi encontrado.")

        # Envio seguro usando TLS
        try:
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()  # Criptografa a conexão
                server.login(self.user, self.password)
                server.send_message(msg)
            print(f"E-mail enviado com sucesso para {destinatarios}!")
        except Exception as e:
            print(f"Falha ao enviar e-mail: {e}")