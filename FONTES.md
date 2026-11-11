# Fontes, proveniência e transformação dos dados

PTC3567 · Sarampo em São Paulo, 2019 · Organização preparada em 11/11/2026.

## Origem dos arquivos

Os DBC foram fornecidos pelo usuário em `arquivo.zip`; vacinação, PIB e documentos de proveniência vieram de `raw.zip`, reunido em trabalho anterior. As tabelas populacionais e a malha são as fontes utilizadas na análise anterior, preservadas neste projeto. Não se afirma que os DBC ou a cobertura vacinal foram baixados novamente nesta execução.

`data/raw` significa **entrada preservada do projeto**. Nem todos os arquivos dessa pasta são microdados originais: os CSV de vacinação e PIB já eram extrações normalizadas recebidas. A etapa anterior de normalização é documentada, mas não inteiramente reconstruída pelo script deste projeto.

| Arquivo em `data/raw` | Fonte e referência | Papel no projeto |
|---|---|---|
| `EXANBR19.dbc` | SINAN, doenças exantemáticas; notificações nacionais de 2019, arquivo recebido | 68.765 registros nacionais, 107 campos |
| `EXANBR20.dbc` | SINAN, doenças exantemáticas; notificações nacionais de 2020, arquivo recebido | 17.937 registros nacionais, 107 campos; recupera notificações tardias |
| `mmr_2016_2018.csv` | SI-PNI histórico, segundo `mmr_provenance.json`; 2016–2018 | 645 municípios × 3 anos × 2 doses = 3.870 observações |
| `mmr_provenance.json` | Metadados recebidos da preparação anterior | Indicadores, espelho usado, anomalias e limitações da cobertura |
| `gdp_per_capita_2016.csv` | Extração derivada de IBGE/SIDRA | PIB por habitante de 2016; 645 municípios |
| `ibge_sidra_gdp_2016.json` | IBGE/SIDRA, tabela 5938, variável 37, 2016 | Evidência da extração de PIB total utilizada na etapa anterior |
| `ibge_sidra_population_2016.json` | IBGE/SIDRA, tabela 6579, variável 9324, 2016 | Evidência do denominador do PIB por habitante |
| `pop_idade.html` | Ministério da Saúde/TabNet, `popsvs2024br.def`, ano 2019 | População municipal por idade simples; denominador principal |
| `pop_sexo.html` | Mesma série e ano | População municipal por sexo |
| `pop2019.xls` | IBGE, estimativa de 2019, arquivo `POP2019_20220905.xls` | Denominador alternativo, 45.919.049 habitantes no estado |
| `sp_municipios.zip` | IBGE, malha municipal de 2019, São Paulo | 645 municípios, coordenadas e área territorial |
| `query_population.json` | Parâmetros preservados da consulta TabNet | Reprodução documental do recorte populacional |
| `manifesto_consultas_original.json` | Manifesto da coleta anterior | URLs, parâmetros, data de consulta e hashes; inclui consultas históricas de casos não necessárias ao processamento atual |

O total populacional principal é 45.306.139. Essa série revisada não deve ser substituída silenciosamente pela estimativa IBGE alternativa.

## Links das fontes e documentação

- [TabNet nacional de sarampo e rubéola](https://tabnet.datasus.gov.br/cgi/deftohtm.exe?sinannet/cnv/exantbr.def)
- [Dicionário de dados de exantemáticas — Ministério da Saúde](https://goias.gov.br/saude/wp-content/uploads/sites/34/2013/08/exantematica1-b5a.pdf)
- [População municipal por idade e sexo — TabNet](https://tabnet.datasus.gov.br/cgi/deftohtm.exe?ibge/cnv/popsvs2024br.def)
- [Estimativas populacionais IBGE de 2019](https://ftp.ibge.gov.br/Estimativas_de_Populacao/Estimativas_2019/)
- [Malha municipal IBGE 2019 — SP](https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2019/UFs/SP/)
- [SIDRA, tabela 5938](https://sidra.ibge.gov.br/tabela/5938)
- [SIDRA, tabela 6579](https://sidra.ibge.gov.br/tabela/6579)
- [Espelho SI-PNI declarado na proveniência recebida](https://huggingface.co/datasets/SidneyBissoli/sipni-agregados-cobertura)

Os arquivos de proveniência originais podem conter caminhos do computador anterior. Esses caminhos são preservados como metadados e nunca usados na execução.

## Preparação de `data/processed`

1. Descompactar os DBC em DBF temporários com `dbc-to-dbf` e ler os 107 campos com `dbfread` (Latin-1). Concatenar as duas safras sem acrescentar o Parquet de 2019, que duplicaria a base.
2. Exportar 31 campos necessários, incluindo o arquivo de origem. Datas em ISO e códigos preservados. Não agregar as notificações nesse CSV.
3. Ler a população dos 645 municípios e agregar idades simples às faixas da análise. Preservar os denominadores principal e alternativo.
4. Ler atributos e coordenadas da malha e criar a chave SINAN de seis dígitos a partir do código IBGE de sete dígitos.
5. Copiar sem alteração os CSV normalizados de vacinação e PIB para os nomes usados pelo notebook.
6. Gerar o manifesto SHA-256 das fontes e derivados, com versões das dependências. O manifesto não inclui seu próprio hash.

| Arquivo processado | Conteúdo |
|---|---|
| `notificacoes.csv` | 86.702 notificações nacionais, 31 campos; filtros epidemiológicos aplicados no notebook |
| `municipios.csv` | Nome, código, área e duas populações de 2019 |
| `pop_idade.csv` | População por município e faixa etária |
| `pop_sexo.csv` | População por município e sexo |
| `mmr.csv` | Cobertura administrativa por município, ano e dose |
| `pib.csv` | PIB por habitante de 2016 |
| `malha.json` | Anéis dos polígonos municipais, coordenadas originais |
| `fontes.json` | Identificação e hashes dos DBC e CSV recebidos |
| `manifesto_processamento.json` | Integridade, versões e definição do recorte |

## Recorte epidemiológico e limites

O notebook seleciona `SG_UF=35`, `CLASSI_FIN=1` e ano de `DT_INICIO_=2019`. Resultado: 18.025 registros, incluindo 55 notificados em 2020. Residência não é local provável de infecção. `DT_INICIO_` é exantema; `DT_NOTIFIC` é notificação. `CS_VACINA` é antecedente vacinal, enquanto `CS_VACINAL` descreve bloqueio vacinal.

Não há imputação de datas nem exclusão automática de registros apenas semelhantes. Os registros com atrasos extremos são examinados em sensibilidade, sem modificar a coorte principal. Não há identificador individual suficiente para afirmar ausência absoluta de duplicação de pessoas.

A cobertura recebida contém 1.380 valores >100%, inclusive extremos de 440%. É cobertura administrativa infantil, não proporção de pessoas imunes nem cobertura de adultos. O CSV é mantido sem truncamento; restrições a 0–100% são análises de sensibilidade. A normalização anterior mapeou 021 para D1 e 098 para D2, conforme a proveniência recebida; este projeto não repete a auditoria das partições históricas do espelho.

O PIB por habitante recebido corresponde a PIB total dividido pela população (com conversão da unidade monetária na etapa anterior). O script atual preserva o CSV, sem recalculá-lo dos JSON. PIB não equivale à renda domiciliar ou à desigualdade.

As associações municipais são exploratórias e não causais. O notebook não estima efetividade vacinal, cadeias de transmissão ou efeito de campanhas. Os arquivos representam as versões recebidas; nenhuma atualização automática é feita.

## Extensão de machine learning

Nenhuma nova fonte de dados foi adicionada. `scripts/modelagem.py` deriva de `data/processed` uma linha por município: contagem de casos, exposição populacional, log de densidade e PIB, frações etárias, médias e mudanças vacinais de 2016–2018 e indicador de cobertura >100%. O município não recebe informação de desfecho de outro município como preditor. Coordenadas aproximadas são usadas exclusivamente para definir as partições espaciais.

A demografia de 2019 é uma série revisada recuperada posteriormente: não é uma fotografia da informação disponível antes da epidemia. A análise é de transferência espacial retrospectiva, não de previsão temporal prospectiva.

### Resultados derivados em `results/ml`

| Arquivo | Conteúdo |
|---|---|
| `base_municipal_ml.csv` | 645 municípios, atributos, alvo, exposição e rótulos das partições |
| `predicoes.csv` | 14.835 previsões externas: sete modelos em três partições e dois modelos na sensibilidade vacinal |
| `metricas.csv` | Métricas agregadas calculadas das previsões externas |
| `folds.csv` | Métricas por bloco externo, tamanhos de treino/teste e parâmetro selecionado |
| `ajustes.csv` | Critérios de seleção dos hiperparâmetros na validação interna |
| `permutacao.csv` | Diagnóstico por permutação de grupos no teste espacial |
| `dispersao.csv` | Diagnóstico de Pearson no treino do Poisson completo |
| `metricas_sem_capital.csv` | Mesmas previsões, excluindo a capital somente da avaliação |
| `execucao.json` | Versões, grades, protocolo e hashes de entradas, script e resultados |

A divisão principal usa cinco agrupamentos geográficos (semente 42), com ajuste interno nos blocos restantes. Sensibilidades: faixas de longitude, divisão aleatória e coberturas limitadas a 100%. Nenhuma variável-alvo é usada para definir as regiões. Não há faixa de exclusão nas fronteiras; independência espacial completa não é garantida.

Documentação dos algoritmos: [scikit-learn: Poisson e exposição](https://scikit-learn.org/stable/auto_examples/linear_model/plot_tweedie_regression_insurance_claims.html), [gradient boosting](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html), [statsmodels: modelos lineares generalizados](https://www.statsmodels.org/stable/glm.html). Os modelos e hiperparâmetros estão detalhados na seção 12 do notebook e no manifesto de execução.

## Clustering municipal — seção 13

Não foram adicionadas fontes externas. Os mesmos 645 municípios são descritos em quatro quadrantes (D2 média original versus incidência) e agrupados a partir de sete atributos: médias de D1/D2, diferenças 2018−2016, log(1+incidência), log da densidade e proporção de crianças de 0–4 anos. As coberturas anuais são limitadas a 100% na solução principal antes da agregação; a escolha é testada contra alternativas, sem alterar os arquivos raw.

Padronização por variável e ponderação por bloco: quatro atributos vacinais ×0,5; intensidade ×1; dois demográficos ×1/√2. Cada município tem peso igual. K-means, semente 42, 30 inicializações, k=2–6; seleção por silhueta com mínimo de 20 municípios por grupo. A PCA é somente uma projeção visual, não a entrada do algoritmo. Os números dos grupos são rótulos arbitrários ordenados pela incidência mediana.

A estabilidade usa 40 subamostras sem reposição de 80% das observações; todas as transformações são reajustadas. ARI compara partições projetadas sobre os 645 municípios; não é validação preditiva. Reescolhemos k em cada subamostra para mostrar sua incerteza. Um controle exploratório de 20 embaralhamentos independentes das colunas refaz a busca de k com a mesma restrição de tamanho; ele não equivale a teste formal de populações naturais.

| Arquivo em `results/clustering` | Conteúdo |
|---|---|
| `municipios.csv` | Atributos, quadrante, grupo principal, solução k=2, concordância de reamostragem e coordenadas PCA |
| `perfis.csv` | Tamanho, casos, incidências, vacinação e contexto por grupo |
| `perfil_casos.csv` | Idade, calendário e hospitalizações dos casos; atributos não usados para formar grupos |
| `selecao_k.csv` | Silhueta e tamanhos das soluções k=2–6 |
| `estabilidade.csv` | ARI com k fixo e k reescolhido em cada subamostra |
| `jaccard.csv` | Sobreposição dos grupos após correspondência ótima dos rótulos |
| `sensibilidades.csv` | Concordância com tratamentos alternativos, Ward e agrupamentos univariados |
| `grupos_alternativos.csv` | Rótulos por município nos cenários alternativos; IDs não alinhados entre cenários |
| `controle_permutado.csv` | Melhor silhueta por repetição com colunas embaralhadas |
| `grupos_quadrantes.csv` | Tabela cruzada entre perfis multivariados e os quadrantes simples |
| `centros_padronizados.csv` | Médias no espaço padronizado e ponderado |
| `execucao.json` | Assinaturas das fontes processadas e scripts, configuração, thresholds, PCA e hashes das saídas |

Referência de métodos: [scikit-learn — clustering, silhueta e ARI](https://scikit-learn.org/stable/modules/clustering.html). A interpretação substantiva depende da qualidade administrativa das coberturas e da inclusão da incidência na definição dos grupos. Diferenças de incidência entre grupos não são evidência independente de efeito vacinal.
