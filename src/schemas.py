"""Schemas Pydantic para validação de dados de loterias."""

from typing import Annotated

from pydantic import BaseModel, Field, create_model, field_validator

from src.config import LOTOFACIL, DIA_DE_SORTE, MEGA_SENA, QUINA, LOTOMANIA, DUPLA_SENA, LoteriaConfig


def _criar_schema_concurso(lot: LoteriaConfig) -> type[BaseModel]:
    """Gera dinamicamente um schema Pydantic para uma loteria."""

    campos = {
        "concurso": (int, Field(gt=0, description="Número do concurso")),
        "data": (str, Field(min_length=8, description="Data do sorteio")),
    }

    for i, col in enumerate(lot.colunas_bolas, 1):
        campos[col] = (
            int,
            Field(ge=1, le=lot.dezena_maxima, description=f"Bola {i}"),
        )

    schema = create_model(
        f"Concurso{lot.nome.replace(' ', '').replace('-', '')}",
        **campos,
    )
    return schema


# Schemas pré-gerados
ConcursoLotofacil = _criar_schema_concurso(LOTOFACIL)
ConcursoDiaDeSorte = _criar_schema_concurso(DIA_DE_SORTE)
ConcursoMegaSena = _criar_schema_concurso(MEGA_SENA)
ConcursoQuina = _criar_schema_concurso(QUINA)
ConcursoLotomania = _criar_schema_concurso(LOTOMANIA)
ConcursoDuplaSena = _criar_schema_concurso(DUPLA_SENA)

SCHEMAS = {
    "lotofacil": ConcursoLotofacil,
    "diadesorte": ConcursoDiaDeSorte,
    "megasena": ConcursoMegaSena,
    "quina": ConcursoQuina,
    "lotomania": ConcursoLotomania,
    "duplasena": ConcursoDuplaSena,
}


def validar_registro(lot: LoteriaConfig, dados: dict) -> dict:
    """Valida um registro usando o schema Pydantic da loteria."""
    schema = SCHEMAS[lot.sigla]
    return schema(**dados).model_dump()
