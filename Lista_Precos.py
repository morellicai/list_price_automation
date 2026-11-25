import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import urllib3
from dotenv import load_dotenv

from services.body_email_gen import (
    gerar_html_conclusao,
    gerar_html_inicio,
    gerar_html_interrupcao,
)
from services.checkpoint_service import GerenciadorCheckpoint

# pyrefly: ignore [missing-import]
from services.email_service import NotificadorEmail
from services.leitura_listas import LeitorListas
from services.limpeza_service import LimpezaArquivos
from services.lista_itens import ItensSap
from services.logger_service import GerenciadorLogger
from services.login_logout_sap import LoginLogoutSap

load_dotenv()

urllib3.disable_warnings()

DIAS_RETENCAO_LOGS = 30
DIAS_RETENCAO_CHECKPOINTS = 30

ASSUNTO = "Automação: Atualização da Lista de Preços"
SAP_URL = os.getenv("SAP_URL")
DESTINATARIOS = [
    "ti01@inconelinox.com.br",
    "ti@inconelinox.com.br",
    # "jgnann@inconelinox.com.br",
    # "armando.abdalla@inconelinox.com.br",
]
DESTINATARIOS_ALERTA = [
    "ti01@inconelinox.com.br",
    # "jgnann@gmail.com",
    # "ti@inconelinox.com.br",
]


def executar_carga() -> None:
    agora_inicio = datetime.now()
    data_ciclo = agora_inicio.strftime("%Y-%m-%d")

    logger = GerenciadorLogger().configurar(data_ciclo)
    logger.info("=== Iniciando execução da automação de Lista de Preços ===")

    limpeza = LimpezaArquivos(logger=logger)
    limpeza.limpar_antigos(Path("logs"), "execucao_*.log*", DIAS_RETENCAO_LOGS)
    limpeza.limpar_antigos(
        Path("checkpoints"), "checkpoint_*.json", DIAS_RETENCAO_CHECKPOINTS
    )
    limpeza.limpar_antigos(
        Path("checkpoints/historico"),
        "checkpoint_*.json",
        DIAS_RETENCAO_CHECKPOINTS,
    )

    checkpoint = GerenciadorCheckpoint(logger=logger)
    estado_ckpt = checkpoint.carregar(data_ciclo)
    concluidas_set = set(estado_ckpt.get("listas_concluidas", []))

    leitor = LeitorListas(logger=logger)
    arquivos_txt = leitor.listar_arquivos()
    itens_por_arquivo, itens_invalidos, lista_tabelas = leitor.ler_pendentes(
        arquivos_txt, concluidas_set
    )
    if itens_invalidos:
        logger.warning(f"Itens inválidos ignorados na leitura: {len(itens_invalidos)}")

    todos_itens_lidos = [item for itens in itens_por_arquivo.values() for item in itens]
    email = NotificadorEmail()
    hour = agora_inicio.hour
    eh_fim_de_semana = agora_inicio.weekday() >= 5

    if not todos_itens_lidos:
        logger.info("Nenhum arquivo/item pendente para processamento.")
        if arquivos_txt and len(concluidas_set) >= len(arquivos_txt):
            checkpoint.arquivar(data_ciclo)
        return

    if not (hour >= 18 or eh_fim_de_semana) and os.getenv("SAP_DB") == "SBOINCONEL_PRD":
        logger.warning(
            f"Hora atual: {hour}h. Execução permitida apenas a partir das "
            "18h em dias úteis."
        )
        corpo_interrupcao = gerar_html_interrupcao(
            tabelas_afetadas=[],
            total_atualizados=0,
            motivo=(
                "Execução fora do horário permitido (18h às 08h) ou "
                "Lista de Preços vazia. Nenhum item processado."
            ),
        )
        email.enviar(
            destinatarios=DESTINATARIOS_ALERTA,
            assunto=f"{ASSUNTO} - Atenção: Execução Fora do Horário",
            corpo_html=corpo_interrupcao,
        )
        return

    login_logout_sap = LoginLogoutSap()
    cookies: Any = None
    interrompido_horario = False
    tempo_total = "0:00:00"
    total = 0
    lista_itens_atualizados: dict[str, Any] = {
        "PriceList": set(),
        "Items": [],
    }

    try:
        logger.info("Autenticando na Service Layer do SAP B1...")
        cookies = login_logout_sap.login_sap()
        lista_itens_sap = ItensSap(
            cookies,
            SAP_URL,
            auth_service=login_logout_sap,
            logger=logger,
        )

        itens_sap = lista_itens_sap.lista_atual_sap(cookies, set(lista_tabelas))
        df_lista = pd.DataFrame(itens_sap)

        itens_atualizar_por_arquivo: dict[Path, list[dict[str, Any]]] = {}
        for arquivo, itens_arq in itens_por_arquivo.items():
            if not df_lista.empty:
                df_arq = pd.DataFrame(itens_arq)
                df_merge = pd.merge(
                    df_arq,
                    df_lista,
                    on=["ItemCode", "PriceList"],
                    how="inner",
                )
                df_filt = df_merge[df_merge["Price"] != df_merge["PriceSAP"]]
                delta_arq = df_filt.to_dict("records")
            else:
                delta_arq = itens_arq
            itens_atualizar_por_arquivo[arquivo] = delta_arq

        todos_delta = [
            item for itens in itens_atualizar_por_arquivo.values() for item in itens
        ]
        total = len(todos_delta)
        logger.info(f"Total de itens com divergência (delta real): {total}")

        tempo_est_seg = int(total * 0.3)
        tempo_esp_str = (
            str(timedelta(seconds=tempo_est_seg))
            if total > 0
            else "0s (itens já atualizados)"
        )
        janela_desc = (
            "Sem limite (Final de semana - execução contínua)"
            if datetime.now().weekday() >= 5
            else "Até 08:00 (Início do expediente comercial)"
        )

        corpo_inicio = gerar_html_inicio(
            tabelas=lista_tabelas,
            total_itens=len(todos_itens_lidos),
            total_real_atualizar=total,
            tempo_esperado=tempo_esp_str,
            janela_limite=janela_desc,
        )
        email.enviar(
            destinatarios=DESTINATARIOS,
            assunto=f"{ASSUNTO} - Inicio do Processo",
            corpo_html=corpo_inicio,
        )

        tempo_inicio = time.time()
        atualizados = 0

        for arquivo, itens_delta in itens_atualizar_por_arquivo.items():
            logger.info(
                f"Iniciando arquivo {arquivo.name} "
                f"({len(itens_delta)} itens a atualizar)"
            )
            falha_no_arquivo = False

            for item in itens_delta:
                agora = datetime.now()
                eh_dia_util = agora.weekday() < 5
                if (
                    eh_dia_util
                    and 8 <= agora.hour < 18
                    and os.getenv("SAP_DB") == "SBOINCONEL_PRD"
                ):
                    logger.warning(
                        f"Horário comercial atingido ({agora.hour}h). "
                        "Pausando execução para não impactar a operação."
                    )
                    interrompido_horario = True
                    break

                sucesso_item = lista_itens_sap.atualizar_tabela_sap(
                    lista_itens_sap.cookies,
                    item["ItemCode"],
                    item["Price"],
                    item["PriceList"],
                )
                if not sucesso_item:
                    falha_no_arquivo = True
                    continue

                lista_itens_atualizados["Items"].append(item["ItemCode"])
                lista_itens_atualizados["PriceList"].add(str(item["PriceList"]))
                atualizados += 1

                if atualizados % 50 == 0 or atualizados == total:
                    decorrido = time.time() - tempo_inicio
                    medio = decorrido / atualizados
                    restantes = total - atualizados
                    eta_str = str(timedelta(seconds=int(restantes * medio)))
                    logger.info(
                        f"Progresso: [{atualizados}/{total}] atualizados | "
                        f"ETA restante: {eta_str}"
                    )

            if interrompido_horario:
                break

            if not falha_no_arquivo:
                estado_ckpt["listas_concluidas"].append(arquivo.name)
                checkpoint.salvar(data_ciclo, estado_ckpt)
                logger.info(f"Arquivo concluído e salvo no checkpoint: {arquivo.name}")
                limpeza.remover_arquivo_lista(arquivo)

        tempo_total = str(timedelta(seconds=int(time.time() - tempo_inicio)))

        if interrompido_horario:
            restantes = total - atualizados
            decorrido = time.time() - tempo_inicio
            medio = decorrido / atualizados if atualizados > 0 else 0.3
            eta_rest_str = str(timedelta(seconds=int(restantes * medio)))

            itens_pendentes = todos_delta[atualizados:]
            tabs_pend = {str(i["PriceList"]) for i in itens_pendentes}
            listas_comp = [t for t in lista_tabelas if str(t) not in tabs_pend]

            logger.warning(
                f"Automação pausada às {datetime.now():%H:%M:%S}. "
                f"Atualizados: {atualizados}/{total}. "
                f"ETA restante: {eta_rest_str}"
            )
            corpo_interrupcao = gerar_html_interrupcao(
                tabelas_afetadas=sorted(lista_itens_atualizados["PriceList"]),
                total_atualizados=atualizados,
                motivo=(
                    "Pausa programada: início do horário comercial (08:00). "
                    "A automação continuará na próxima janela noturna."
                ),
                listas_completas=listas_comp,
                tempo_esperado_restante=eta_rest_str,
            )
            email.enviar(
                destinatarios=DESTINATARIOS,
                assunto=(f"{ASSUNTO} - Pausa: Início do Horário Comercial (08:00)"),
                corpo_html=corpo_interrupcao,
            )
        else:
            logger.info(
                f"Ciclo concluído! {atualizados} itens atualizados em {tempo_total}."
            )
            checkpoint.arquivar(data_ciclo)
            corpo_conclusao = gerar_html_conclusao(
                tabelas_processadas=sorted(lista_itens_atualizados["PriceList"]),
                total_atualizados=len(lista_itens_atualizados["Items"]),
                tempo_total=tempo_total,
            )
            email.enviar(
                destinatarios=DESTINATARIOS,
                assunto=f"{ASSUNTO} - Concluído com Sucesso",
                corpo_html=corpo_conclusao,
            )

    except BaseException as exc:
        motivo = (
            "Interrupção manual pelo operador (Ctrl+C)"
            if isinstance(exc, KeyboardInterrupt)
            else str(exc)
        )
        logger.critical(
            f"Exceção crítica capturada na execução: {motivo}",
            exc_info=True,
        )
        corpo_interrupcao = gerar_html_interrupcao(
            tabelas_afetadas=sorted(lista_itens_atualizados["PriceList"]),
            total_atualizados=len(lista_itens_atualizados["Items"]),
            motivo=motivo,
        )
        email.enviar(
            destinatarios=DESTINATARIOS_ALERTA,
            assunto=f"{ASSUNTO} - Atenção: Automação Interrompida",
            corpo_html=corpo_interrupcao,
        )
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise

    finally:
        if cookies is not None:
            login_logout_sap.logout_sap(
                lista_itens_sap.cookies if "lista_itens_sap" in locals() else cookies
            )
            logger.info("Sessão SAP encerrada com sucesso.")


if __name__ == "__main__":
    executar_carga()
