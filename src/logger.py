"""Logging estruturado com rotação de arquivo."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.config import LOG_NIVEL, LOG_ARQUIVO


def configurar_logger(nome: str = "loterias") -> logging.Logger:
    """Cria e configura o logger principal do projeto."""
    logger = logging.getLogger(nome)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, LOG_NIVEL, logging.INFO))
    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-7s %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # Arquivo com rotação (5 MB × 3 backups)
    log_path = Path(LOG_ARQUIVO)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    arquivo = RotatingFileHandler(
        log_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    arquivo.setFormatter(fmt)
    logger.addHandler(arquivo)

    return logger


log = configurar_logger()
