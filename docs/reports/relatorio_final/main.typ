#import "@preview/abntly:0.1.1": *

#show: trabalho-academico.with(
  dados: config-dados(
    titulo: [Sarampo no Estado de São Paulo],
    subtitulo: [caracterização do surto de 2019, modelagem espaço-temporal e projeção da suscetibilidade vacinal para 2026\u{2013}2027],
    autor: [Thiago Kei Shimasaki \
      Carlos Eduardo Santos Lima \
      Nicolas de Oliveira Honda \
      Erwan Pierre Didelot],
    instituicao: [Escola Politécnica da Universidade de São Paulo],
    programa: [PTC3567 \u{2014} Ciência dos Dados em Automação e Engenharia],
    area: [Ciência de dados aplicada à saúde pública],
    local: [São Paulo],
    ano: 2026,
  ),
)

// --- Elementos pré-textuais ---
#capa()

#resumo[
  Entre 2019 e 2020, o Estado de São Paulo registrou o maior surto de sarampo do país desde a eliminação da
  doença em 2016, com 18.109 casos confirmados em 307 municípios. Este trabalho integra bases oficiais do SINAN,
  do Ministério da Saúde (PNI/InfoMS e SIH/SUS) e do IBGE em um painel de 645 municípios paulistas entre 2007 e
  2026 para caracterizar o surto, modelar o risco municipal e projetar o acúmulo de crianças sem as doses de
  rotina da vacina tríplice viral para o triênio 2026\u{2013}2027. Os resultados mostram que a cobertura vacinal
  infantil recente tem baixo poder preditivo sobre a distribuição espacial dos casos \u{2014} o porte populacional
  do município domina essa distribuição \u{2014}, enquanto a geração de nascimento do indivíduo (dose única na
  rotina entre 1989 e 2001, ausência de dose antes de 2018) explica uma parcela relevante do risco individual.
  A combinação de lugar e geração eleva a deviance explicada de 13,9% (só lugar) para 33,9%, e um classificador
  treinado nos dados de 2019\u{2013}2020 valida-se fora da amostra nos anos de 2021 a 2026. Sob a cobertura
  observada em 2023\u{2013}2025, a projeção indica aproximadamente 40 mil crianças sem a primeira dose e 148 mil
  sem a segunda dose entre 2026 e 2027 no estado.

  #palavras-chave[sarampo][cobertura vacinal][epidemiologia espacial][ciência de dados][saúde pública]
]

#outline()

// --- Elementos textuais ---

= Introdução

== Contexto e definição do problema

Nos últimos anos, o Brasil enfrentou uma queda relevante nas taxas de cobertura vacinal infantil, acompanhada
pela reintrodução do vírus do sarampo e pela ocorrência de surtos expressivos a partir de 2018. O Estado de São
Paulo foi o mais afetado: em 2019 registrou 18.109 casos confirmados de sarampo (critério `CLASSI_FIN = 1`, UF de
notificação igual a São Paulo) distribuídos em 307 dos seus 645 municípios, com incidência estadual de
39,97 por 100 mil habitantes e pico semanal entre 11 e 17 de agosto daquele ano (1.356 casos na semana).
O município da capital concentrou 52,0% dos registros, mas a maior incidência relativa ocorreu em Francisco
Morato (372,3 por 100 mil). A faixa de 20 a 29 anos respondeu pelo maior volume de casos (31,0%), enquanto
crianças com menos de um ano tiveram a maior incidência (557,4 por 100 mil); houve 2.256 hospitalizações e 18
óbitos no período.

Embora a incidência tenha recuado a partir de 2022 e o Brasil tenha recuperado, em novembro de 2024, o
certificado de eliminação do sarampo concedido pela Organização Mundial da Saúde, a manutenção de bolsões
municipais com cobertura vacinal abaixo da meta de 95% e o acúmulo de crianças não vacinadas ao longo dos anos
representam um risco permanente de reemergência epidemiológica. O problema central deste trabalho é, portanto,
duplo: (i) entender quais fatores municipais e individuais explicam onde e em quem o sarampo se concentrou em
2019\u{2013}2020; e (ii) projetar, a partir das tendências recentes de cobertura, o tamanho da população infantil
suscetível nos próximos anos (2026\u{2013}2027), de modo a subsidiar ações preventivas de saúde pública.

== Trabalhos relacionados

Cinco estudos publicados na base SciELO entre 2024 e 2025 embasaram a formulação das hipóteses e da metodologia
deste trabalho. @loureiro2024 analisam o efeito das campanhas de vacinação sobre internações e mortalidade por
sarampo no Brasil entre 2013 e 2022, mostrando que a cobertura vacinal caiu de forma acentuada após 2019,
período em que as internações e óbitos atingiram os maiores valores da década \u{2014} achado consistente com o
recorte temporal do surto paulista aqui estudado. @reis2024 oferecem a referência metodológica mais direta para a
análise espacial deste trabalho: um estudo ecológico intraurbano no Rio de Janeiro (2007\u{2013}2021, 774 casos)
que descreve difusão hierárquica por relocação, da região da Grande Tijuca para zonas Oeste e Sul, e identifica
oito clusters de alto risco \u{2014} padrão de difusão espacial análogo ao que se buscou caracterizar entre os
645 municípios paulistas. @silva2024ape correlacionam, em nível nacional, a queda de cobertura vacinal com o
aumento de internações hospitalares por sarampo entre 2011 e 2020, destacando 2018 como o ano de maior
descolamento entre as duas séries. Como estudos complementares, @santosluna2025 revisam sistematicamente a
influência da pandemia de covid-19 sobre a cobertura vacinal do sarampo, e @maciel2024 quantificam, por meio de
inquérito domiciliar em coorte de nascidos em 2017\u{2013}2018, uma cobertura de 79,3% (IC95% 76,5\u{2013}81,8) e
evasão de 10,6% da tríplice viral/MMR em capitais e municípios do interior do Nordeste \u{2014} evidência direta
de que a meta de 95% não vem sendo atingida mesmo fora do estado aqui estudado.

= Estratégias de gestão dos dados

== Fontes de dados e citação

Todos os dados utilizados são públicos, secundários e provenientes de órgãos oficiais brasileiros: o Sistema de
Informação de Agravos de Notificação \u{2014} SINAN, séries de 2007 a 2026 filtradas para o Estado de São Paulo
(94.429 notificações de um total nacional de 257.378) @sinan2026; os painéis de cobertura vacinal infantil do
Programa Nacional de Imunizações, na série histórica do TABNET (até 2022) e nos painéis InfoMS (2023 em diante)
@infoms2026; o Sistema de Informações Hospitalares do SUS, usado tanto para o período corrente quanto para a
reconstrução da epidemia de 1997\u{2013}1998 a partir dos arquivos originais de 1996\u{2013}1998 @sihsus2026; e
estimativas populacionais, Censo Demográfico 2022, Produto Interno Bruto municipal e a hierarquia urbana das
Regiões de Influência das Cidades (REGIC 2018) do Instituto Brasileiro de Geografia e Estatística @ibge2026.
Fontes governamentais abertas desse tipo não possuem, em geral, um DOI próprio; a citação de DOI exigida para
este trabalho recai, portanto, sobre o pacote que os autores produzem a partir delas: o conjunto formado pelo
relatório, pelos dados processados e pelo código de processamento, depositado no Zenodo e associado à comunidade
*Big Data Analytics Research Group of Escola Politécnica da Universidade de São Paulo*, com o
DOI #raw("10.5281/zenodo.XXXXXXX") (a ser preenchido após a publicação do depósito) @zenododeposito.

== Reprodutibilidade e repositório de código

O código-fonte completo do projeto \u{2014} scripts de preparação de dados, modelagem, clustering e projeção, além
do notebook executado que constitui o relatório técnico detalhado \u{2014} está hospedado publicamente no
GitHub, em #raw("github.com/erwan-dlt/sao-paulo-sarampo") (branch `integracao`, que reúne a integração final dos
dois subgrupos do projeto). A reprodutibilidade é garantida por quatro mecanismos documentados no próprio
repositório: (i) uso exclusivo de bases públicas, sem dependência de credenciais; (ii) um módulo único
(`scripts/base.py`) que centraliza as decisões de modelagem comuns a todas as análises (definição de caso,
janela de cobertura pré-surto, esquema de validação espacial), evitando divergência entre scripts; (iii) um
manifesto de hashes SHA-256 (`data/processed/manifesto_processamento.json`) que verifica a integridade dos dados
derivados a cada execução; e (iv) uma verificação automática de consistência \u{2014} `scripts/prepare_data.py`
interrompe a execução caso o total de casos confirmados recalculado deixe de ser 18.109, e o resultado é também
conferido contra o total oficial da RIPSA (18.113, diferença de 4 casos documentada em `FONTES.md`).

== Ferramentas computacionais

Todo o pipeline foi implementado em Python 3.10, com `pandas` e `numpy` para manipulação tabular, `scipy` e
`statsmodels` para os modelos estatísticos (regressão de Poisson, binomial negativa e logística), `scikit-learn`
para clustering (k-means) e validação cruzada, `shapely` para operações geoespaciais sobre a malha municipal do
IBGE e `matplotlib` para as figuras. O relatório técnico foi produzido como um notebook Jupyter executado
(`sarampo_sp_2019.ipynb`), e o leitor de arquivos `.dbc` do DATASUS (`scripts/dbc.py`) foi implementado em Python
puro, sem dependências externas, para eliminar a necessidade de software proprietário na etapa de aquisição.

= Caracterização e preparação dos dados

== Unidade amostral e estrutura dos dados

Após a integração das bases dos dois subgrupos do projeto, os dados foram organizados em três tabelas
relacionadas pela chave `co_ibge` (código municipal do IBGE) e, quando aplicável, pelo ano: uma tabela de
notificações individuais do SINAN (94.429 linhas, uma por caso notificado em São Paulo entre 2007 e 2026), uma
tabela municipal estática (645 linhas, uma por município) e uma tabela município-ano (9.675 linhas, 645
municípios por 15 anos) que concentra as séries de cobertura vacinal, população e indicadores socioeconômicos
usadas na modelagem agregada.

== Limpeza e tratamento dos dados

O catálogo de integração e limpeza (`docs/integracao_e_limpeza.md`) documenta, problema a problema, as linhas
afetadas e o tratamento aplicado. Antes da integração final havia quatro versões divergentes da tabela municipal,
duas bases de casos e três malhas geográficas distintas produzidas pelos dois subgrupos; o processo de fusão
unificou essas fontes em um único pipeline, auditado por conferência linha a linha contra a tabela anterior e por
comparação do total de casos contra o valor oficial da RIPSA. Entre os tratamentos quantificados: 90 datas de
caso corrigidas, 19.102 idades decodificadas a partir de código, nenhuma duplicata exata, cobertura vacinal acima
de 100% mantida e sinalizada (presente em cerca de 45% dos município-ano para a primeira dose e 25% para a
segunda, artefato conhecido de estimativas populacionais desatualizadas no denominador), um erro de CID-9
corrigido nos dados de internação do SIH/SUS de 1997\u{2013}1998 (hérnia classificada como sarampo) e a estimativa
do PIB municipal de 2024, ainda não publicado pelo IBGE no momento da coleta.

== Limitações dos dados

`FONTES.md` documenta explicitamente as principais fragilidades: uma mudança de sistema de apuração da
cobertura vacinal entre o TABNET e o InfoMS produz um salto artificial na série nacional (de 78% para 94% entre
2022 e 2023) que não reflete uma melhora real; a série de população do IBGE tem um degrau metodológico entre as
estimativas pré-Censo e pós-Censo 2022; e os registros de internação do SIH/SUS não equivalem a casos confirmados
\u{2014} em 2019, por exemplo, há 582 internações por sarampo contra 2.256 hospitalizações contabilizadas a
partir da base de casos confirmados do SINAN, que inclui notificação de internação como variável própria.

= Modelagem e análise dos dados

A análise foi conduzida em etapas encadeadas, cada uma em um script próprio, descritas aqui na ordem em que
aparecem no notebook (seções 12 a 18) e complementadas por uma validação temporal mais recente.

== Modelo de contagem municipal (seção 12)

`scripts/modelagem.py` ajusta modelos de contagem (Poisson, binomial negativa e gradient boosting) para o número
de casos por município, com validação espacial por exclusão de uma Região Regional de Saúde (RRAS) por vez. O
modelo binomial negativo completo obteve o menor desvio de Poisson médio (\u{2248}13,3, uma redução de
aproximadamente 60% frente a um modelo de referência apenas populacional, cujo desvio foi 33,6), com
$R^2 \u{2248} 0,19$ e soma das previsões equivalente a 85% do total observado. Notavelmente, adicionar a cobertura
vacinal ao modelo *piora* o ajuste (desvio de Poisson +9% no modelo linear e +16% no boosting), indicando que,
nessa escala de agregação, a cobertura recente carrega pouca informação adicional sobre a estrutura populacional
e geográfica do município.

== Perfis municipais por clustering (seção 13)

`scripts/clustering.py` agrupa os 645 municípios por k-means em sete variáveis padronizadas (cobertura vacinal,
intensidade do surto e indicadores demográficos). A seleção de $k = 3$ grupos (silhueta 0,325 contra 0,320 para
$k=2$, diferença não conclusiva, testada com sensibilidade) revelou um grupo de 60 municípios com cobertura menor
e crescente, um grupo de 321 municípios com cobertura maior e baixa incidência, e um grupo de 264 municípios de
maior densidade populacional que concentrou 18.017 dos 18.109 casos. A estabilidade dos grupos foi confirmada por
subamostragem (índice de Rand ajustado médio \u{2248} 0,983 em 40 repetições).

== Classificador "o município teve caso?" (seção 14)

`scripts/modelo_alvos.py` testa quatro definições do alvo binário "o município registrou ao menos um caso" com
regressão logística e boosting, validados por exclusão de RRAS. A população isolada já atinge AUC = 0,868;
acrescentar cobertura vacinal e variáveis estruturais eleva a AUC marginalmente para 0,864\u{2013}0,920 segundo a
definição do alvo, mas a razão de chances da cobertura de primeira dose permanece próxima da neutralidade
($"OR" \u{2248} 1,00$, IC95% 0,80\u{2013}1,27) \u{2014} reforçando que o porte populacional, não a cobertura
recente, é o preditor dominante de onde o surto ocorreu.

== Geração de nascimento e lugar combinado com geração (seções 15 e 16)

`scripts/coortes_suscetibilidade.py` e `scripts/sinan_coortes.py` recompõem a incidência por ano de nascimento:
indivíduos nascidos entre 1989 e 2001 (período de dose única na rotina de vacinação) tiveram incidência de 93
casos por 100 mil e responderam por 44% de todos os casos confirmados; crianças nascidas em 2018\u{2013}2019
tiveram incidência de 425 por 100 mil (26% dos casos); já os nascidos entre 2002 e 2013, cobertos pelo esquema de
duas doses, tiveram incidência de apenas 16 por 100 mil. `scripts/modelo_lugar_geracao.py` combina lugar e
geração em nível de município × coorte: a deviance explicada passa de 13,9% (apenas lugar) para 33,9%
(lugar + geração), e a AUC do modelo para "duas ou mais notificações no grupo" sobe de 0,887 para 0,920 quando a
geração é incorporada.

== Epidemia de 1997 e padrão histórico (seção 17)

`scripts/historico_1997.py` reconstrói, a partir de arquivos originais do SIH/SUS de 1996\u{2013}1998, os 72
municípios que registraram internação por sarampo na epidemia de 1997. Desses, 85% voltaram a ter caso confirmado
em 2019\u{2013}2020, contra 45% dos demais municípios ($"OR" = 1,43$; IC95% 1,13\u{2013}1,81 para incidência
$\u{2265} 20$ por 100 mil) \u{2014} evidência de que a vulnerabilidade municipal ao sarampo é persistente ao
longo de décadas, embora o histórico não melhore o classificador binário de "teve caso".

== Validação fora da amostra e projeção 2026\u{2013}2027 (seção 18 e validação temporal)

Um teste de validação temporal (`scripts/teste_no_tempo.py`, incorporado ao projeto mais recentemente) aplica o
classificador treinado exclusivamente nos dados de 2019\u{2013}2020 aos anos de 2021 a 2026: nos poucos
municípios que voltaram a registrar casos em 2026, todos ficaram entre as sete primeiras posições do ranking de
risco gerado pelo modelo \u{2014} uma validação fora da amostra e fora do período de treino, mais rigorosa do que
a validação espacial por RRAS usada nas demais seções. Por fim, `scripts/projecao.py` projeta, a partir dos
cenários de cobertura InfoMS de 2023 a 2025 (primeira dose em 93,7%/99,4%/94,4%; segunda dose em
80,3%/88,1%/84,8%), o número de crianças que permanecerão sem cada dose da tríplice viral entre 2026 e 2027: cerca
de 40 mil sem a primeira dose e 148 mil sem a segunda (375 mil acumulados sem a segunda dose desde 2023), caindo
para 34 mil e 47 mil, respectivamente, caso todas as Regiões Regionais de Saúde atinjam a meta de 95%.

= Apresentação e discussão dos resultados

Os resultados convergem para uma conclusão central e, à primeira vista, contraintuitiva: a cobertura vacinal
infantil *recente* tem baixo valor preditivo sobre onde e quantos casos de sarampo ocorreram em São Paulo em
2019\u{2013}2020. Em todos os modelos agregados por município \u{2014} contagem (seção 12), classificação binária
(seção 14) e clustering (seção 13) \u{2014} o porte populacional e a densidade do município dominam a variação
observada, enquanto a cobertura vacinal contemporânea contribui pouco ou, em alguns casos, piora o ajuste. Isso
não significa que a vacinação seja irrelevante: significa que o risco individual está associado a um histórico
vacinal acumulado por geração, não à cobertura do ano corrente. A seção de coortes (15\u{2013}16) mostra esse
mecanismo de forma direta \u{2014} indivíduos nascidos no período de dose única (1989\u{2013}2001) e bebês ainda
não totalmente vacinados (2018\u{2013}2019) concentram o risco, e combinar lugar com geração quase triplica a
deviance explicada em relação ao lugar isolado (de 13,9% para 33,9%).

A robustez desse padrão é reforçada por duas evidências independentes. Primeiro, a persistência histórica: os
municípios vulneráveis à epidemia de 1997 têm, 22 anos depois, probabilidade quase duas vezes maior de registrar
incidência elevada em 2019, sugerindo que fatores estruturais municipais (e não apenas a cobertura do momento)
sustentam a vulnerabilidade ao longo do tempo. Segundo, a validação temporal fora da amostra: um classificador
treinado apenas com os dados de 2019\u{2013}2020 continua discriminando corretamente os municípios de risco em
anos completamente fora do período de treinamento (2021 a 2026), o que indica que o modelo captura uma
característica estrutural do município, e não um padrão específico do surto que o gerou.

Esses achados respondem, com ressalvas, às hipóteses formuladas: a hipótese de que a baixa cobertura vacinal
*municipal corrente* explicaria diretamente a concentração de casos não se sustenta nos modelos agregados, mas a
hipótese ligada à mobilidade/porte urbano é corroborada pela dominância do tamanho populacional, e o padrão de
difusão regional observado é qualitativamente compatível com o descrito por @reis2024 para o Rio de Janeiro,
ainda que a escala municipal estadual aqui usada não permita a mesma granularidade intraurbana daquele estudo. Já
a projeção de suscetibilidade acumulada para 2026\u{2013}2027 (cerca de 40 mil crianças sem primeira dose e 148
mil sem segunda dose sob a tendência atual) é consistente com o quadro nacional de queda de cobertura descrito por
@loureiro2024 e @santosluna2025, e com a lacuna de 95% observada mesmo fora de São Paulo por @maciel2024,
reforçando que o problema de suscetibilidade acumulada não é uma particularidade paulista, mas um padrão nacional
do qual São Paulo é um caso bem documentado.

= Conclusões

Este trabalho caracterizou o surto de sarampo de 2019 em São Paulo (18.109 casos confirmados em 307 municípios),
modelou o risco municipal por múltiplas abordagens complementares e projetou a suscetibilidade vacinal infantil
para 2026\u{2013}2027. A conclusão mais relevante para a formulação de políticas públicas é que o risco de
reemergência do sarampo não deve ser monitorado apenas pela cobertura vacinal do ano corrente em cada município
\u{2014} indicador que, isoladamente, tem baixo poder de previsão espacial \u{2014}, mas sim pelo acúmulo de
suscetíveis por geração de nascimento, que este trabalho mostrou ser o fator com maior poder explicativo
individual e cuja combinação com o porte do município quase triplica a capacidade explicativa dos modelos. A
persistência do padrão de vulnerabilidade entre a epidemia de 1997 e o surto de 2019, validada adicionalmente por
um teste fora da amostra e fora do período de treinamento até os dados de 2026, sugere que esse resultado não é
um artefato do surto específico analisado, mas uma característica estrutural dos municípios paulistas. A projeção
de que, mantida a tendência atual de cobertura, entre 40 mil e 148 mil crianças ficarão sem a primeira e a segunda
dose da tríplice viral entre 2026 e 2027 (respectivamente) indica uma janela de oportunidade concreta para ações
preventivas direcionadas, sobretudo nas Regiões Regionais de Saúde onde a projeção concentra o maior número de
crianças não vacinadas. Como trabalho futuro, destaca-se a necessidade de dados de cobertura vacinal em nível
mais fino que o municipal (por exemplo, por bairro ou unidade básica de saúde) para testar se o padrão de difusão
intraurbana identificado por @reis2024 no Rio de Janeiro também se manifesta dentro dos municípios paulistas de
maior porte.

#bibliography("refs.bib")
