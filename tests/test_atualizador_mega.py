import pytest
from src.atualizador_mega import (
    converter_data, validar_dezena,
    validar_registro,
)


def test_converter_data():
    assert converter_data("15/07/2024") == "15/07/2024"
    assert converter_data("2024-07-15") == "15/07/2024"
    assert converter_data("") == ""


def test_validar_dezena():
    assert validar_dezena(30) == 30
    assert validar_dezena("60") == 60
    with pytest.raises(ValueError):
        validar_dezena(61)


def test_validar_registro_minimo():
    reg = {
        "concurso": 200,
        "data": "01/01/2024",
        **{f"bola{i}": i * 8 for i in range(1, 7)},
    }
    resultado = validar_registro(reg)
    assert resultado["concurso"] == 200
