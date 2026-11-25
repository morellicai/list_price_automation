import logging
from collections.abc import Iterable
from typing import Any

import requests

from services.login_logout_sap import (
    TIMEOUT_PADRAO,
    LoginLogoutSap,
    criar_sessao_sap,
)


class ItensSap:
    def __init__(
        self,
        cookies: Any,
        sap_url: str | None,
        auth_service: LoginLogoutSap | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.cookies = cookies
        self.SAP_URL = sap_url
        self.auth_service = auth_service
        self.logger = logger
        self.session = auth_service.session if auth_service else criar_sessao_sap()

    def _registrar_log(self, nivel: str, mensagem: str) -> None:
        if self.logger is not None:
            getattr(self.logger, nivel)(mensagem)
        else:
            print(mensagem)

    def _requisitar(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        kwargs.setdefault("cookies", self.cookies)
        kwargs.setdefault("verify", False)
        kwargs.setdefault("timeout", TIMEOUT_PADRAO)

        response = self.session.request(method, url, **kwargs)

        # Sessões B1SESSION expiram após algumas horas em cargas longas.
        if response.status_code == 401 and self.auth_service is not None:
            self._registrar_log(
                "warning",
                "Sessão SAP expirada (HTTP 401). Renovando autenticação...",
            )
            self.cookies = self.auth_service.login_sap()
            kwargs["cookies"] = self.cookies
            response = self.session.request(method, url, **kwargs)
            self._registrar_log(
                "info", "Sessão SAP renovada com sucesso após HTTP 401."
            )

        response.raise_for_status()
        return response

    def atualizar_tabela_sap(self, *args: Any, **kwargs: Any) -> bool:
        """Atualiza preço de item na tabela do SAP B1 via PATCH."""
        if len(args) == 4:
            cookies, cod_item, price, table = args
        elif len(args) == 3:
            cod_item, price, table = args
            cookies = kwargs.get("cookies", self.cookies)
        else:
            cod_item = kwargs.get("cod_item")
            price = kwargs.get("price")
            table = kwargs.get("table")
            cookies = kwargs.get("cookies", self.cookies)

        self.cookies = cookies
        url = f"{self.SAP_URL}/Items('{cod_item}')"
        payload = {"ItemPrices": [{"PriceList": int(table), "Price": price}]}

        try:
            self._requisitar("PATCH", url, json=payload, cookies=self.cookies)
            return True
        except requests.exceptions.RequestException as exc:
            self._registrar_log("error", f"Erro ao atualizar {cod_item} no SAP: {exc}")
            return False

    def lista_atual_sap(
        self, cookies: Any, tabelas_alvo: Iterable[str | int]
    ) -> list[dict[str, Any]]:
        """Retorna os preços atuais do SAP B1 para as tabelas informadas."""
        self.cookies = cookies
        if isinstance(tabelas_alvo, (str, int)):
            alvo_set = {str(tabelas_alvo).strip()}
        else:
            alvo_set = {str(t).strip() for t in tabelas_alvo}

        tabelas_fmt = ", ".join(sorted(alvo_set))
        self._registrar_log(
            "info",
            f"Consultando preços no SAP para tabelas: {tabelas_fmt}",
        )
        sap_items: list[dict[str, Any]] = []
        url = f"{self.SAP_URL}/Items?$select=ItemCode,ItemPrices&$skip=0"

        while True:
            try:
                response = self._requisitar("GET", url, cookies=self.cookies)
                data = response.json()
                results = data.get("value", [])

                if not results:
                    break

                for item in results:
                    item_code = item.get("ItemCode")
                    if not item_code:
                        continue

                    for price_info in item.get("ItemPrices", []):
                        tab_id = str(price_info.get("PriceList")).strip()
                        if tab_id in alvo_set:
                            raw_price = price_info.get("Price")
                            if raw_price is None:
                                continue
                            try:
                                preco_sap = float(raw_price)
                            except (ValueError, TypeError):
                                continue

                            sap_items.append(
                                {
                                    "ItemCode": item_code,
                                    "PriceList": tab_id,
                                    "PriceSAP": preco_sap,
                                }
                            )

                next_link = data.get("odata.nextLink") or data.get("@odata.nextLink")
                if not next_link:
                    break

                url = (
                    next_link
                    if next_link.startswith("http")
                    else f"{self.SAP_URL}/{next_link.lstrip('/')}"
                )
            except requests.exceptions.RequestException as exc:
                self._registrar_log(
                    "error", f"Erro ao obter lista de preços no SAP: {exc}"
                )
                break

        self._registrar_log(
            "info", f"Total de registros obtidos do SAP: {len(sap_items)}"
        )
        return sap_items
