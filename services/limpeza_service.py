import logging
import time
from pathlib import Path


class LimpezaArquivos:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger

    def _log(self, nivel: str, mensagem: str) -> None:
        if self.logger is not None:
            getattr(self.logger, nivel)(mensagem)

    def limpar_antigos(self, diretorio: Path, padrao: str, dias_retencao: int) -> None:
        if not diretorio.exists():
            return

        limite = time.time() - (dias_retencao * 86400)
        for arquivo in diretorio.glob(padrao):
            if arquivo.is_file() and arquivo.stat().st_mtime < limite:
                try:
                    arquivo.unlink()
                    self._log("info", f"Arquivo antigo removido: {arquivo}")
                except OSError as exc:
                    self._log("warning", f"Falha ao remover {arquivo}: {exc}")

    def remover_arquivo_lista(self, caminho: Path) -> None:
        if not caminho.exists():
            return
        try:
            caminho.unlink()
            self._log("info", f"Arquivo removido após conclusão: {caminho}")
        except OSError as exc:
            self._log("warning", f"Falha ao remover {caminho}: {exc}")
