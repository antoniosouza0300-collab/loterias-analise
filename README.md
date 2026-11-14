# Análise Estatística da Lotofácil

Projeto em Python para consultar, armazenar, validar e organizar os resultados históricos da Lotofácil, mantendo automaticamente os últimos 100 concursos da Caixa Econômica Federal.

## Objetivos

- Consultar os resultados da Lotofácil na API da CAIXA.
- Manter um histórico local em formato CSV.
- Armazenar somente os últimos 100 concursos.
- Atualizar o histórico de forma incremental.
- Evitar registros duplicados.
- Validar os resultados recebidos e os dados armazenados.
- Preservar o arquivo anterior em caso de falha durante a gravação.

## Requisitos

- Python 3.10 ou superior.
- Conexão com a internet para consultar a API da CAIXA.
- Dependências declaradas em `requirements.txt`.

## Estrutura do projeto

```text
loterias-analise/
├── .gitignore
├── README.md
├── requirements.txt
├── data/
│   └── lotofacil.csv
└── src/
    ├── atualizador.py
    ├── atualizador.py.bak
    ├── importador.py
    └── main.py
```

### Arquivos principais

| Arquivo | Responsabilidade |
|---|---|
| `src/main.py` | Ponto de entrada e inicialização do programa |
| `src/atualizador.py` | Consulta a API, valida e atualiza o histórico |
| `src/importador.py` | Importação e validação de resultados em CSV |
| `data/lotofacil.csv` | Histórico local dos concursos |
| `requirements.txt` | Lista de dependências do projeto |
| `src/atualizador.py.bak` | Cópia de segurança do atualizador |

## Instalação

Clone o repositório e acesse a pasta do projeto.

Crie um ambiente virtual:

```bash
python -m venv .venv
```

Ative o ambiente virtual.

**Linux / macOS:**

```bash
source .venv/bin/activate
```

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Execução

### Inicialização principal

Execute na raiz do projeto:

```bash
python -m src.main
```

O programa inicia a rotina de atualização do histórico antes de concluir a inicialização.

### Atualização isolada

Para executar somente a atualização dos resultados:

```bash
python -m src.atualizador
```

## Atualização automática do histórico

Ao executar `python -m src.main`, o programa consulta a API oficial da CAIXA e atualiza o arquivo local.

O atualizador foi implementado para:

- Manter somente os últimos 100 concursos.
- Identificar concursos ausentes no histórico.
- Consultar o concurso mais recente para verificar atualizações.
- Inserir novos resultados sem duplicar registros.
- Evitar gravações quando não existem alterações.
- Preservar a continuidade da sequência de concursos.

A atualização depende de conexão com a internet e da disponibilidade da API da CAIXA.

## Validações implementadas

O atualizador verifica:

- Existência dos campos esperados no registro.
- Identificação válida do concurso.
- Presença de 15 dezenas por resultado.
- Dezenas inteiras entre 1 e 25.
- Ausência de dezenas repetidas no mesmo concurso.
- Ausência de concursos duplicados.
- Continuidade da sequência histórica.
- Organização dos registros por número de concurso.

## Segurança e integridade dos dados

A gravação do histórico utiliza um arquivo temporário e substituição atômica com `os.replace`.

Esse procedimento reduz o risco de deixar o CSV parcialmente gravado caso ocorra uma falha durante a atualização.

Quando não há alterações, o arquivo existente é preservado sem regravação.

## Formato do histórico

O arquivo `data/lotofacil.csv` utiliza as seguintes colunas:

```text
concurso,data,bola1,bola2,bola3,bola4,bola5,bola6,bola7,bola8,bola9,bola10,bola11,bola12,bola13,bola14,bola15
```

Cada linha representa um concurso e suas 15 dezenas sorteadas.

## Critérios estatísticos planejados

Os critérios abaixo fazem parte do planejamento de evolução do projeto. Não devem ser considerados funcionalidades implementadas nesta versão:

- Frequência histórica e classificação de dezenas.
- Soma das dezenas.
- Quantidade de pares e ímpares.
- Números primos.
- Moldura e miolo.
- Repetições e ausências em relação ao concurso anterior.
- Múltiplos de 3.
- Sequência de Fibonacci.
- Linhas, colunas e quadrantes.
- Diagonais, cruz e extremos.
- Filtros configuráveis para avaliação de combinações.
- Geração de relatórios estatísticos.

As definições matemáticas desses critérios deverão ser especificadas e validadas antes da implementação.

## Testes

O projeto declara `pytest` entre as dependências. A estrutura atual, entretanto, ainda não contém uma pasta `tests/` nem uma suíte de testes automatizados documentada.

As validações realizadas pelo próprio atualizador fazem parte da execução do programa e não devem ser confundidas com testes automatizados.

## Limitações estatísticas

As frequências e os padrões históricos descrevem resultados anteriores. Em um sorteio justo, cada combinação válida de 15 dezenas possui a mesma probabilidade matemática de ser sorteada.

Portanto, análises históricas e filtros podem organizar ou selecionar combinações segundo critérios definidos, mas não predizem o próximo resultado nem aumentam a probabilidade matemática de uma combinação específica.

## Licença

Licença ainda não definida.
