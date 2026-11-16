"""Testes dos schemas Pydantic."""

import pytest
from pydantic import ValidationError
from src.schemas import (
    ConcursoQuina,
    ConcursoLotofacil,
    SCHEMAS,
    validar_registro,
)
from src.config import QUINA, LOTOFACIL


class TestConcursoQuina:
    def test_valido(self):
        c = ConcursoQuina(
            concurso=6500, data="15/06/2025",
            bola1=7, bola2=23, bola3=41, bola4=58, bola5=72,
        )
        assert c.concurso == 6500
        assert c.bola1 == 7

    def test_concurso_zero_invalido(self):
        with pytest.raises(ValidationError):
            ConcursoQuina(
                concurso=0, data="15/06/2025",
                bola1=1, bola2=2, bola3=3, bola4=4, bola5=5,
            )

    def test_bola_acima_maximo(self):
        with pytest.raises(ValidationError):
            ConcursoQuina(
                concurso=1, data="15/06/2025",
                bola1=1, bola2=2, bola3=3, bola4=4, bola5=81,
            )


class TestSchemas:
    def test_todas_loterias_tem_schema(self):
        assert "lotofacil" in SCHEMAS
        assert "diadesorte" in SCHEMAS
        assert "megasena" in SCHEMAS
        assert "quina" in SCHEMAS

    def test_validar_registro_quina(self):
        dados = {
            "concurso": 100, "data": "01/01/2025",
            "bola1": 1, "bola2": 10, "bola3": 20,
            "bola4": 40, "bola5": 80,
        }
        resultado = validar_registro(QUINA, dados)
        assert resultado["concurso"] == 100
