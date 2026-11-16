import pytest
from src.atualizador_dia import (
    converter_data, converter_mes, validar_dezena,
    validar_registro, MESES_MAP,
)


def test_converter_data():
    assert converter_data("15/07/2024") == "15/07/2024"
    assert converter_data("2024-07-15") == "15/07/2024"
    assert converter_data("") == ""


def test_converter_mes():
    assert converter_mes("JANEIRO") == 1
    assert converter_mes("dezembro") == 12
    assert converter_mes(6) == 6
    with pytest.raises(ValueError):
        converter_mes("INVALIDO")


def test_validar_dezena():
    assert validar_dezena(15) == 15
    assert validar_dezena("31") == 31
    with pytest.raises(ValueError):
        validar_dezena(32)


def test_validar_registro_minimo():
    reg = {
        "concurso": 100,
        "data": "01/01/2024",
        "mes": "JANEIRO",
        **{f"bola{i}": i * 4 for i in range(1, 8)},
    }
    resultado = validar_registro(reg)
    assert resultado["concurso"] == 100
    assert resultado["mes"] == 1
