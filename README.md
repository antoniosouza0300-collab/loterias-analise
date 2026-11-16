# Análise Estatística de Loterias

Projeto em Python para consultar, armazenar, validar e organizar os resultados históricos de loterias da Caixa Econômica Federal, com dashboard interativo em Gradio.

## Loterias suportadas

| Loteria | Dezenas | Sorteios | Arquivo CSV |
|---------|---------|----------|-------------|
| 🎱 Lotofácil (15 de 25) | 15 de 25 | Seg-Sáb | data/lotofacil.csv |
| 🍀 Dia de Sorte (7 de 31) | 7 de 31 + mês | Ter, Qui, Sáb | data/diadesorte.csv |
| 🍀 Mega-Sena (6 de 60) | 6 de 60 | Ter, Qui, Sáb | data/megasena.csv |
| 🎯 Quina (5 de 80) | 5 de 80 | Seg-Sáb | data/quina.csv |
| 🎲 Lotomania (20 de 100) | 20 de 100 | Seg-Sáb | data/lotomania.csv |

## Funcionalidades

- Dashboard interativo com 6 abas (5 loterias + Analytics)
- Atualização automática via API CAIXA
- Gráficos interativos Plotly
- Score de aderência 0-100
- Tendências temporais
- SQLite + Cache + Retry com backoff
- Validação Pydantic
- CI/CD com GitHub Actions
- 169 testes automatizados

## Instalação

    git clone https://github.com/antoniosouza0300-collab/loterias-analise.git
    cd loterias-analise
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

## Execução

    python -m src.interface

## Testes

    pytest tests/ -v

## Limitações estatísticas

Análises históricas não predizem resultados futuros. Cada combinação válida tem a mesma probabilidade matemática.

## Licença

Licença ainda não definida.
