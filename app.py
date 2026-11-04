import csv
from pathlib import Path

import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings()

import os

import requests
import urllib3

# pyrefly: ignore [missing-import]
from services.email_service import NotificadorEmail
from services.login_logout_sap import LoginLogoutSap

tab18 = Path("./src/TAB18.txt")
assunto = "Automação: Atualização da Lista de Preços"
SAP_URL = os.getenv("SAP_URL")
load_dotenv()


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
    resp = requests.post(
        f"{SAP_URL}/Items('{cod_item}')",
        json={"ItemPrices": [{"PriceList": table, "Price": price}]},
        cookies=cookies,
        verify=False,
        timeout=15,
    )
    if resp.status_code not in [200, 204]:
        raise Exception(f"Erro ao atualizar {cod_item} no SAP: {resp.text}")

    print(f"  {cod_item} atualizado no SAP B1 com sucesso!")


# Lista para armazenar os itens processados para o payload
itens_payload = []
itens_invalidos = []

with open(tab18, mode="r", encoding="utf-16") as f:
    # O DictReader utiliza a 1ª linha como chave de cada coluna
    leitor = csv.DictReader(f, delimiter="\t")

    for linha in leitor:
        item_code = linha.get("Nº do item", "").strip()
        preco_bruto = linha.get("Preço unitário", "").strip()
        table = linha.get("Nº da lista de preços", "").strip()

        if not item_code:
            continue

        preco_unitario = limpar_preco(preco_bruto)

        # Se o preço vier como '#N/D' ou '#VALOR!', você pode ignorar ou tratar
        if preco_unitario is None:
            itens_invalidos.append(
                {"ItemCode": item_code, "PrecoOriginal": preco_bruto}
            )
            continue

        # Estrutura pronta para o payload da API
        item_data = {
            "PriceList": table,
            "ItemCode": item_code,
            "Price": preco_unitario,  # ou preco_bruto se preferir manter 'R$ 28,87'
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
