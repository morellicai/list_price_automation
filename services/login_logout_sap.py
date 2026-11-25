import os
from typing import Any

import requests
import urllib3
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from requests.cookies import RequestsCookieJar
from urllib3.util.retry import Retry

load_dotenv()
urllib3.disable_warnings()

TIMEOUT_PADRAO: tuple[int, int] = (10, 60)


def criar_sessao_sap() -> requests.Session:
    """Cria uma sessão HTTP configurada com retry exponencial para o SAP."""
    # O SAP Service Layer usa POST/PATCH em login e carga; o urllib3 2.x
    # exige allowed_methods explícito para retentar métodos não idempotentes.
    estrategia_retry = Retry(
        total=5,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({'GET', 'POST', 'PATCH'}),
        raise_on_status=False,
    )
    adaptador = HTTPAdapter(max_retries=estrategia_retry)
    sessao = requests.Session()
    sessao.mount('https://', adaptador)
    sessao.mount('http://', adaptador)
    return sessao


class LoginLogoutSap:
    def __init__(self, session: requests.Session | None = None) -> None:
        self.SAP_URL = os.getenv('SAP_URL')
        self.SAP_DB = os.getenv('SAP_DB')
        self.SAP_USER = os.getenv('SAP_USER')
        self.SAP_PASS = os.getenv('SAP_PASS')
        self.session = session or criar_sessao_sap()

    def login_sap(self) -> RequestsCookieJar:
        """Autentica no SAP B1 Service Layer e retorna os cookies da sessão."""
        try:
            resp = self.session.post(
                f'{self.SAP_URL}/Login',
                json={
                    'UserName': self.SAP_USER,
                    'Password': self.SAP_PASS,
                    'CompanyDB': self.SAP_DB,
                },
                verify=False,
                timeout=TIMEOUT_PADRAO,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(f'Falha ao conectar ao SAP: {exc}') from exc

        self.session.cookies.update(resp.cookies)
        return resp.cookies

    def logout_sap(self, cookies: Any = None) -> bool:
        """Encerra a sessão ativa no SAP B1."""
        try:
            resp = self.session.post(
                f'{self.SAP_URL}/Logout',
                cookies=cookies,
                verify=False,
                timeout=TIMEOUT_PADRAO,
            )
            resp.raise_for_status()
            return True
        except requests.RequestException:
            return False
