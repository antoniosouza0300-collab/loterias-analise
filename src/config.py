"""Configuração centralizada de todas as loterias."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class LoteriaConfig:
    """Configuração imutável de uma loteria."""
    nome: str
    sigla: str
    total_dezenas: int
    dezena_maxima: int
    endpoint: str
    emoji: str
    cor: str
    colunas_bolas: list[str] = field(default_factory=list)
    sorteios_semana: str = ""

    def __post_init__(self):
        if not self.colunas_bolas:
            object.__setattr__(
                self, "colunas_bolas",
                [f"bola{i}" for i in range(1, self.total_dezenas + 1)],
            )

    @property
    def colunas_csv(self) -> list[str]:
        return ["concurso", "data"] + self.colunas_bolas

    @property
    def arquivo_csv(self) -> str:
        return str(Path("data") / f"{self.sigla}.csv")

    @property
    def url_api(self) -> str:
        return f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{self.endpoint}"


# ── Instâncias ──────────────────────────────────────────────

LOTOFACIL = LoteriaConfig(
    nome="Lotofácil",
    sigla="lotofacil",
    total_dezenas=15,
    dezena_maxima=25,
    endpoint="lotofacil",
    emoji="🎱",
    cor="#8b5cf6",
    sorteios_semana="Seg–Sáb",
)

DIA_DE_SORTE = LoteriaConfig(
    nome="Dia de Sorte",
    sigla="diadesorte",
    total_dezenas=7,
    dezena_maxima=31,
    endpoint="diadesorte",
    emoji="🍀",
    cor="#10b981",
    sorteios_semana="Ter, Qui, Sáb",
)

MEGA_SENA = LoteriaConfig(
    nome="Mega-Sena",
    sigla="megasena",
    total_dezenas=6,
    dezena_maxima=60,
    endpoint="megasena",
    emoji="🍀",
    cor="#f59e0b",
    sorteios_semana="Ter, Qui, Sáb",
)

LOTOMANIA = LoteriaConfig(
    nome="Lotomania",
    sigla="lotomania",
    total_dezenas=20,
    dezena_maxima=100,
    endpoint="lotomania",
    emoji="🎲",
    cor="#e11d48",
    sorteios_semana="Seg–Sáb",
)

QUINA = LoteriaConfig(
    nome="Quina",
    sigla="quina",
    total_dezenas=5,
    dezena_maxima=80,
    endpoint="quina",
    emoji="🎯",
    cor="#7c3aed",
    sorteios_semana="Seg–Sáb",
)

TODAS_LOTERIAS = [LOTOFACIL, DIA_DE_SORTE, MEGA_SENA, QUINA, LOTOMANIA]

# ── Configurações globais ──────────────────────────────────

TOTAL_CONCURSOS_HISTORICO = 100
API_TIMEOUT = 15
API_TENTATIVAS = 3
API_BACKOFF_BASE = 2  # segundos (2, 4, 8)
CACHE_TTL_SEGUNDOS = 3600  # 1 hora
LOG_NIVEL = "INFO"
LOG_ARQUIVO = "logs/loterias.log"
