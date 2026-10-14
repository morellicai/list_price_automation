import urllib3
import os
import requests
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()
urllib3.disable_warnings()

class LoginLogoutSapTest:
    def __init__(self):
        self.SAP_URL  = os.getenv("SAP_URL")
        self.SAP_DB   = os.getenv("SAP_DB_TEST")
        self.SAP_USER = os.getenv("SAP_USER")
        self.SAP_PASS = os.getenv("SAP_PASS")
        
    def login_sap(self):
        """Faz login no SAP B1 Service Layer e retorna os cookies de sessao."""
        resp = requests.post(
            f"{self.SAP_URL}/Login",
            json={
                "UserName": self.SAP_USER,
                "Password": self.SAP_PASS,
                "CompanyDB": self.SAP_DB
            },
            verify=False,
            timeout=15
        )

        if resp.status_code != 200:
            raise Exception(f"Falha no login SAP: {resp.text}")
        return resp.cookies


    def logout_sap(self, cookies):
        """Encerra a sessao no SAP B1."""
        try:
            requests.post(f"{self.SAP_URL}/Logout", cookies=cookies,
                        verify=False, timeout=10)
            print("  Sessao encerrada (logout)")
            return True
        except Exception:
            pass  # logout falhou, mas nao e critico
            return False