import csv
from pathlib import Path

import urllib3

urllib3.disable_warnings()

import os

import requests
import urllib3

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
            json={"ItemPrices": [{"PriceList": table, "Price": price}]},
            cookies=cookies,
            verify=False,
            timeout=10,
        )
    except requests.exceptions.RequestException as e:
        print(f"Erro ao atualizar {cod_item} no SAP: {e}")

    print(
        f"{cod_item} na tabela {table} atualizado no SAP B1 com sucesso! Valor atualizado: {price}"
    )


# Lista para armazenar os itens processados para o payload
itens_payload = []
itens_invalidos = []

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

if itens_payload:
    print(f"Total de itens válidos para atualização: {len(itens_payload)}")
    login_logout_SAP = LoginLogoutSap()
    email = NotificadorEmail()
    # Aqui você pode chamar a função para enviar os dados para o SAP B1
    try:
        cookies = login_logout_SAP.login_sap()
        email.enviar(
            destinatarios="ti01@inconelinox.com.br",
            assunto=assunto + " - Login SAP",
            corpo_html="<p>Login Realizado pela automação no SAP</p>",
        )
        for item in itens_payload:
            atualizar_tabela_sap(
                cookies, item["ItemCode"], item["Price"], item["PriceList"]
            )
    except Exception as e:
        msg = f"Erro ao atualizar preços no SAP: {e}"
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
