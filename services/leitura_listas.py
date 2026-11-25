import csv
import logging
from pathlib import Path
from typing import Any


class LeitorListas:
    def __init__(
        self,
        diretorio_listas: Path = Path("Listas"),
        logger: logging.Logger | None = None,
    ) -> None:
        self.diretorio_listas = diretorio_listas
        self.logger = logger

    @staticmethod
    def limpar_preco(valor_str: str) -> float | None:
        """Converte 'R$ 28,87' para float (28.87).

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

    def listar_arquivos(self) -> list[Path]:
        return sorted(self.diretorio_listas.glob("*.txt"))

    def ler_pendentes(
        self, arquivos: list[Path], listas_concluidas: set[str]
    ) -> tuple[dict[Path, list[dict[str, Any]]], list[dict[str, str]], list[str]]:
        itens_por_arquivo: dict[Path, list[dict[str, Any]]] = {}
        itens_invalidos: list[dict[str, str]] = []
        lista_preco_id: list[str] = []

        for arquivo in arquivos:
            if arquivo.name in listas_concluidas:
                if self.logger is not None:
                    self.logger.info(
                        f"Arquivo já concluído no checkpoint, ignorando: {arquivo.name}"
                    )
                continue

            itens_arquivo: list[dict[str, Any]] = []
            with open(arquivo, mode="r", encoding="utf-16") as f:
                leitor = csv.DictReader(f, delimiter="\t")
                for linha in leitor:
                    item_code = (linha.get("Nº do item") or "").strip()
                    preco_bruto = (
                        linha.get("Nº do item, Preço unitário")
                        or linha.get("Preço unitário")
                        or ""
                    ).strip()
                    table = (linha.get("Nº da lista de preços") or "").strip()

                    preco_unitario = self.limpar_preco(preco_bruto)
                    if preco_unitario is None:
                        itens_invalidos.append(
                            {
                                "ItemCode": item_code,
                                "PrecoOriginal": preco_bruto,
                            }
                        )
                        continue

                    itens_arquivo.append(
                        {
                            "PriceList": table,
                            "ItemCode": item_code,
                            "Price": preco_unitario,
                        }
                    )
                    lista_preco_id.append(table)

            if itens_arquivo:
                itens_por_arquivo[arquivo] = itens_arquivo

        return (
            itens_por_arquivo,
            itens_invalidos,
            sorted(set(lista_preco_id)),
        )
