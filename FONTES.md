# Fontes, proveniência e transformação dos dados

PTC3567 · Sarampo em São Paulo · base integrada em 16/11/2026.

Convenção usada aqui e no notebook: **dado** é o que vem de uma base oficial; **regra do projeto** é uma escolha nossa, sempre com a alternativa testada; **interpretação** é leitura nossa dos resultados.

## 1. Fontes brutas (`data/raw`)

| Arquivo | Fonte | Recorte | Coletado por | Uso |
|---|---|---|---|---|
| `sinan/EXANBR07.dbc` … `EXANBR26.dbc` | SINAN, doenças exantemáticas, FTP DATASUS `dissemin/publicos/SINAN/DADOS` (pastas `FINAIS` e `PRELIM`; os anos mais recentes são preliminares) | Notificações do Brasil, 2007–2026 | download manual do FTP | Casos confirmados, idade, datas, vacinação, gravidade |
| `pop_ms_sp.csv.gz` | Ministério da Saúde, série revisada de população residente (POPSVS), FTP DATASUS `dissemin/publicos/IBGE/POPSVS/POPSBRaa.zip` | SP, 2000–2025, município × sexo × idade (0–80; 80 = 80 e mais) | `scripts/coleta/popsvs.py` | Denominador principal; população por idade |
| `sidra_pop_estim.csv` | IBGE, SIDRA 6579 (variável 9324) | SP, 2012–2021, 2024–2025 | `scripts/coleta/sidra.py` | Sensibilidade do denominador |
| `sidra_censo2022.csv` | IBGE, Censo 2022 (variáveis 93, 614, 6318) | SP, 2022 | `scripts/coleta/sidra.py` | Área territorial; população do Censo (sensibilidade) |
| `sidra_pib.csv` | IBGE, SIDRA 5938 (variável 37) | SP, 2012–2023 | `scripts/coleta/sidra.py` | PIB municipal |
| `cobertura_scr_2012_2022.csv` | PNI, TABNET `bd_pni/cpnibr.def`, cobertura tríplice viral D1 e D2 | SP por município, 2012–2022 | `scripts/coleta/tabnet_pni.py` + `parse_tabnet.py` | Cobertura municipal |
| `cobertura_hist_1995_2011.csv` | PNI, TABNET `cpnibr.def`: vacina sarampo (monovalente) e tríplice D1 | SP por município, 1995–2011 | `scripts/coleta/tabnet_pni_anos.py` + `parse_tabnet.py` | Cobertura das coortes antigas (seção 15) |
| `cobertura_uf_sp_1995_2022.csv` | PNI, TABNET `cpnibr.def`, linha = UF | Estado de SP, 1995–2022 | idem | Cobertura estadual histórica |
| `cobertura_infoms_2023.xlsx` … `2026_parcial.xlsx` | Painel InfoMS de cobertura vacinal, exportado manualmente | Brasil, todas as vacinas, 2023–2026 (2026 parcial) | exportação manual | Cobertura municipal com doses e população-alvo |
| `REGIC2018_Municipios_Hierarquia_e_regiao.xlsx` | IBGE, REGIC 2018 | Brasil | download manual (geoftp IBGE) | Hierarquia urbana e arranjos populacionais |
| `malha_sp.json` | IBGE, API de malhas v3, qualidade intermediária | Municípios de SP | download | Centroides, distância à capital, vizinhança, mapas |
| `ripsa008mb.csv.zip` | RIPSA, indicador MRB.1.01 (casos de sarampo) | Brasil, 2012–2024 | download manual | Região de saúde e RRAS de cada município; conferência dos totais de casos |
| `sih_sarampo.csv` | SIH/SUS, TABNET `sih/cnv/nrsp.def`, lista de morbidade CID-10 "sarampo", por residência e ano de atendimento | SP por município, 2012–2024 | `scripts/coleta/tabnet_sih.py` | Internações SUS (estimativa, não caso confirmado) |
| `sih_sarampo_1996_1998_municipio.csv`, `..._mes.csv` | SIH/SUS, arquivos RD do FTP DATASUS 1996–1998 (CID-9 055 até 1997, CID-10 B05 em 1998) | SP | `scripts/coleta/sih_sarampo_1996_1998.py` | Epidemia de 1997 (seção 17) |
| `cve_sarampo_serie_1980_2026.pdf` | Centro de Vigilância Epidemiológica (CVE-SP), série histórica de casos | Estado de SP, 1980–2026 | download manual | Referência para o contexto histórico |

Arquivos grandes baixados pelos scripts de coleta ficam fora do git (`.gitignore`): `data/raw/popsvs/` (zips da série de população, 86 MB) e `data/raw/sih_1996_1998/` (DBC do SIH, 284 MB). Os CSV derivados deles estão versionados.

A nota técnica da série de população está em `docs/NT-POPULACAO-RESIDENTE-2000-2024.pdf`.

### Notas sobre as fontes

- **População (POPSVS).** Segue o método da RIPSA: parte dos Censos 2000, 2010 e 2022 e é ajustada às projeções estaduais do IBGE (revisão 2024). Por isso fica cerca de 3% acima da contagem bruta do Censo 2022 e coincide com as estimativas oficiais do IBGE para 2024 e 2025. As estimativas publicadas pelo IBGE antes do Censo (`sidra_pop_estim.csv`) têm um degrau artificial entre 2021 (46,65 milhões) e 2022 (44,41 milhões, Censo); por isso ficaram só como sensibilidade.
- **Cobertura.** O TABNET termina em 2022; de 2023 em diante só existe o painel InfoMS, exportado à mão. As planilhas não trazem o ano: ele foi identificado pelo denominador do 2º reforço da DTP, que corresponde aos nascidos quatro anos antes. A troca de sistema cria um salto (D1 estadual de 78% em 2022 para 94% em 2023), marcado na coluna `fonte_cobertura`. A versão anterior deste projeto usava um espelho de terceiros do SI-PNI (HuggingFace). Os valores são próximos, exceto em **2017**: a mediana municipal da D1 é 90% no TABNET e era 96% no espelho. A causa da diferença não foi identificada.
- **Internações (SIH).** Diagnóstico hospitalar no SUS, sem a confirmação da vigilância. Em 2019 há 582 internações no SIH contra 2.256 internados no SINAN, e entre 2021 e 2024 há internações em anos sem caso confirmado. Use como estimativa, nunca como "casos graves".
- **PIB 2024.** Ainda não publicado (previsão do IBGE: dez/2026). Foi estimado como PIB 2023 × 1,034 (crescimento real de SP em 2024, Seade) × 1,0408 (deflator implícito do Brasil em 2024, SIDRA 1846/6612), supondo crescimento igual em todos os municípios. Não entra em nenhuma análise (a janela usada é 2016–2018).

## 2. Processamento (`scripts/prepare_data.py`)

Lê só `data/raw`, sem rede, e grava `data/processed`. Os DBC são lidos por `scripts/dbc.py`, que descomprime em Python puro, sem dependências. O script confere os totais e grava um manifesto com o SHA-256 de cada fonte e derivado; o notebook recusa rodar se algum hash mudar.

**Regras do projeto aplicadas aqui:**

- **Data do caso (`DT_CASO`).** Início do exantema (`DT_INICIO_`). Se ele faltar, ou estiver mais de 365 dias antes ou mais de 30 dias depois da notificação, usa-se a data dos primeiros sintomas (`DT_SIN_PRI`). Motivo: há exantemas com ano digitado errado (ex.: 10/08/2012 com sintomas em 10/08/2019 e notificação em 16/08/2019). Resultado em 2019: 18.109 casos, contra 18.113 da RIPSA. Alternativa testada: só o exantema, 18.025 casos (seção 10 do notebook).
- **Caso:** `CLASSI_FIN = 1`, residência em SP (`SG_UF = 35`).
- **Internações SIH:** município ausente na consulta TABNET = 0 internações, porque o TABNET omite linhas vazias. 2017 inteiro ausente = 0, coerente com zero caso confirmado no SINAN.

### Dicionário dos arquivos processados

**`municipio.csv`**: uma linha por município (645).

| Coluna | Descrição | Fonte |
|---|---|---|
| `co_ibge` | Código IBGE de 6 dígitos (chave de todas as tabelas) | IBGE |
| `no_municipio`, `co_regiao_saude`, `no_regiao_saude`, `rras` | Nome, região de saúde e RRAS (19 no estado) | RIPSA |
| `area_km2` | Área territorial | Censo 2022 |
| `regic_hierarquia`, `regic_nivel`, `regic_grupo` | Hierarquia urbana (1A = metrópole … 5 = centro local); nível 1–11 em ordem | REGIC 2018 |
| `arranjo_populacional`, `regic_regiao_influencia` | Arranjo populacional (vazio se o município não pertence a um) e região de influência | REGIC 2018 |
| `lat`, `lon` | Centroide (ou ponto interno, se o centroide cair fora do polígono) | malha IBGE |
| `dist_capital_km` | Distância em linha reta até o centroide da capital (haversine) | calculada |
| `n_vizinhos` | Municípios que fazem fronteira (Ilhabela = 0) | calculada |

**`municipio_ano.csv`**: município × ano, 2012–2026 (9.675 linhas).

| Coluna | Descrição | Fonte |
|---|---|---|
| `casos` | Casos confirmados com `DT_CASO` no ano | SINAN |
| `internacoes_sih` | Internações SUS com diagnóstico de sarampo (estimativa; vazio após 2024) | SIH |
| `cob_triplice_d1`, `cob_triplice_d2` | Cobertura administrativa da tríplice viral, % (pode passar de 100; D2 vazia em 2012) | TABNET até 2022, InfoMS depois |
| `fonte_cobertura` | `TABNET PNI`, `InfoMS` ou `InfoMS (parcial)` | — |
| `populacao` | População residente, série do Ministério da Saúde (vazia em 2026) | POPSVS |
| `populacao_ibge` | População publicada pelo IBGE na época (estimativa; 2022 = Censo; 2023 vazio) | SIDRA |
| `pib_mil_reais`, `fonte_pib` | PIB a preços correntes, mil R$ (2024 estimado; ver acima) | SIDRA 5938 |

**`notificacoes.csv`**: uma linha por notificação de residente de SP, arquivos 2007–2026 (94.429 linhas). Os 32 campos do SINAN estão no [dicionário de exantemáticas](https://goias.gov.br/saude/wp-content/uploads/sites/34/2013/08/exantematica1-b5a.pdf). Não há nomes, endereços nem texto livre. Datas em ISO; demais campos como texto. Acrescentados: `arquivo`, `DT_CASO` e `ORIGEM_DT_CASO` (`exantema` ou `primeiros sintomas`).

**`cobertura_estado.csv`**: cobertura estadual 1995–2026. Até 2022, TABNET (linha = UF); de 2023 em diante, InfoMS (soma das doses / soma da população-alvo dos municípios). A monovalente vai até 2003.

**`vizinhos.json`**: lista de municípios vizinhos de cada município. **`malha.json`**: anéis dos polígonos (lon, lat) para os mapas.

## 3. Variáveis das análises (`scripts/base.py`)

Todas as análises leem os dados pelo mesmo módulo, que fixa as decisões comuns:

- **Coorte de 2019:** 18.109 casos (`DT_CASO` em 2019).
- **Cobertura pré-surto:** média de 2016–2018 (D1 e D2) e diferença 2018 − 2016. Os tratamentos dos valores acima de 100% (original, teto de 100 ou ausente) são sensibilidades.
- **População de 2019** da série do Ministério da Saúde; **PIB por habitante** médio de 2016–2018; frações etárias de 2019.
- **Validação espacial:** uma RRAS de fora por vez. Os 5 blocos k-means das coordenadas, as faixas de longitude e a divisão aleatória são sensibilidades.

## 4. Resultados (`results/`)

| Pasta | Script | Conteúdo |
|---|---|---|
| `ml` | `modelagem.py` | Modelos de contagem (seção 12): previsões externas, métricas, ajustes, permutação, hashes |
| `clustering` | `clustering.py` | Perfis municipais (seção 13) |
| `classificador` | `modelo_alvos.py` | Classificador "teve caso" com quatro alvos (seção 14) |
| `geracoes` | `coortes_suscetibilidade.py`, `sinan_coortes.py`, `modelo_lugar_geracao.py` | Incidência por ano de nascimento; modelo município × geração (seções 15–16) |
| `historico` | `historico_1997.py` | 1997 (SIH) × 2019 (seção 17) |
| `projecao` | `projecao.py` | Cenários 2026–2027 por RRAS e estado (seção 18) |

## 5. Pendências de verificação

Estes pontos aparecem no texto como interpretação ou "a conferir" até terem fonte:

- **Calendário vacinal:** dose única na rotina para os nascidos até ~2001, segunda dose a partir de 2004 e campanha de 2008 para adultos de 20–39 anos. Falta citar o documento oficial do PNI.
- **`TPAUTOCTO`:** usado como "autóctone do município de residência" (1 = sim, 2 = não, 3 = indeterminado); confirmar no dicionário do SINAN.
- **`NDUPLIC_N`:** marca de duplicidade do SINAN (17 confirmados com valor 1); significado exato a confirmar antes de qualquer uso. Hoje o campo não é usado.
- **Cobertura de 2017:** a diferença entre o TABNET e o espelho usado na versão anterior não foi explicada.

## 6. Limites

As associações municipais são exploratórias e não causais. Cobertura administrativa não é imunidade, e os indicadores são infantis enquanto os casos incluem todas as idades. Incidência de casos notificados e confirmados não equivale à incidência de infecções. Residência não é local de infecção. Não há identificador individual para auditar duplicidades de pessoas. A projeção conta crianças sem dose sob cenários explícitos; não prevê casos.
