"""Engine unificado — 1 código base para todas as loterias."""

from typing import Any, Optional

from src.config import LoteriaConfig, TOTAL_CONCURSOS_HISTORICO
from src.api_client import requisitar_json
from src.database import (
    buscar_ultimo_concurso,
    buscar_historico,
    inserir_concurso,
    contar_concursos,
    importar_csv_para_sqlite,
    inicializar_banco,
)
from src.logger import log


class LoteriaEngine:
    """
    Motor genérico para qualquer loteria.

    Uso:
        engine = LoteriaEngine(QUINA, converter_fn=converter_resultado_api)
        engine.atualizar()
        historico = engine.historico()
    """

    def __init__(
        self,
        config: LoteriaConfig,
        converter_fn: Any,
        validar_fn: Any = None,
    ):
        self.config = config
        self._converter = converter_fn
        self._validar = validar_fn
        self._historico_cache: Optional[list[dict]] = None

    @property
    def nome(self) -> str:
        return self.config.nome

    @property
    def sigla(self) -> str:
        return self.config.sigla

    def inicializar(self) -> None:
        """Garante que o banco e os dados existem."""
        inicializar_banco()
        if contar_concursos(self.config) == 0:
            importados = importar_csv_para_sqlite(self.config)
            log.info("%s: %d registros importados do CSV", self.nome, importados)

    def atualizar(self) -> dict[str, Any]:
        """
        Atualiza o histórico buscando novos concursos da API.

        Retorna resumo da operação.
        """
        self.inicializar()
        ultimo_local = buscar_ultimo_concurso(self.config)
        log.info("%s: último concurso local = %s", self.nome, ultimo_local)

        # Busca o mais recente na API
        url_ultimo = f"{self.config.url_api}"
        dados = requisitar_json(url_ultimo)

        if dados is None:
            log.warning("%s: API indisponível, usando dados locais", self.nome)
            return {"status": "offline", "novos": 0}

        ultimo_api = dados.get("numero", 0)
        if ultimo_local and ultimo_api <= ultimo_local:
            log.info("%s: já atualizado (concurso %d)", self.nome, ultimo_local)
            self._historico_cache = None
            return {"status": "atualizado", "novos": 0}

        # Busca concursos faltantes
        inicio = (ultimo_local or 0) + 1
        novos = 0

        for num in range(inicio, ultimo_api + 1):
            url = f"{self.config.url_api}/{num}"
            dados_concurso = requisitar_json(url)
            if dados_concurso is None:
                continue

            try:
                registro = self._converter(dados_concurso)
                if self._validar:
                    self._validar(registro)
                if inserir_concurso(self.config, registro):
                    novos += 1
                    log.debug("%s: concurso %d inserido", self.nome, num)
            except (ValueError, KeyError, TypeError) as exc:
                log.warning(
                    "%s: concurso %d inválido — %s", self.nome, num, exc
                )

        self._historico_cache = None
        log.info("%s: %d novos concursos", self.nome, novos)
        return {"status": "ok", "novos": novos, "ultimo": ultimo_api}

    def historico(self, limite: int = TOTAL_CONCURSOS_HISTORICO) -> list[dict]:
        """Retorna o histórico (com cache em memória)."""
        if self._historico_cache is None:
            self._historico_cache = buscar_historico(self.config, limite)
        return self._historico_cache

    def limpar_cache(self) -> None:
        """Limpa o cache de histórico em memória."""
        self._historico_cache = None

    def total_concursos(self) -> int:
        """Quantidade de concursos no banco."""
        return contar_concursos(self.config)
