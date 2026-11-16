import pytest
import pandas as pd
from src.importador import validar_resultados, importar_resultados


def _df_ok():
    return pd.DataFrame({
        "concurso": [1, 2],
        "data": ["01/01/2024", "03/01/2024"],
        **{f"bola{i}": [i, i + 1] for i in range(1, 16)},
    })


def test_validar_ok():
    df = validar_resultados(_df_ok())
    assert len(df) == 2


def test_validar_resultados_rejeita_dataframe_vazio():
    with pytest.raises(ValueError, match="vazio"):
        validar_resultados(pd.DataFrame())


def test_validar_resultados_rejeita_tipo_invalido():
    with pytest.raises(TypeError):
        validar_resultados("não é df")


def test_validar_resultados_rejeita_colunas_ausentes():
    df = pd.DataFrame({"concurso": [1]})
    with pytest.raises(ValueError, match="ausentes"):
        validar_resultados(df)


def test_validar_resultados_rejeita_dezena_fora_do_intervalo():
    df = _df_ok()
    df.loc[0, "bola1"] = 99
    with pytest.raises(ValueError, match="fora de 1"):
        validar_resultados(df)


def test_importar_resultados_csv_vazio(tmp_path):
    p = tmp_path / "vazio.csv"
    p.write_text("concurso,bola1,bola2,bola3,bola4,bola5,bola6,bola7,bola8,bola9,bola10,bola11,bola12,bola13,bola14,bola15\n")
    with pytest.raises(ValueError, match="vazio"):
        importar_resultados(str(p))


def test_importar_arquivo_inexistente():
    with pytest.raises(FileNotFoundError):
        importar_resultados("/tmp/inexistente_xyz.csv")
