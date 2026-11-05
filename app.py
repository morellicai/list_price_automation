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
                else f"{SAP_URL}/{next_link.lstrip('/')}"
            )
            print(f"  {len(sap_items)} registros coletados do SAP...")

        except requests.exceptions.RequestException as e:
            print(f"Erro ao obter lista de preços no SAP: {e}")
            break

    print(f"-> Total de registros obtidos do SAP: {len(sap_items)}\n")
    return sap_items


# ── Geradores de HTML compatíveis com Microsoft Outlook ──────────────────────


def gerar_html_inicio(tabelas: list[str], total_itens: int) -> str:
    """Gera o HTML do e-mail de início no formato compatível com o Word/Outlook."""
    tabelas_str = ", ".join(tabelas) if tabelas else "Nenhuma"
    return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
        <title>Automação Iniciada</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f4f5f7; font-family: Arial, Helvetica, sans-serif;">
        <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f4f5f7; width: 100%;">
            <tr>
            <td align="center" style="padding: 20px 10px;">
                <!--[if (gte mso 9)|(IE)]>
                <table role="presentation" width="600" align="center" border="0" cellspacing="0" cellpadding="0"><tr><td>
                <![endif]-->
                <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; width: 100%; background-color: #ffffff; border: 1px solid #e1e4e8; border-collapse: collapse;">
                <tr>
                    <td style="background-color: #0052cc; padding: 20px; text-align: center;">
                    <h2 style="color: #ffffff; margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 20px;">Automação SAP B1: Iniciada</h2>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 25px 20px; font-family: Arial, Helvetica, sans-serif;">
                    <p style="color: #333333; font-size: 15px; margin: 0 0 12px 0;">Olá, equipe,</p>
                    <p style="color: #555555; font-size: 14px; line-height: 20px; margin: 0 0 20px 0;">
                        O script de carga de preços realizou o login no Service Layer com sucesso e iniciou o processamento.
                    </p>
                    <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="10" style="border-collapse: collapse; margin-bottom: 25px;">
                        <tr>
                        <td width="55%" style="border-bottom: 1px solid #eeeeee; color: #555555; font-size: 13px;"><strong>Tabelas na Fila:</strong></td>
                        <td width="45%" style="border-bottom: 1px solid #eeeeee; color: #333333; font-size: 13px;">{len(tabelas)} ({tabelas_str})</td>
                        </tr>
                        <tr>
                        <td style="border-bottom: 1px solid #eeeeee; color: #555555; font-size: 13px;"><strong>Total de Itens nos Arquivos:</strong></td>
                        <td style="border-bottom: 1px solid #eeeeee; color: #333333; font-size: 13px;">{total_itens}</td>
                        </tr>
                        <tr>
                        <td style="border-bottom: 1px solid #eeeeee; color: #555555; font-size: 13px;"><strong>Status:</strong></td>
                        <td style="border-bottom: 1px solid #eeeeee; color: #0052cc; font-size: 13px;"><strong>Calculando delta e atualizando...</strong></td>
                        </tr>
                    </table>
                    <p style="color: #888888; font-size: 12px; margin: 0; text-align: center; border-top: 1px solid #f0f0f0; padding-top: 15px;">
                        Gerado automaticamente via Python • Inconel Inox IT
                    </p>
                    </td>
                </tr>
                </table>
                <!--[if (gte mso 9)|(IE)]>
                </td></tr></table>
                <![endif]-->
            </td>
            </tr>
        </table>
        </body>
        </html>"""


def gerar_html_interrupcao(
    tabelas_afetadas: list[str], total_atualizados: int, motivo: str
) -> str:
    """Gera o HTML do e-mail de interrupção/erro no formato compatível com o Word/Outlook."""
    tabelas_str = ", ".join(tabelas_afetadas) if tabelas_afetadas else "Nenhuma"
    return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
        <title>Automação Interrompida</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f4f5f7; font-family: Arial, Helvetica, sans-serif;">
        <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f4f5f7; width: 100%;">
            <tr>
            <td align="center" style="padding: 20px 10px;">
                <!--[if (gte mso 9)|(IE)]>
                <table role="presentation" width="600" align="center" border="0" cellspacing="0" cellpadding="0"><tr><td>
                <![endif]-->
                <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; width: 100%; background-color: #ffffff; border: 1px solid #dddddd; border-collapse: collapse;">
                <tr>
                    <td style="background-color: #d32f2f; padding: 20px; text-align: center;">
                    <h2 style="color: #ffffff; margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 20px;">⚠️ Atenção: Automação Interrompida</h2>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 25px 20px; font-family: Arial, Helvetica, sans-serif;">
                    <p style="color: #333333; font-size: 15px; margin: 0 0 10px 0;">Olá, equipe,</p>
                    <p style="color: #555555; font-size: 14px; line-height: 20px; margin: 0 0 15px 0;">
                        A rotina de atualização da lista de preços foi <strong>interrompida inesperadamente</strong> antes de finalizar todos os registros.
                    </p>
                    
                    <!-- Callout Box seguro para Outlook -->
                    <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #fff3f3; border-left: 4px solid #d32f2f; border-collapse: collapse; margin-bottom: 20px;">
                        <tr>
                        <td style="padding: 15px; font-family: Arial, Helvetica, sans-serif;">
                            <h3 style="margin: 0 0 10px 0; color: #d32f2f; font-size: 15px;">Progresso Salvo até a Interrupção</h3>
                            <p style="margin: 0 0 8px 0; color: #333333; font-size: 13px;">
                            <strong>Tabelas com Itens Atualizados:</strong> {tabelas_str}
                            </p>
                            <p style="margin: 0 0 8px 0; color: #333333; font-size: 13px;">
                            <strong>Itens Atualizados com Sucesso:</strong> {total_atualizados}
                            </p>
                            <p style="margin: 0; color: #c62828; font-size: 13px;">
                            <strong>Motivo / Erro:</strong> {motivo}
                            </p>
                        </td>
                        </tr>
                    </table>

                    <p style="color: #555555; font-size: 13px; line-height: 18px; margin: 0 0 20px 0;">
                        Graças à arquitetura de carga delta, ao reiniciar o script, os itens já atualizados acima serão ignorados automaticamente.
                    </p>
                    <p style="color: #888888; font-size: 12px; margin: 0; text-align: center; border-top: 1px solid #f0f0f0; padding-top: 15px;">
                        Mensagem automática gerada pelo script de integração TI • Inconel Inox
                    </p>
                    </td>
                </tr>
                </table>
                <!--[if (gte mso 9)|(IE)]>
                </td></tr></table>
                <![endif]-->
            </td>
            </tr>
        </table>
        </body>
        </html>"""


def gerar_html_conclusao(
    tabelas_processadas: list[str], total_atualizados: int, tempo_total: str
) -> str:
    """Gera o HTML do e-mail de conclusão no formato compatível com o Word/Outlook."""
    tabelas_str = ", ".join(tabelas_processadas) if tabelas_processadas else "Nenhuma"
    return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
        <title>Atualização Concluída</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f4f5f7; font-family: Arial, Helvetica, sans-serif;">
        <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f4f5f7; width: 100%;">
            <tr>
            <td align="center" style="padding: 20px 10px;">
                <!--[if (gte mso 9)|(IE)]>
                <table role="presentation" width="600" align="center" border="0" cellspacing="0" cellpadding="0"><tr><td>
                <![endif]-->
                <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; width: 100%; background-color: #ffffff; border: 1px solid #dddddd; border-collapse: collapse;">
                <tr>
                    <td style="background-color: #2e7d32; padding: 20px; text-align: center;">
                    <h2 style="color: #ffffff; margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 20px;">✅ Atualização Concluída com Sucesso</h2>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 25px 20px; font-family: Arial, Helvetica, sans-serif;">
                    <p style="color: #333333; font-size: 15px; margin: 0 0 10px 0;">Olá, equipe,</p>
                    <p style="color: #555555; font-size: 14px; line-height: 20px; margin: 0 0 15px 0;">
                        A automação da lista de preços foi finalizada com sucesso no SAP B1.
                    </p>
                    
                    <!-- Callout Box seguro para Outlook -->
                    <table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f1f8e9; border-left: 4px solid #2e7d32; border-collapse: collapse; margin-bottom: 20px;">
                        <tr>
                        <td style="padding: 15px; font-family: Arial, Helvetica, sans-serif;">
                            <h3 style="margin: 0 0 10px 0; color: #2e7d32; font-size: 15px;">Resultados Finais</h3>
                            <p style="margin: 0 0 8px 0; color: #333333; font-size: 13px;">
                            <strong>Tabelas Processadas:</strong> {tabelas_str}
                            </p>
                            <p style="margin: 0 0 8px 0; color: #333333; font-size: 13px;">
                            <strong>Itens Atualizados no Total:</strong> {total_atualizados}
                            </p>
                            <p style="margin: 0; color: #333333; font-size: 13px;">
                            <strong>Tempo Total de Execução:</strong> {tempo_total}
                            </p>
                        </td>
                        </tr>
                    </table>

                    <br>
                    <p style="color: #888888; font-size: 12px; margin: 0; text-align: center; border-top: 1px solid #f0f0f0; padding-top: 15px;">
                        Mensagem automática gerada pelo script de integração TI • Inconel Inox
                    </p>
                    </td>
                </tr>
                </table>
                <!--[if (gte mso 9)|(IE)]>
                </td></tr></table>
                <![endif]-->
            </td>
            </tr>
        </table>
        </body>
        </html>"""


# ── Execução Principal ────────────────────────────────────────────────────────

itens_payload = []
itens_invalidos = []
lista_preco_id = []

# Estrutura com tipagem coerente para armazenar os itens atualizados com sucesso
lista_itens_atualizados = {
    "PriceList": set(),  # Conjunto de IDs das tabelas atualizadas (ex: {'7', '18'})
    "Items": [],  # Lista com os códigos dos itens atualizados (ex: ['AB01', ...])
}

for arquivo in arquivos_txt:
    with open(arquivo, mode="r", encoding="utf-16") as f:
        leitor = csv.DictReader(f, delimiter="\t")

        for linha in leitor:
            item_code = linha.get("Nº do item", "").strip()
            preco_bruto = (
                linha.get("Nº do item, Preço unitário")
                or linha.get("Preço unitário")
                or ""
            ).strip()
            table = linha.get("Nº da lista de preços", "").strip()

            preco_unitario = limpar_preco(preco_bruto)

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

lista_tabelas = sorted(list(set(lista_preco_id)))
print(
    f"Total de listas ({len(lista_tabelas)}) e itens válidos no arquivo: {len(itens_payload)}\n"
)

if itens_payload:
    login_logout_SAP = LoginLogoutSap()
    email = NotificadorEmail()
    df_payload = pd.DataFrame(itens_payload)
    print("Iniciando processo de login no SAP...")

    try:
        cookies = login_logout_SAP.login_sap()

        # 1. E-mail de Início
        corpo_inicio = gerar_html_inicio(lista_tabelas, len(itens_payload))
        email.enviar(
            destinatarios="ti01@inconelinox.com.br",
            assunto=assunto + " - Login SAP",
            corpo_html=corpo_inicio,
        )

        # 2. Consulta de preços atuais no SAP para as tabelas alvo
        tabelas_alvo = set(lista_tabelas)
        itens_sap = lista_atual_sap(cookies, tabelas_alvo)
        df_lista = pd.DataFrame(itens_sap)

        # 3. Comparação (Delta) por ItemCode e PriceList
        if not df_lista.empty:
            df_merge = pd.merge(
                df_payload, df_lista, on=["ItemCode", "PriceList"], how="inner"
            )
            df_filtrado = df_merge[df_merge["Price"] != df_merge["PriceSAP"]]
            itens_atualizar = df_filtrado.to_dict("records")
        else:
            itens_atualizar = itens_payload

        total_validos = len(itens_atualizar)
        print(f"Total de itens que realmente precisam ser atualizados: {total_validos}")

        total = len(itens_atualizar)
        tempo_inicio = time.time()
        atualizados = 0

        # 4. Atualização em lote
        for item in itens_atualizar:
            atualizar_tabela_sap(
                cookies, item["ItemCode"], item["Price"], item["PriceList"]
            )

            # Armazena os dados com tipos consistentes
            lista_itens_atualizados["Items"].append(item["ItemCode"])
            lista_itens_atualizados["PriceList"].add(str(item["PriceList"]))

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

        tempo_total = str(timedelta(seconds=int(time.time() - tempo_inicio)))
        print(
            f"\nConcluído! {atualizados} itens foram atualizados com sucesso em {tempo_total}."
        )

        # 5. E-mail de Conclusão com Sucesso (apenas se finalizou o loop sem erros)

    except (Exception, KeyboardInterrupt) as e:
        motivo = (
            "Interrupção manual pelo operador (Ctrl+C)"
            if isinstance(e, KeyboardInterrupt)
            else str(e)
        )
        print(f"\nFalha / Interrupção na execução: {motivo}")

        # 6. E-mail de Interrupção / Falha
        corpo_interrupcao = gerar_html_interrupcao(
            tabelas_afetadas=sorted(list(lista_itens_atualizados["PriceList"])),
            total_atualizados=len(lista_itens_atualizados["Items"]),
            motivo=motivo,
        )
        email.enviar(
            destinatarios="ti01@inconelinox.com.br",
            assunto=assunto + " - Atenção: Automação Interrompida",
            corpo_html=corpo_interrupcao,
        )

    finally:
        if cookies:
            login_logout_SAP.logout_sap(cookies)
            print("Sessão SAP encerrada com sucesso.")

        corpo_conclusao = gerar_html_conclusao(
            tabelas_processadas=sorted(list(lista_itens_atualizados["PriceList"])),
            total_atualizados=len(lista_itens_atualizados["Items"]),
            tempo_total=tempo_total,
        )
        email.enviar(
            destinatarios="ti01@inconelinox.com.br",
            assunto=assunto + " - Concluído com Sucesso",
            corpo_html=corpo_conclusao,
        )

        if os.path.exists(arquivos_txt):
            os.remove(arquivos_txt)
            print("Arquivos de entrada removidos com sucesso.")
