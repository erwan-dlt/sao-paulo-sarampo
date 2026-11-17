# Integração e limpeza dos dados — catálogo com contagens

Base para os slides de dados. Números contados nos arquivos de `data/raw` e `data/processed` em 16/11/2026. Para cada item: o que foi encontrado, quantas linhas foram afetadas e o que foi feito (**corrigido**, **mantido e sinalizado** ou **removido**).

## 1. Integração: de dois trabalhos para uma base

| Antes | Depois |
|---|---|
| 4 versões da tabela "uma linha por município" (2 de cada subgrupo), cada uma calculando as variáveis do seu jeito | 1 módulo (`scripts/base.py`) usado por todas as análises |
| 2 bases de casos: Brasil inteiro 2019–2020 (86.702 notificações) e só SP 2019–2020 | 1 base: residentes de SP, 2007–2026 (94.429 notificações de 257.378 no Brasil) |
| 3 malhas municipais; a processada tinha 26 MB | 1 malha oficial (IBGE API v3); processada com 0,8 MB |
| Cobertura de um espelho de terceiros (HuggingFace), 2016–2018 | Cobertura oficial: TABNET 2012–2022 + InfoMS 2023–2026 |
| População TabNet 2019 + estimativas IBGE com degrau em 2022 | Uma série (Ministério da Saúde, 2000–2025) para todos os anos |
| 11 arquivos brutos e 6 processados do subgrupo 1 substituídos | Fontes oficiais, sem duplicata (o EXANBR19 dos dois lados era idêntico byte a byte) |

**Modelo de dados.** Três tabelas, uma por nível, ligadas por `co_ibge` (6 dígitos) + `ano`: notificação (94.429 linhas), município (645), município × ano (645 × 15 = 9.675). Não é uma tabela só porque misturar níveis repetiria linhas.

**Junção das fontes com os 645 municípios** (todas com 645 municípios, junção 1 para 1 validada):

| Fonte | Linhas lidas | Ajuste necessário |
|---|---|---|
| SINAN (notificações) | 257.378 no Brasil → 94.429 em SP | município de residência já em 6 dígitos |
| População Ministério da Saúde (POPSVS) | ~900 mil por ano no Brasil → 2.716.740 em SP (26 anos × sexo × idade) | código de 7 → 6 dígitos; 2025 com nomes de campo diferentes |
| IBGE/SIDRA estimativas, PIB, Censo | 7.740 + 7.740 + 1.935 | código de 7 → 6 dígitos; "-" = zero |
| TABNET cobertura | 7.095 (2012–2022) + 10.965 (1995–2011) | extraída do HTML do TABNET |
| InfoMS cobertura | 4 planilhas do Brasil, todas as vacinas → 645 × 4 anos | ano identificado pelo denominador do 2º reforço da DTP (nascidos 4 anos antes) |
| REGIC 2018 | Brasil → 645 | código de 7 → 6 dígitos; 390 municípios sem arranjo (isolados, não é dado faltante) |
| Malha IBGE | 645 polígonos | 3 multipolígonos; 3 centroides caíam fora do polígono (trocados por ponto interno); vizinhança calculada (Ilhabela sem vizinho) |
| RIPSA | Brasil → 645 | fonte de nome, região de saúde (62) e RRAS (19) |
| SIH (TABNET) | 1.284 linhas, 107 municípios | 7.101 município-anos ausentes = zero internações (o TABNET omite linhas vazias) |

## 2. Limpeza do SINAN

| Problema | Linhas afetadas | Tratamento |
|---|---|---|
| Ano do exantema digitado errado (ex.: 10/08/2012 com sintomas em 10/08/2019) ou ausente | 90 confirmados (67 sem data; 23 implausíveis) | **Corrigido** pela regra `DT_CASO`: usa os primeiros sintomas se o exantema faltar ou estiver >365 dias antes / >30 dias depois da notificação. 2019: 18.025 → 18.109 (RIPSA: 18.113) |
| Data de sintomas com ano 1985 num caso de 2019 | 1 | mantido e sinalizado (a data do caso vem do exantema) |
| Idade codificada (milhar = unidade: 1 hora, 2 dia, 3 mês, 4 ano; ex.: 4025 = 25 anos) | 19.102 confirmados: 15.565 em anos, 3.492 em meses, 45 em dias | **Decodificado**; 0 inválidas; 44 sem ano de nascimento |
| Linhas idênticas nos 33 campos exportados | 134 linhas (67 pares), quase todas descartadas; 2 pares entre confirmados | mantidas: diferem em campos não exportados (zero duplicata exata nos 107 campos originais em 2019) |
| Classificação final | 94.429: 19.102 sarampo (1), 71.783 código 3, 2.262 código 2, 334 código 8, 948 vazias | só `CLASSI_FIN = 1` entra como caso (significado dos demais códigos: conferir no dicionário) |
| Campos ignorados ou vazios (2019, 18.109 casos) | vacina 3.257 (18%), evolução 2.769 (15%), autoctonia 3.286 (18%), internação 1.731 (10%) | mantidos como "desconhecido", nunca como "não" |
| Datas incoerentes (2019) | exantema antes dos sintomas 617; internação antes dos sintomas 75; internado sem data 90; vacinado sem data da dose 1.483; dose depois do caso 255 | mantidos e sinalizados; nenhuma data foi inventada |
| Nomes, endereços e texto livre | todos | **removidos** na exportação (32 campos de 107) |

## 3. População

| Problema | Afetado | Tratamento |
|---|---|---|
| Degrau entre estimativa IBGE 2021 (46,65 mi) e Censo 2022 (44,41 mi) | 96 municípios com salto >15% | **trocado** pela série do Ministério da Saúde (maior salto anual: 6,2%) |
| Censo conta 3% menos que as projeções (pessoas não recenseadas) | 2022 | a série do Ministério já ajusta às projeções do IBGE (nota técnica em `docs/`) |
| Sem estimativa oficial de 2023 (versão anterior interpolava) | 645 | resolvido pela série do Ministério (sem interpolação) |
| 2026 sem população | 645 | deixado vazio |
| Idades acima de 80 agrupadas | — | faixa "80 e mais" |

## 4. Cobertura vacinal

| Problema | Afetado | Tratamento |
|---|---|---|
| Cobertura acima de 100% (vacinação de crianças de cidades vizinhas; denominador pequeno) | D1: 4.313 de 9.675 município-anos (45%); D2: 2.412 (25%); acima de 200%: 103 e 51 | **mantida**; sensibilidades com teto de 100 e como ausente; na projeção, agregação por região (doses e população-alvo somadas) |
| Troca de sistema TABNET → InfoMS em 2023, sem ano comum | D1 estadual 78% (2022) → 94% (2023); capital 68% → 95% | coluna `fonte_cobertura`; projeção só com InfoMS |
| DATASUS avisa que 2020–2022 estão "em fase de revisão" | 3 anos | sinalizado; não entram nos modelos (janela 2016–2018) |
| Planilhas do InfoMS sem o ano | 4 arquivos | ano identificado pelo denominador do 2º reforço da DTP |
| D2 inexistente em 2012 | 645 | vazio |
| Cobertura zero | D1 2; D2 30 | mantida |
| D2 maior que D1 no mesmo ano | 1.813 | mantido (populações-alvo diferentes) |
| Diferença com o espelho antigo em 2017 | mediana D1 90% (TABNET) × 96% (espelho) | sinalizado; causa não identificada |

## 5. Outras fontes

| Problema | Afetado | Tratamento |
|---|---|---|
| SIH ≠ caso confirmado (2019: 582 internações SIH × 2.256 internados SINAN; 2021–2024 com internações e zero caso) | 41 município-anos com mais internações que casos | mantido como **estimativa** (`internacoes_sih`) |
| SIH até 1997 em CID-9 com zero à esquerda (sarampo = `0055x`; `055093` é hérnia inguinal) | 1996–1997 | **corrigido** (a primeira leitura pegava hérnias) |
| Data de internação AAMMDD em 1996–97 e AAAAMMDD em 1998 | 1996–1998 | convertida |
| PIB municipal de 2024 não publicado | 645 | **estimado** (PIB 2023 × 1,034 × 1,0408) e marcado; não entra nas análises |

## 6. Auditorias automáticas

- `prepare_data.py` para se o total de 2019 mudar (18.109 pela regra; 18.025 só pelo exantema) ou se houver duplicata exata na coorte.
- Casos do painel = contagem das notificações, em todos os 9.675 município-anos.
- Manifesto com SHA-256 de 44 arquivos (38 brutos e 6 processados); o notebook confere antes de rodar.
- Cobertura, PIB, REGIC e geografia da base nova conferidos linha a linha contra a tabela única anterior: idênticos (cobertura do InfoMS com diferença de arredondamento < 0,0001).
- Totais por ano conferidos contra a RIPSA (2019: 18.109 × 18.113; 2012–2015 iguais ou com 1 caso de diferença).
