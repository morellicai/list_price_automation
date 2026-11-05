import os
from datetime import datetime

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

        if resp.status_code != 200:
            raise Exception(f"Falha no login SAP: {resp.text}")  # noqa: TRY002
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
            # logout falhou, mas nao e critico
            return False


class AtualizaTaxa:
    def __init__(self):
        self.SAP_URL = os.getenv("SAP_URL")

    def atualizar_taxa_sap(self, cookies, moeda, taxa):
        """Atualiza a taxa de câmbio no SAP B1 Service Layer."""
        hoje_sap = datetime.now().strftime("%Y-%m-%d")
        resp = requests.post(
            f"{self.SAP_URL}/SBOBobService_SetCurrencyRate",
            json={"Currency": moeda, "Rate": str(taxa), "RateDate": hoje_sap},
            cookies=cookies,
            verify=False,
            timeout=15,
        )
        if resp.status_code not in [200, 204]:
            raise RuntimeError(f"Erro ao atualizar {moeda} no SAP: {resp.text}")

        print(f"  {moeda} atualizado no SAP B1 com sucesso!")
