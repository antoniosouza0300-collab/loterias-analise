"""Camada de integração entre o Engine e o dashboard Gradio."""

from typing import Any, Optional

from src.config import LoteriaConfig, TODAS_LOTERIAS
from src.engine import LoteriaEngine
from src.logger import log

# Engines lazy-loaded
_engines: dict[str, LoteriaEngine] = {}


def _get_converter(lot: LoteriaConfig) -> Any:
    """Retorna a função converter de cada loteria."""
    if lot.sigla == "lotofacil":
        from src.atualizador import converter_resultado_api
        return converter_resultado_api
    elif lot.sigla == "diadesorte":
        from src.atualizador_dia import converter_resultado_api
        return converter_resultado_api
    elif lot.sigla == "megasena":
        from src.atualizador_mega import converter_resultado_api
        return converter_resultado_api
    elif lot.sigla == "quina":
        from src.atualizador_quina import converter_resultado_api
        return converter_resultado_api
    elif lot.sigla == "lotomania":
        from src.atualizador_lotomania import converter_resultado_api
        return converter_resultado_api
    raise ValueError(f"Lotera desconhecida: {lot.sigla}")


def get_engine(lot: LoteriaConfig) -> LoteriaEngine:
    """Retorna o engine da loteria (cria se não existir — lazy)."""
    if lot.sigla not in _engines:
        log.info("Inicializando engine: %s", lot.nome)
        converter = _get_converter(lot)
        _engines[lot.sigla] = LoteriaEngine(lot, converter_fn=converter)
    return _engines[lot.sigla]


def atualizar_loteria(lot: LoteriaConfig) -> str:
    """Atualiza uma loteria e retorna resumo textual."""
    try:
        engine = get_engine(lot)
        resultado = engine.atualizar()
        status = resultado.get("status", "desconhecido")
        novos = resultado.get("novos", 0)
        total = engine.total_concursos()

        if status == "offline":
            return f"⚠️ API indisponível. Usando {total} concursos locais."
        if novos == 0:
            return f"✅ {lot.nome} já atualizado ({total} concursos)."
        return f"🚀 {novos} novos concursos! Total: {total}."

    except Exception as exc:
        log.error("Erro ao atualizar %s: %s", lot.nome, exc, exc_info=True)
        return f"❌ Erro: {exc}"


def carregar_historico(
    lot: LoteriaConfig, limite: int = 100
) -> list[dict[str, Any]]:
    """Carrega histórico (lazy — só busca do banco quando chamado)."""
    try:
        engine = get_engine(lot)
        return engine.historico(limite)
    except Exception as exc:
        log.error("Erro ao carregar %s: %s", lot.nome, exc)
        return []


def obter_score_jogo(
    lot: LoteriaConfig, jogo: list[int]
) -> str:
    """Calcula e formata o score de um jogo."""
    from src.score import calcular_score, formatar_score

    avaliar_fn = _get_avaliar_regras(lot)
    if avaliar_fn is None:
        return "⚠️ Função de regras não disponível."

    resultado = calcular_score(jogo, avaliar_fn)
    return formatar_score(resultado)


def _get_avaliar_regras(lot: LoteriaConfig) -> Optional[Any]:
    """Retorna a função avaliar_regras de cada loteria."""
    try:
        if lot.sigla == "lotofacil":
            from src.regras import avaliar_regras
            return avaliar_regras
        elif lot.sigla == "diadesorte":
            from src.regras_dia import avaliar_regras
            return avaliar_regras
        elif lot.sigla == "megasena":
            from src.regras_mega import avaliar_regras
            return avaliar_regras
        elif lot.sigla == "quina":
            from src.regras_quina import avaliar_regras
            return avaliar_regras
        elif lot.sigla == "lotomania":
            from src.regras_lotomania import avaliar_regras
            return avaliar_regras
    except ImportError:
        return None
    return None


def obter_tendencias(lot: LoteriaConfig) -> str:
    """Retorna resumo de tendências da loteria."""
    from src.tendencias import resumo_tendencias_texto
    historico = carregar_historico(lot)
    return resumo_tendencias_texto(historico, lot)


def obter_grafico_frequencia(lot: LoteriaConfig):
    """Retorna gráfico Plotly de frequência."""
    from src.graficos import grafico_frequencia_dezenas
    historico = carregar_historico(lot)
    return grafico_frequencia_dezenas(historico, lot)


def obter_grafico_atraso(lot: LoteriaConfig):
    """Retorna gráfico Plotly de atraso."""
    from src.graficos import grafico_atraso_dezenas
    historico = carregar_historico(lot)
    return grafico_atraso_dezenas(historico, lot)


def obter_grafico_soma(lot: LoteriaConfig):
    """Retorna gráfico Plotly de soma temporal."""
    from src.graficos import grafico_soma_temporal
    historico = carregar_historico(lot)
    return grafico_soma_temporal(historico, lot)


def obter_grafico_pares(lot: LoteriaConfig):
    """Retorna gráfico Plotly de pares vs ímpares."""
    from src.graficos import grafico_pares_impares
    historico = carregar_historico(lot)
    return grafico_pares_impares(historico, lot)
