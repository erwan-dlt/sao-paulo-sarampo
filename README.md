# Sarampo no estado de São Paulo — o surto de 2019 e a proteção das crianças em 2026–2027

Projeto PTC3567 (Poli-USP). Caracterização do surto de sarampo de 2019 em São Paulo (18.109 casos confirmados), modelos municipais com validação espacial, análise por geração de nascimento e projeção para 2026–2027 de quantas crianças ficam sem vacina. O relatório é o notebook `sarampo_sp_2019.ipynb`, na raiz, já executado.

**Principais resultados**

- A cobertura vacinal infantil recente **não ajuda a prever** onde houve casos nem quantos: o porte do município explica quase tudo.
- O risco seguiu a **geração**: nascidos em 1989–2001 (dose única na rotina) tiveram 93 casos por 100 mil e 44% dos casos; bebês de 2018–2019, 425 por 100 mil.
- Lugar e geração juntos explicam 34% da deviance no nível município × geração, contra 14% só com o lugar.
- Em 2026–2027, mantida a cobertura de 2023–2025, cerca de 40 mil crianças ficam sem a 1ª dose e 148 mil sem a 2ª. Com 95% em todas as regiões, seriam 34 mil e 47 mil.

## Organização

| Caminho | Conteúdo |
|---|---|
| `sarampo_sp_2019.ipynb` | Relatório: 19 seções, tabelas e figuras já executadas |
| `data/raw/` | Fontes brutas (ver `FONTES.md`) |
| `data/processed/` | Tabelas derivadas lidas pelas análises e manifesto de hashes |
| `scripts/prepare_data.py` | Gera `data/processed` a partir de `data/raw`, sem rede |
| `scripts/base.py` | Leitura única dos dados e decisões comuns (coorte, janela de cobertura, validação por RRAS) |
| `scripts/dbc.py` | Leitor dos arquivos `.dbc` do DATASUS em Python puro |
| `scripts/modelagem.py`, `clustering.py` | Modelos de contagem (seção 12) e perfis municipais (seção 13) |
| `scripts/modelo_alvos.py` | Classificador "o município teve caso?" (seção 14) |
| `scripts/coortes_suscetibilidade.py`, `sinan_coortes.py`, `modelo_lugar_geracao.py` | Gerações e lugar × geração (seções 15–16) |
| `scripts/historico_1997.py` | Epidemia de 1997 × surto de 2019 (seção 17) |
| `scripts/projecao.py` | Cenários 2026–2027 (seção 18) |
| `scripts/coleta/` | Scripts que baixaram as fontes (precisam de rede; não são necessários para reproduzir) |
| `results/` | Saídas dos scripts, uma pasta por análise |
| `docs/` | Nota técnica da série de população do Ministério da Saúde |
| `FONTES.md` | Proveniência, dicionário de dados, regras do projeto, pendências e limites |

## Instalar

Use **Python 3.10, 3.11 ou 3.12, de 64 bits**. Os resultados versionados foram gerados com Python 3.10.11 e as versões de `requirements.txt`. Abra um terminal na pasta deste README.

**Windows — PowerShell**

```powershell
py --version
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Linux / macOS**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

No Ubuntu/Debian, se faltar o módulo `venv`: `sudo apt install python3-venv`.

## Executar

Os dados processados e os resultados já estão no repositório. Para só ler ou rodar o notebook:

```bash
.venv/bin/python -m jupyterlab            # Windows: .\.venv\Scripts\python.exe -m jupyterlab
```

Abra `sarampo_sp_2019.ipynb` na raiz e use **Run → Run All Cells**. O notebook confere os hashes de todas as fontes e derivados antes de começar. Também dá para executar sem abrir o Jupyter:

```bash
python -m nbconvert --to notebook --execute --inplace sarampo_sp_2019.ipynb
```

### Reconstruir tudo do zero

Na raiz do projeto, com o ambiente ativado:

```bash
python scripts/prepare_data.py            # data/raw -> data/processed (cerca de 1 min)
python scripts/modelagem.py               # results/ml (alguns minutos)
python scripts/clustering.py              # results/clustering
python scripts/modelo_alvos.py            # results/classificador
python scripts/coortes_suscetibilidade.py # results/geracoes
python scripts/sinan_coortes.py
python scripts/modelo_lugar_geracao.py
python scripts/historico_1997.py          # results/historico
python scripts/projecao.py                # results/projecao
```

O notebook também recalcula sozinho o que estiver desatualizado: compara os hashes das entradas de `modelagem.py` e `clustering.py` com os registrados em `results/` e roda de novo se algo mudou. Para forçar, defina `RECALCULAR_ML`, `RECALCULAR_CLUSTERING` ou `RECALCULAR_NOSSOS` como `True` nas células correspondentes.

`prepare_data.py` verifica os totais de referência (18.109 casos em 2019 pela regra do projeto; 18.025 só pelo exantema). Se uma fonte for trocada por outra versão, ele para e mostra a divergência. Não remova esses controles para forçar a execução.

## Decisões do projeto

Escolhas nossas, cada uma com alternativa testada no notebook:

| Decisão | Escolha | Alternativa (sensibilidade) |
|---|---|---|
| Ano do caso | Início do exantema; primeiros sintomas se o exantema faltar ou for implausível (18.109 casos em 2019) | Só exantema (18.025) |
| População | Série revisada do Ministério da Saúde (POPSVS) | Estimativas IBGE da época |
| Cobertura pré-surto | Média 2016–2018 | Teto de 100% ou valores > 100 como ausentes |
| Validação espacial | Uma RRAS de fora por vez (19) | 5 blocos k-means, 5 faixas de longitude, divisão aleatória |
| Projeção | Três cenários de cobertura por RRAS (InfoMS 2023–2025) | — (cenários, não previsão) |

## Histórico

A primeira versão (11/11/2026) caracterizava o surto e testava modelos e clustering com dados de 2019. Em 16/11/2026 ela foi integrada ao trabalho do outro subgrupo do grupo: base de dados única (SINAN 2007–2026, população do Ministério da Saúde, cobertura TABNET/InfoMS, REGIC), validação por RRAS e as seções 14 a 19. Os números da primeira versão mudaram pouco; as diferenças estão explicadas no notebook e em `FONTES.md`.

## Observações

As análises são descritivas e exploratórias. Cobertura administrativa não é imunidade individual; associação municipal não demonstra causalidade; a projeção conta crianças sem dose sob cenários explícitos e não prevê casos. Consulte `FONTES.md` antes de reutilizar os dados.
