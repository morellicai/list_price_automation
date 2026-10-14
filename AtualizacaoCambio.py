from datetime import time
import requests
import urllib3
import os
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from datetime import date, timedelta, datetime
from services.login_logout_sap import LoginLogoutSap
from services.email_service import NotificadorEmail
from services.test_api import api_esta_online

load_dotenv()

SAP_URL  = os.getenv("SAP_URL")
SAP_DB   = os.getenv("SAP_DB")
SAP_USER = os.getenv("SAP_USER")
SAP_PASS = os.getenv("SAP_PASS")
DESTINATARIOS_EMAIL = os.getenv("DESTINATARIOS_EMAIL").split(",")

ASSUNTO = "Automação: Atualização da Lista de Preços"

urllib3.disable_warnings()

def atualizar_tabela_sap(cookies, moeda, taxa):
    """Envia a taxa de cambio para o SAP B1."""
    hoje_sap = date.today().strftime("%Y%m%d")
    resp = requests.post(
        f"{SAP_URL}/SBOBobService_SetCurrencyRate",
        json={
            "Currency": moeda,
            "Rate": str(taxa),
            "RateDate": hoje_sap
        },
        cookies=cookies,
        verify=False,
        timeout=15
    )
    if resp.status_code not in [200, 204]:
        raise Exception(f"Erro ao atualizar {moeda} no SAP: {resp.text}")
        
    print(f"  {moeda} atualizado no SAP B1 com sucesso!")

def tabela_precos():
    pass

# ── Execucao principal ──────────────────────────────────────

hour = datetime.now().hour
login_logout_SAP = LoginLogoutSap()
email = NotificadorEmail()

if hour >= 15:
    separador = "=" * 50

    cookies = None
    dados = []
    erros = []

    try:
        cookies = login_logout_SAP.login_sap()
        email.enviar(
            destinatarios="ti01@inconelinox.com.br",
            assunto=ASSUNTO + " - Login SAP",
            corpo_html="<p>Login Realizado pela automação no SAP</p>"
        )
        
        for price in 3:
            print(f"[ {price} ]")
            try:
                m,t = tabela_precos()
                dados.append((m,t))
                atualizar_tabela_sap(cookies, m, t)
            except Exception as e:
                msg = f"AVISO — {price}: {e}"
                email.enviar(
                    destinatarios=["ti01@inconelinox.com.br"], 
                    assunto=ASSUNTO + " - Atualizacao de Cambio", 
                    corpo_html=msg
                )
                erros.append(msg)

    except Exception as e:
        email.enviar(
            destinatarios="ti01@inconelinox.com.br",
            assunto=ASSUNTO + " - Erro no Login",
            corpo_html=f"<p>Erro geral no login do SAP: {str(e)}</p>"
        )
        erros.append(str(e))

    finally:
        if cookies:
            login_logout_SAP.logout_sap(cookies)
            email.enviar(
                destinatarios="ti01@inconelinox.com.br",
                assunto=ASSUNTO + " - Logout SAP", 
                corpo_html="<p>Logout Realizado no SAP</p>"
            )

    print(separador)

    if erros:
        print("  Concluido com avisos:")
        for e in erros:
            print(f"    - {e}")
        email.enviar(
            destinatarios=DESTINATARIOS_EMAIL,
            assunto="Automação: Atualizacao de Cambio - Concluido com Avisos", 
            corpo_html=f"""
                <p>Atualizacao de cambio finalizada com avisos:</p>
                """ + "".join(f"<p>{str(e)}</p>" for e in erros) + """
            """
        )
    else:
        email.enviar(
            destinatarios=DESTINATARIOS_EMAIL,
            assunto="Automação: Atualizacao de Cambio - Concluido com Sucesso", 
            corpo_html=f"""
                <p>Atualizacao de cambio finalizada com sucesso.</p>
                <p>Taxa Dolar Atualizada: {dados[0]}</p>
                <p>Taxa Euro Atualizada: {dados[1]}</p>
            """
        )