"""Testes do logging estruturado."""

import logging
from src.logger import configurar_logger, log


class TestLogger:
    def test_logger_existe(self):
        assert log is not None
        assert isinstance(log, logging.Logger)

    def test_logger_nome(self):
        assert log.name == "loterias"

    def test_logger_tem_handlers(self):
        assert len(log.handlers) >= 1

    def test_configurar_retorna_mesmo_logger(self):
        log2 = configurar_logger()
        assert log2 is log

    def test_nivel_info(self):
        assert log.level == logging.INFO
