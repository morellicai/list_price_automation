import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()


class NotificadorEmail:
    def __init__(self):
        self.host = os.getenv("EMAIL_HOST")
        self.port = int(os.getenv("EMAIL_PORT"))
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
        if copias:
            if isinstance(copias, list):
                msg["Cc"] = ", ".join(copias)
            else:
                msg["Cc"] = copias

        # Envio seguro usando TLS / SSL
        try:
            if self.port == 465:
                server_ctx = smtplib.SMTP_SSL(self.host, self.port)
            else:
                server_ctx = smtplib.SMTP(self.host, self.port)

            with server_ctx as server:
                if self.port != 465:
                    server.starttls()  # Criptografa a conexão
                server.login(self.user, self.password)
                server.send_message(msg)
            print(f"E-mail enviado com sucesso para {destinatarios}!")
            return True
        except (smtplib.SMTPException, OSError) as e:
            print(f"Falha ao enviar e-mail: {e}")
            return False
