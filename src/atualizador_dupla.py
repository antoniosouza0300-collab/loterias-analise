"""Atualizador do histórico da Dupla Sena (6 de 50) via API CAIXA.

A Dupla Sena tem 2 sorteios por concurso. Armazenamos o 1º sorteio
como bolas principais e o 2º como bolas extras (bola7-bola12).
"""

import csv
import json
import tempfile
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import TOTAL_CONCURSOS_HISTORICO, API_TIMEOUT, API_TENTATIVAS
from src.logger import log

ARQUIVO_CSV = "data/duplasena.csv"
URL_API = "https://servicebus2.caixa.gov.br/portaldeloterias/api/duplasena"
TOTAL_DEZENAS = 6
DEZENA_MINIMA = 1
DEZENA_MAXIMA = 50
COLUNAS = (
    ["concurso", "data"]
    + [f"bola{i}" for i in range(1, 7)]
    + [f"bola2s_{i}" for i in range(1, 7)]
)


def converter_data(valor: Any) -> str:
    if isinstance(valor, str) and len(valor) >= 10:
        return valor[:10]
    return str(valor)


def validar_dezena(valor: Any) -> int:
    d = int(valor)
    if d < DEZENA_MINIMA or d > DEZENA_MAXIMA:
        raise ValueError(f"Dezena fora do intervalo: {d}")
    return d


def converter_resultado_api(dados: Any) -> Dict[str, Any]:
    if not isinstance(dados, dict):
        raise ValueError("Resposta da API deve ser um dicionário")

    concurso = dados.get("numero") or dados.get("concurso") or dados.get("id")
    if isinstance(concurso, str) and concurso.isdigit():
        concurso = int(concurso)
    if type(concurso) is not int or concurso <= 0:
        raise ValueError("Concurso inválido na API")

    # 1º sorteio
    dezenas1 = (
        dados.get("listaDezenas")
        or dados.get("dezenas")
        or dados.get("dezenasSorteadasOrdemSorteio")
    )
    if not isinstance(dezenas1, list) or len(dezenas1) != TOTAL_DEZENAS:
        raise ValueError(
            f"1º sorteio: esperadas {TOTAL_DEZENAS} dezenas, "
            f"recebeu {len(dezenas1) if isinstance(dezenas1, list) else 'N/A'}"
        )

    # 2º sorteio
    dezenas2 = (
        dados.get("listaDezenasSegundoSorteio")
        or dados.get("dezenasSegundoSorteio")
        or dados.get("listaDezenas2")
    )
    if not isinstance(dezenas2, list) or len(dezenas2) != TOTAL_DEZENAS:
        dezenas2 = dezenas1  # fallback

    bolas1 = sorted(validar_dezena(d) for d in dezenas1)
    bolas2 = sorted(validar_dezena(d) for d in dezenas2)

    registro: Dict[str, Any] = {
        "concurso": concurso,
        "data": converter_data(dados.get("dataApuracao", "")),
    }
    for i, b in enumerate(bolas1, 1):
        registro[f"bola{i}"] = b
    for i, b in enumerate(bolas2, 1):
        registro[f"bola2s_{i}"] = b

    return registro


def limpar_registro_para_csv(registro: Dict[str, Any]) -> Dict[str, Any]:
    limpo: Dict[str, Any] = {}
    for col in COLUNAS:
        limpo[col] = registro.get(col, "")
    return limpo


def validar_registro(registro: Dict[str, Any]) -> Dict[str, Any]:
    if "concurso" not in registro:
        raise ValueError("Registro sem concurso")
    registro["concurso"] = int(registro["concurso"])
    for col in [f"bola{i}" for i in range(1, TOTAL_DEZENAS + 1)]:
        if col in registro:
            registro[col] = validar_dezena(registro[col])
    return registro


def validar_historico(historico: List[Dict[str, Any]]) -> bool:
    if not historico:
        return True
    concursos = [r["concurso"] for r in historico]
    if len(set(concursos)) != len(concursos):
        raise ValueError("Concursos duplicados no histórico")
    return True


def ler_historico(caminho: Optional[str] = None) -> List[Dict[str, Any]]:
    path = Path(caminho) if caminho else Path(ARQUIVO_CSV)
    if not path.exists():
        return []
    historico = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f)
        if not leitor.fieldnames:
            raise ValueError("Cabeçalho vazio")
        for linha in leitor:
            try:
                historico.append(validar_registro(linha))
            except (ValueError, KeyError) as exc:
                log.warning("Linha inválida ignorada: %s", exc)
    return historico


def gravar_historico(
    historico: List[Dict[str, Any]], caminho: Optional[str] = None
) -> None:
    path = Path(caminho) if caminho else Path(ARQUIVO_CSV)
    registros = sorted(
        [validar_registro(r) for r in historico],
        key=lambda x: x["concurso"],
    )
    validar_historico(registros)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=str(path.parent), prefix=".duplasena_", suffix=".csv"
    )
    try:
        with open(fd, "w", encoding="utf-8", newline="") as f:
            escritor = csv.DictWriter(f, fieldnames=COLUNAS)
            escritor.writeheader()
            for r in registros:
                escritor.writerow(limpar_registro_para_csv(r))
        import os
        os.replace(tmp, str(path))
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise


def consultar_concurso(numero: Optional[int] = None) -> Dict[str, Any]:
    url = URL_API if numero is None else f"{URL_API}/{numero}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
    )
    for tentativa in range(API_TENTATIVAS):
        try:
            with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            log.warning("Tentativa %d falhou: %s", tentativa + 1, exc)
    raise ConnectionError(f"API indisponível após {API_TENTATIVAS} tentativas")


def atualizar_historico(caminho: Optional[str] = None) -> Dict[str, Any]:
    historico = ler_historico(caminho)
    ultimo_local = max((r["concurso"] for r in historico), default=0)

    try:
        dados = consultar_concurso()
        ultimo_api = int(dados.get("numero", 0))
    except Exception as exc:
        log.warning("Dupla Sena: API indisponível — %s", exc)
        return {"status": "offline", "novos": 0, "total": len(historico)}

    if ultimo_api <= ultimo_local:
        return {"status": "atualizado", "novos": 0, "total": len(historico)}

    novos = 0
    for num in range(ultimo_local + 1, ultimo_api + 1):
        try:
            dados_c = consultar_concurso(num)
            registro = converter_resultado_api(dados_c)
            historico.append(registro)
            novos += 1
        except Exception as exc:
            log.warning("Dupla Sena concurso %d: %s", num, exc)

    historico.sort(key=lambda x: x["concurso"])
    historico = historico[-TOTAL_CONCURSOS_HISTORICO:]
    gravar_historico(historico, caminho)

    log.info("Dupla Sena: +%d concursos (total %d)", novos, len(historico))
    return {"status": "ok", "novos": novos, "total": len(historico)}
