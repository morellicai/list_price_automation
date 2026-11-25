import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


class GerenciadorCheckpoint:
    def __init__(
        self,
        diretorio_checkpoints: Path = Path("checkpoints"),
        logger: logging.Logger | None = None,
    ) -> None:
        self.diretorio = diretorio_checkpoints
        self.diretorio_historico = self.diretorio / "historico"
        self.logger = logger

    def _log(self, nivel: str, mensagem: str) -> None:
        if self.logger is not None:
            getattr(self.logger, nivel)(mensagem)

    def caminho_ciclo(self, data_ciclo: str) -> Path:
        return self.diretorio / f"checkpoint_{data_ciclo}.json"

    def carregar(self, data_ciclo: str) -> dict[str, Any]:
        self.diretorio.mkdir(parents=True, exist_ok=True)
        self.diretorio_historico.mkdir(parents=True, exist_ok=True)
        caminho = self.caminho_ciclo(data_ciclo)

        if caminho.exists():
            try:
                with open(caminho, mode="r", encoding="utf-8") as f:
                    dados = json.load(f)
                if isinstance(dados, dict) and "listas_concluidas" in dados:
                    return dados
            except (OSError, json.JSONDecodeError) as exc:
                self._log(
                    "warning",
                    f"Checkpoint corrompido ({exc}). Iniciando estado limpo.",
                )

        return {"data_ciclo": data_ciclo, "listas_concluidas": []}

    def salvar(self, data_ciclo: str, estado: dict[str, Any]) -> None:
        # Escrita atômica via arquivo temporário + fsync evita corrupção.
        caminho = self.caminho_ciclo(data_ciclo)
        caminho_tmp = caminho.with_suffix(".tmp")
        with open(caminho_tmp, mode="w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(caminho_tmp, caminho)

    def arquivar(self, data_ciclo: str) -> None:
        caminho = self.caminho_ciclo(data_ciclo)
        if not caminho.exists():
            return
        sufixo = datetime.now().strftime("%H%M%S")
        destino = self.diretorio_historico / f"checkpoint_{data_ciclo}_{sufixo}.json"
        shutil.move(str(caminho), str(destino))
        self._log("info", f"Checkpoint arquivado em: {destino}")
