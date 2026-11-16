import os
import tempfile
import pytest
from src.atualizador import (
    converter_data, validar_dezena,
    validar_registro, gravar_historico, ler_historico,
    validar_historico, COLUNAS,
)


def test_converter_data():
    assert converter_data("15/07/2024") == "15/07/2024"
    assert converter_data("2024-07-15") == "15/07/2024"
    assert converter_data("") == ""


def test_validar_dezena():
    assert validar_dezena(15) == 15
    assert validar_dezena("25") == 25
    with pytest.raises(ValueError):
        validar_dezena(26)


def test_validar_registro_minimo():
    reg = {
        "concurso": 100,
        "data": "01/01/2024",
        **{f"bola{i}": i + 1 for i in range(1, 16)},
    }
    resultado = validar_registro(reg)
    assert resultado["concurso"] == 100


def test_gravar_e_ler_historico():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.csv")
        historico = [
            {
                "concurso": i,
                "data": f"{i:02d}/01/2024",
                **{f"bola{j}": j + i for j in range(1, 16)},
            }
            for i in range(1, 4)
        ]
        gravar_historico(historico, path)
        lido = ler_historico(path)
        assert len(lido) == 3
        assert lido[0]["concurso"] == 1
        assert lido[-1]["concurso"] == 3


def test_gravacao_invalida_preserva_csv():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.csv")
        historico_ok = [
            {
                "concurso": 1,
                "data": "01/01/2024",
                **{f"bola{j}": j for j in range(1, 16)},
            }
        ]
        gravar_historico(historico_ok, path)
        with pytest.raises(ValueError):
            gravar_historico([{"concurso": -1}], path)
        lido = ler_historico(path)
        assert len(lido) == 1


def test_validar_historico_duplicados():
    reg = {
        "concurso": 1,
        "data": "01/01/2024",
        **{f"bola{j}": j for j in range(1, 16)},
    }
    with pytest.raises(ValueError, match="duplicados"):
        validar_historico([reg, reg])


def test_validar_historico_lacuna():
    r1 = {
        "concurso": 1, "data": "01/01/2024",
        **{f"bola{j}": j for j in range(1, 16)},
    }
    r3 = {
        "concurso": 3, "data": "03/01/2024",
        **{f"bola{j}": j for j in range(1, 16)},
    }
    with pytest.raises(ValueError, match="Lacuna"):
        validar_historico([r1, r3])
