import os

import requests
import urllib3
from dotenv import load_dotenv

load_dotenv()
urllib3.disable_warnings()


class LoginLogoutSap:
    def __init__(self):
        self.SAP_URL = os.getenv("SAP_URL")
        self.SAP_DB = os.getenv("SAP_DB")
        self.SAP_USER = os.getenv("SAP_USER")
        self.SAP_PASS = os.getenv("SAP_PASS")

    def login_sap(self):
        """Faz login no SAP B1 Service Layer e retorna os cookies de sessao."""
        try:
            resp = requests.post(
                f"{self.SAP_URL}/Login",
                json={
                    "UserName": self.SAP_USER,
                    "Password": self.SAP_PASS,
                    "CompanyDB": self.SAP_DB,
                },
                verify=False,
                timeout=15,
            )
        except requests.HTTPError as e:
            raise print(f"Falha ao conectar ao SAP: {e}")

        return resp.cookies

    def logout_sap(self, cookies):
        """Encerra a sessao no SAP B1."""
        try:
            requests.post(
                f"{self.SAP_URL}/Logout", cookies=cookies, verify=False, timeout=10
            )
            print("  Sessao encerrada (logout)")
            return True
        except requests.RequestException:
            return False
