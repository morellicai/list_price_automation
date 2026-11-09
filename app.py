import csv
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import urllib3

urllib3.disable_warnings()


from services.body_email_gen import (
    gerar_html_conclusao,
    gerar_html_inicio,
    gerar_html_interrupcao,
)

# pyrefly: ignore [missing-import]
from services.email_service import NotificadorEmail
from services.lista_itens import ItensSap
from services.login_logout_sap import LoginLogoutSap

arquivos_txt = list(Path("src").glob("*.txt"))
assunto = "Automação: Atualização da Lista de Preços"
SAP_URL = os.getenv("SAP_URL")
hour = datetime.now().hour


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


# ── Execução Principal ────────────────────────────────────────────────────────

itens_payload = []
itens_invalidos = []
lista_preco_id = []


lista_itens_atualizados = {
    "PriceList": set(),
    "Items": [],
}

if arquivos_txt:
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

lista_tabelas = sorted(set(lista_preco_id))

if itens_payload and hour >= 18:
    login_logout_SAP = LoginLogoutSap()
    email = NotificadorEmail()
    df_payload = pd.DataFrame(itens_payload)
    print("Iniciando processo de login no SAP...")

    interrompido_horario = False
    total = 0
    tempo_total = "0:00:00"

    try:
        cookies = login_logout_SAP.login_sap()

        lista_itens_sap = ItensSap(cookies, SAP_URL)

        tabelas_alvo = set(lista_tabelas)
        itens_sap = lista_itens_sap.lista_atual_sap(cookies, tabelas_alvo)
        df_lista = pd.DataFrame(itens_sap)

        if not df_lista.empty:
            df_merge = pd.merge(
                df_payload, df_lista, on=["ItemCode", "PriceList"], how="inner"
            )
            df_filtrado = df_merge[df_merge["Price"] != df_merge["PriceSAP"]]
            itens_atualizar = df_filtrado.to_dict("records")
        else:
            itens_atualizar = itens_payload

        total_validos = len(itens_atualizar)
        total = total_validos
        print(f"Total de itens que realmente precisam ser atualizados: {total_validos}")

        # Estimativa prévia de duração (~0.3s por item no SAP B1 Service Layer)
        tempo_estimado_seg = int(total * 0.3)
        tempo_esperado_str = (
            str(timedelta(seconds=tempo_estimado_seg))
            if total > 0
            else "0s (itens já atualizados)"
        )

        corpo_inicio = gerar_html_inicio(
            tabelas=lista_tabelas,
            total_itens=len(itens_payload),
            total_real_atualizar=total,
            tempo_esperado=tempo_esperado_str,
        )
        email.enviar(
            destinatarios=[
                "ti01@inconelinox.com.br",
                # "armando.abdalla@inconelinox.com.br",
            ],
            assunto=assunto + " - Inicio do Processo",
            corpo_html=corpo_inicio,
        )

        tempo_inicio = time.time()
        atualizados = 0

        # 4. Atualização em lote
        for item in itens_atualizar:
            # Verifica se atingiu o início do horário comercial (08:00)
            hora_atual = datetime.now().hour
            if 8 <= hora_atual < 18:
                print(
                    f"\n[HORÁRIO LIMITE] Atingido {hora_atual}h (horário comercial). "
                    "Pausando a execução para não impactar a operação."
                )
                interrompido_horario = True
                break

            lista_itens_sap.atualizar_tabela_sap(
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

        if interrompido_horario:
            itens_restantes = total - atualizados
            tempo_medio = (
                (time.time() - tempo_inicio) / atualizados if atualizados > 0 else 0.3
            )
            eta_restante_str = str(
                timedelta(seconds=int(itens_restantes * tempo_medio))
            )

            # Identifica quais tabelas foram 100% concluídas
            itens_pendentes = itens_atualizar[atualizados:]
            tabelas_pendentes = {str(i["PriceList"]) for i in itens_pendentes}
            listas_completas = [
                tab for tab in lista_tabelas if str(tab) not in tabelas_pendentes
            ]

            print(
                f"\nAutomação pausada pelo horário comercial às {datetime.now().strftime('%H:%M:%S')}."
            )
            print(f"Atualizados: {atualizados}/{total} itens.")
            print(f"Listas concluídas: {len(listas_completas)}/{len(lista_tabelas)}.")
            print(f"Tempo estimado restante: {eta_restante_str}.")

            corpo_interrupcao = gerar_html_interrupcao(
                tabelas_afetadas=sorted(lista_itens_atualizados["PriceList"]),
                total_atualizados=atualizados,
                motivo="Pausa programada: início do horário comercial (08:00). A automação continuará na próxima janela noturna.",
                listas_completas=listas_completas,
                tempo_esperado_restante=eta_restante_str,
            )
            email.enviar(
                destinatarios=[
                    "ti01@inconelinox.com.br",
                    # "armando.abdalla@inconelinox.com.br",
                ],
                assunto=assunto + " - Pausa: Início do Horário Comercial (08:00)",
                corpo_html=corpo_interrupcao,
            )
        else:
            print(
                f"\nConcluído! {atualizados} itens foram atualizados com sucesso em {tempo_total}."
            )

    except (Exception, KeyboardInterrupt) as e:
        motivo = (
            "Interrupção manual pelo operador (Ctrl+C)"
            if isinstance(e, KeyboardInterrupt)
            else str(e)
        )
        print(f"\nFalha / Interrupção na execução: {motivo}")

        # 6. E-mail de Interrupção / Falha
        corpo_interrupcao = gerar_html_interrupcao(
            tabelas_afetadas=sorted(lista_itens_atualizados["PriceList"]),
            total_atualizados=len(lista_itens_atualizados["Items"]),
            motivo=motivo,
        )
        email.enviar(
            destinatarios=[
                "ti01@inconelinox.com.br",
                # "armando.abdalla@inconelinox.com.br",
            ],
            assunto=assunto + " - Atenção: Automação Interrompida",
            corpo_html=corpo_interrupcao,
        )

    finally:
        if cookies:
            login_logout_SAP.logout_sap(cookies)
            print("Sessão SAP encerrada com sucesso.")

        if (
            not interrompido_horario
            and total > 0
            and len(lista_itens_atualizados["Items"]) == total
        ):
            print(
                "Todos os itens foram atualizados com sucesso. E-mail de conclusão enviado."
            )
            for arquivo in arquivos_txt:
                if os.path.exists(arquivo):
                    os.remove(arquivo)
                    print(f"Arquivo de entrada '{arquivo}' removido com sucesso.")

            corpo_conclusao = gerar_html_conclusao(
                tabelas_processadas=sorted(lista_itens_atualizados["PriceList"]),
                total_atualizados=len(lista_itens_atualizados["Items"]),
                tempo_total=tempo_total,
            )
            email.enviar(
                destinatarios=[
                    "ti01@inconelinox.com.br",
                    # "armando.abdalla@inconelinox.com.br",
                ],
                assunto=assunto + " - Concluído com Sucesso",
                corpo_html=corpo_conclusao,
            )
        elif interrompido_horario:
            print(
                "Execução pausada às 08:00. Arquivos de entrada mantidos para continuidade na próxima execução."
            )
        else:
            print("Nenhum item pendente para atualização.")
else:
    if hour < 18:
        print(
            f"Hora atual: {hour}h. A execução só é permitida a partir das 18h. Nenhum arquivo de entrada processado."
        )
    else:
        print("Nenhum arquivo de entrada encontrado. Nenhum item processado.")
