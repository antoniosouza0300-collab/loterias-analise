from collections import Counter
from typing import Dict, List, Any

def analisar_temperatura_dezenas(historico: List[Dict[str, Any]], ultimos_n: int = 20) -> Dict[str, List[int]]:
    """
    Analisa o histórico e classifica as dezenas de 1 a 25 em quentes, mornas e frias
    com base nos últimos N concursos.
    """
    if not historico:
        return {"quentes": [], "mornas": [], "frias": list(range(1, 26))}

    # Pega apenas os últimos N concursos para análise recente
    concursos_recentes = historico[-ultimos_n:]
    
    # Conta a frequência de cada dezena
    contador = Counter()
    for reg in concursos_recentes:
        for i in range(1, 16):
            bola = reg.get(f"bola{i}")
            if bola is not None:
                contador[int(bola)] += 1

    # Garante que todas as dezenas de 1 a 25 apareçam na contagem (mesmo que 0)
    frequencias = {dez: contador.get(dez, 0) for dez in range(1, 26)}
    
    # Ordena da mais frequente para a menos frequente
    dezenas_ordenadas = sorted(frequencias.keys(), key=lambda d: frequencias[d], reverse=True)

    # Divide em terços: Top 8 quentes, 9 mornas, 8 frias (total 25 dezenas)
    quentes = dezenas_ordenadas[:8]
    mornas = dezenas_ordenadas[8:17]
    frias = dezenas_ordenadas[17:]

    return {
        "quentes": sorted(quentes),
        "mornas": sorted(mornas),
        "frias": sorted(frias),
        "frequencias_completas": frequencias
    }
