import csv
import os
import time
from datetime import timedelta
from pathlib import Path

import pandas as pd
import urllib3

urllib3.disable_warnings()


import requests

# pyrefly: ignore [missing-import]
from services.email_service import NotificadorEmail
from services.login_logout_sap import LoginLogoutSap

arquivos_txt = Path("src").glob("*.txt")
assunto = "Automação: Atualização da Lista de Preços"
SAP_URL = os.getenv("SAP_URL")


def limpar_preco(valor_str: str) -> float | None:
    """
    Converte 'R$ 28,87' para float (28.87).

    Retorna None se o valor for inválido (ex: '#N/D', '#VALOR!').
    """
    texto_limpo = (
        valor_str.replace("R$", "")
        .replace(" ", "")
        .replace(".", "")
        .replace(",", ".")
        .strip()
    )
    try:
        return float(texto_limpo)
    except ValueError:
        return None


def atualizar_tabela_sap(cookies, cod_item, price, table):
    """Atualiza tabela de preços no SAP B1"""
    try:
        requests.patch(
            f"{SAP_URL}/Items('{cod_item}')",
            json={"ItemPrices": [{"PriceList": int(table), "Price": price}]},
            cookies=cookies,
            verify=False,
            timeout=10,
        )
    except requests.exceptions.RequestException as e:
        print(f"Erro ao atualizar {cod_item} no SAP: {e}")

    print(
        f"{cod_item} na tabela {table} atualizado no SAP B1 com sucesso! Valor atualizado: {price}"
    )


def lista_atual_sap(cookies, tabelas_alvo):
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

    print(f"Obtendo preços atuais do SAP para as tabelas: {', '.join(tabelas_alvo)}...")
    sap_items = []
    url = f"{SAP_URL}/Items?$select=ItemCode,ItemPrices&$skip=0"

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

                            sap_items.append({
                                "ItemCode": item_code,
                                "PriceList": tab_id,
                                "PriceSAP": preco_sap,
                            })

            # Validação oficial OData: enquanto houver 'odata.nextLink', há mais páginas a consultar
            next_link = data.get("odata.nextLink") or data.get("@odata.nextLink")
            if not next_link:
                break

            url = (
                next_link
                if next_link.startswith("http")
                else f"{SAP_URL}/{next_link.lstrip('/')}"
            )
            print(f"  {len(sap_items)} registros coletados do SAP...")

        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter lista de preços no SAP: {e}")
            break

    print(f"-> Total de registros obtidos do SAP: {len(sap_items)}\n")
    return sap_items


# Lista para armazenar os itens processados para o payload
itens_payload = []
itens_invalidos = []
lista_preco_id = []
print("Iniciando processamento dos arquivos TXT...")
for arquivo in arquivos_txt:
    with open(arquivo, mode="r", encoding="utf-16") as f:
        # O DictReader utiliza a 1ª linha como chave de cada coluna
        leitor = csv.DictReader(f, delimiter="\t")

        for linha in leitor:
            # Código do item
            item_code = linha.get("Nº do item", "").strip()
            preco_bruto = (
                linha.get("Nº do item, Preço unitário")
                or linha.get("Preço unitário")
                or ""
            ).strip()
            table = linha.get("Nº da lista de preços", "").strip()

            preco_unitario = limpar_preco(preco_bruto)

            # Se o preço vier como '#N/D' ou '#VALOR!', você pode ignorar ou tratar
            if preco_unitario is None:
                itens_invalidos.append(
                    {"ItemCode": item_code, "PrecoOriginal": preco_bruto}
                )
                continue

            item_data = {
                "PriceList": table,
                "ItemCode": item_code,
                "Price": preco_unitario,
            }

            itens_payload.append(item_data)
            lista_preco_id.append(table)

print(
    f"Total de listas ({len(set(lista_preco_id))}) e itens válidos no arquivo: {len(itens_payload)}\n"
)

if itens_payload:
    login_logout_SAP = LoginLogoutSap()
    email = NotificadorEmail()
    df_payload = pd.DataFrame(itens_payload)
    print("Iniciando processo de login no SAP...")
    try:
        cookies = login_logout_SAP.login_sap()
        email.enviar(
            destinatarios="ti01@inconelinox.com.br",
            assunto=assunto + " - Login SAP",
            corpo_html="<p>Login Realizado pela automação no SAP</p>",
        )

        # Consulta os preços atuais no SAP em uma única varredura para as tabelas alvo
        tabelas_alvo = set(lista_preco_id)
        itens_sap = lista_atual_sap(cookies, tabelas_alvo)
        df_lista = pd.DataFrame(itens_sap)

        # Comparação: merge por ItemCode e PriceList, filtrando os que possuem preços diferentes
        if not df_lista.empty:
            df_merge = pd.merge(df_payload, df_lista, on=["ItemCode", "PriceList"], how="inner")
            df_filtrado = df_merge[df_merge["Price"] != df_merge["PriceSAP"]]
            itens_atualizar = df_filtrado.to_dict("records")
        else:
            itens_atualizar = itens_payload

        total_validos = len(itens_atualizar)
        print(f"Total de itens que realmente precisam ser atualizados: {total_validos}")

        total = len(itens_atualizar)
        tempo_inicio = time.time()
        atualizados = 0

        for item in itens_atualizar:
            atualizar_tabela_sap(
                cookies, item["ItemCode"], item["Price"], item["PriceList"]
            )

            atualizados += 1

            if atualizados % 50 == 0 or atualizados == total:
                tempo_decorrido = time.time() - tempo_inicio
                tempo_medio = tempo_decorrido / atualizados
                itens_restantes = total - atualizados
                eta_segundos = itens_restantes * tempo_medio

                eta_formatado = str(timedelta(seconds=int(eta_segundos)))
                print(
                    f"[{atualizados}/{total}] Atualizados... ETA Restante: {eta_formatado}"
                )

        print(f"\nConcluído! {atualizados} itens foram atualizados com sucesso.")

    except Exception as e:
        msg = f"Erro ao atualizar preços no SAP: {e}"
        print(msg)
        email.enviar(
            destinatarios="ti01@inconelinox.com.br",
            assunto=assunto + " - Erro na Atualização",
            corpo_html=f"<p>Ocorreu um erro ao atualizar os preços no SAP: {e}</p>",
        )
    finally:
        if cookies:
            login_logout_SAP.logout_sap(cookies)
            email.enviar(
                destinatarios="ti01@inconelinox.com.br",
                assunto=assunto + " - Logout SAP",
                corpo_html="<p>Logout Realizado no SAP</p>",
            )
