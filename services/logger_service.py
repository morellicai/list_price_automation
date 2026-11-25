import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


class FlushRotatingFileHandler(RotatingFileHandler):
    """Força flush imediato em disco para evitar perda de logs em quedas."""

    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self.flush()


class GerenciadorLogger:
    def __init__(
        self,
        diretorio_logs: Path = Path("logs"),
        nome_logger: str = "carga_price_list",
    ) -> None:
        self.diretorio_logs = diretorio_logs
        self.nome_logger = nome_logger

    def configurar(self, data_ciclo: str) -> logging.Logger:
        self.diretorio_logs.mkdir(parents=True, exist_ok=True)
        caminho_log = self.diretorio_logs / f"execucao_{data_ciclo}.log"

        logger = logging.getLogger(self.nome_logger)
        logger.setLevel(logging.INFO)
        logger.handlers.clear()

        formato = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler = FlushRotatingFileHandler(
            caminho_log,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formato)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formato)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        return logger
