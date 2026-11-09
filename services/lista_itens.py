import requests


class ItensSap:
    def __init__(self, cookies, sap_url):
        self.cookies = cookies
        self.SAP_URL = sap_url

    def atualizar_tabela_sap(self, cod_item, price, table):
        """Atualiza tabela de preços no SAP B1"""
        try:
            requests.patch(
                f"{self.SAP_URL}/Items('{cod_item}')",
                json={"ItemPrices": [{"PriceList": int(table), "Price": price}]},
                cookies=self.cookies,
                verify=False,
                timeout=10,
            )
        except requests.exceptions.RequestException as e:
            print(f"Erro ao atualizar {cod_item} no SAP: {e}")

        print(
            f"{cod_item} na tabela {table} atualizado no SAP B1 com sucesso! Valor atualizado: {price}"
        )

    def lista_atual_sap(self, cookies, tabelas_alvo):
        """Retorna os preços atuais do SAP B1 apenas para as tabelas alvo informadas.

        Retorna uma lista de dicionários com:
        [
            {"ItemCode": "AB012B--00401250A", "PriceList": "7", "PriceSAP": 25.45},
            ...
        ]
        """
        if isinstance(tabelas_alvo, (str, int)):
            tabelas_alvo = {str(tabelas_alvo).strip()}
        else:
            tabelas_alvo = {str(t).strip() for t in tabelas_alvo}

        print(
            f"Obtendo preços atuais do SAP para as tabelas: {', '.join(tabelas_alvo)}..."
        )
        sap_items = []
        url = f"{self.SAP_URL}/Items?$select=ItemCode,ItemPrices&$skip=0"

        while True:
            try:
                response = requests.get(
                    url,
                    cookies=cookies,
                    verify=False,
                    timeout=10,
                )
                response.raise_for_status()
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
                        if tab_id in tabelas_alvo:
                            raw_price = price_info.get("Price")
                            if raw_price is not None:
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

                # Validação oficial OData: enquanto houver 'odata.nextLink', há mais páginas a consultar
                next_link = data.get("odata.nextLink") or data.get("@odata.nextLink")
                if not next_link:
                    break

                url = (
                    next_link
                    if next_link.startswith("http")
                    else f"{self.SAP_URL}/{next_link.lstrip('/')}"
                )
                print(f"  {len(sap_items)} registros coletados do SAP...")

            except requests.exceptions.RequestException as e:
                print(f"Erro ao obter lista de preços no SAP: {e}")
                break

        print(f"-> Total de registros obtidos do SAP: {len(sap_items)}\n")
        return sap_items
