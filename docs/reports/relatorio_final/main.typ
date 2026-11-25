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
  doença em 2016, com 18.109 casos confirmados em 307 municípios. Este trabalho integra bases oficiais de
  vigilância epidemiológica, cobertura vacinal, internações hospitalares e indicadores socioeconômicos em um
  painel de 645 municípios paulistas entre 2007 e 2026 para caracterizar o surto, modelar o risco municipal e
  projetar o acúmulo de crianças sem as doses de rotina da vacina tríplice viral para o triênio 2026\u{2013}2027.
  Os resultados mostram que a cobertura vacinal infantil recente tem baixo poder preditivo sobre a distribuição
  espacial dos casos \u{2014} o porte populacional do município domina essa distribuição \u{2014}, enquanto a
  geração de nascimento do indivíduo (dose única na rotina entre 1989 e 2001, ausência de dose antes de 2018)
  explica uma parcela relevante do risco individual. A combinação de lugar e geração eleva a deviance explicada
  de 13,9% (só lugar) para 33,9%, e um classificador treinado nos dados de 2019\u{2013}2020 valida-se fora da
  amostra nos anos de 2021 a 2026. Sob a cobertura observada em 2023\u{2013}2025, a projeção indica
  aproximadamente 40 mil crianças sem a primeira dose e 148 mil sem a segunda dose entre 2026 e 2027 no estado.

  #palavras-chave[sarampo][cobertura vacinal][epidemiologia espacial][ciência de dados][saúde pública]
]

#outline()

// --- Elementos textuais ---

= Introdução

== Contexto e definição do problema

Nos últimos anos, o Brasil enfrentou uma queda relevante nas taxas de cobertura vacinal infantil, acompanhada
pela reintrodução do vírus do sarampo e pela ocorrência de surtos expressivos a partir de 2018. O Estado de São
Paulo foi o mais afetado do país: em 2019 registrou 18.109 casos confirmados de sarampo, distribuídos em 307 dos
seus 645 municípios, com incidência estadual de 39,97 por 100 mil habitantes e pico semanal entre 11 e 17 de
agosto daquele ano (1.356 casos em uma única semana). O município da capital concentrou 52,0% dos registros, mas
a maior incidência relativa ocorreu em Francisco Morato (372,3 por 100 mil). A faixa de 20 a 29 anos respondeu
pelo maior volume de casos (31,0%), enquanto crianças com menos de um ano tiveram a maior incidência
(557,4 por 100 mil); houve 2.256 hospitalizações e 18 óbitos no período.

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
Informação de Agravos de Notificação, com séries de 2007 a 2026 filtradas para o Estado de São Paulo (94.429
notificações, de um total nacional de 257.378) @sinan2026; os painéis de cobertura vacinal infantil do Programa
Nacional de Imunizações, combinando a série histórica até 2022 com os painéis mais recentes do Ministério da
Saúde (2023 em diante) @infoms2026; o Sistema de Informações Hospitalares do SUS, usado tanto para o período
corrente quanto para a reconstrução da epidemia de 1997\u{2013}1998 a partir de arquivos originais daquele
período @sihsus2026; e estimativas populacionais, Censo Demográfico 2022, Produto Interno Bruto municipal e a
hierarquia urbana das Regiões de Influência das Cidades do Instituto Brasileiro de Geografia e Estatística
@ibge2026. Fontes governamentais abertas desse tipo não possuem, em geral, um DOI próprio; a citação de DOI
exigida para este trabalho recai, portanto, sobre o pacote que os próprios autores produzem a partir delas: o
conjunto formado por este relatório e pelos dados municipais consolidados, depositado no Zenodo e associado à
comunidade *Big Data Analytics Research Group of Escola Politécnica da Universidade de São Paulo*, com o DOI
#link("https://doi.org/10.5281/zenodo.2451851")[10.5281/zenodo.2451851] @zenododeposito.

== Reprodutibilidade e repositório de código

O código-fonte completo do projeto está hospedado publicamente no GitHub, em
#raw("github.com/erwan-dlt/sao-paulo-sarampo"). A reprodutibilidade foi garantida por quatro práticas adotadas de
forma sistemática ao longo do desenvolvimento: (i) uso exclusivo de bases públicas, sem dependência de
credenciais de acesso restrito; (ii) centralização, em um único módulo, das decisões de modelagem comuns a todas
as análises \u{2014} definição de caso confirmado, janela de referência da cobertura vacinal pré-surto, esquema
de validação espacial \u{2014}, de modo a evitar divergência de critérios entre as diferentes etapas; (iii) um
manifesto de verificação de integridade por hash criptográfico sobre cada tabela derivada, conferido a cada
execução; e (iv) uma checagem automática de consistência que interrompe o processamento caso o total de casos
confirmados recalculado deixe de ser 18.109, valor também conferido contra o indicador oficial publicado pela
Rede Interagencial de Informações para a Saúde (18.113, diferença de 4 casos atribuível a critérios de
classificação levemente distintos entre as duas fontes).

== Ferramentas computacionais

Todo o pipeline de processamento, modelagem e geração de figuras foi implementado em Python 3.10, com bibliotecas
de manipulação tabular (`pandas`, `numpy`), de modelagem estatística (`scipy`, `statsmodels`, para regressão de
Poisson, binomial negativa e logística), de aprendizado de máquina (`scikit-learn`, para clustering por k-means e
validação cruzada), de geoprocessamento (`shapely`, sobre a malha municipal oficial do IBGE) e de visualização
(`matplotlib`). O relatório técnico subjacente a este documento foi produzido como um notebook Jupyter executado
de ponta a ponta, e o leitor dos arquivos de notificação do Ministério da Saúde foi implementado em Python puro,
sem dependências externas, para eliminar a necessidade de software proprietário na etapa de aquisição dos dados.

= Caracterização e preparação dos dados

== Unidade amostral e estrutura dos dados

Os dados foram organizados em três níveis complementares, todos relacionados pelo código oficial de seis dígitos
do município e, quando aplicável, pelo ano: um nível de notificação individual (94.429 registros de sarampo
notificados em São Paulo entre 2007 e 2026), um nível municipal estático (645 municípios) e um nível
município-ano (9.675 observações, 645 municípios por 15 anos) que concentra as séries de cobertura vacinal,
população e indicadores socioeconômicos usadas na modelagem agregada. A @fig-funil ilustra o recorte sucessivo
que leva do total nacional de notificações até a contagem de 18.109 casos de 2019 usada neste trabalho.

#ajustada(rotulo: <fig-funil>, caption: [Do arquivo nacional de notificações ao total de casos de 2019 em São
  Paulo])[
  #image("figuras/fig01_funil.png", width: 100%)
  #fonte[Elaboração própria.]
]

== Definição de caso e sensibilidade da contagem

A definição de "caso de 2019" depende de uma escolha metodológica sobre qual data do calendário do paciente
representa o início do quadro \u{2014} decisão que, por si só, pode mudar a contagem final em centenas de casos,
dado que notificações tardias ou com datas registradas incorretamente deslocam casos entre anos-calendário. Após
auditoria de 90 registros com datas inconsistentes (ano de exantema divergente dos primeiros sintomas ou da
notificação em mais de um ano), a contagem de 2019 variou entre 18.025 (critério que usa apenas a data do
exantema) e 18.109 (critério adotado, que usa a data do exantema com complementação pelos primeiros sintomas
quando a primeira está ausente ou implausível), ambos próximos do indicador oficial de 18.113 publicado pela
Rede Interagencial de Informações para a Saúde (@fig-regra-data). A diferença entre os três números é pequena o
suficiente (0,5% do total) para não alterar nenhuma conclusão deste trabalho, mas grande o bastante para merecer
registro explícito do critério adotado.

#ajustada(rotulo: <fig-regra-data>, caption: [Sensibilidade da contagem de casos de 2019 à definição da data do
  caso])[
  #image("figuras/fig02_regra_data.png", width: 100%)
  #fonte[Elaboração própria.]
]

== Limitações dos dados

Duas fragilidades nas séries oficiais de insumo merecem destaque, por afetarem diretamente a interpretação dos
resultados de cobertura vacinal. Em primeiro lugar, uma mudança de sistema de apuração da cobertura vacinal em
2023 produz um salto artificial na série nacional, de 78% para 94% entre um ano e o seguinte (@fig-cobertura,
painel direito) \u{2014} descontinuidade que não reflete uma melhora real da vacinação e que precisa ser tratada
como quebra de série, não como tendência. Em paralelo, valores de cobertura acima de 100% são comuns na série
municipal (presentes em cerca de 45% dos município-ano para a primeira dose), artefato típico de estimativas
populacionais desatualizadas no denominador quando o numerador de doses aplicadas é relativamente estável
(@fig-cobertura, painel esquerdo); esses valores foram mantidos e sinalizados, em vez de descartados, para não
introduzir viés de seleção. Em segundo lugar, a série de população do IBGE sofre um degrau metodológico entre as
estimativas anuais pré-Censo e o resultado do Censo Demográfico de 2022, que reduziu a população estadual
estimada em 2,2 milhões de habitantes em um único ano \u{2014} descontinuidade contornada neste trabalho pelo uso
da série de população revisada do Ministério da Saúde, mais estável ao longo de todo o período (@fig-populacao).
Por fim, os registros de internação hospitalar do SUS não equivalem a casos confirmados de sarampo: em 2019, por
exemplo, há 582 internações classificadas sob o código de internação por sarampo, contra 2.256 hospitalizações
contabilizadas a partir da própria base de vigilância epidemiológica, que registra a internação como um atributo
do caso notificado, não apenas pelo código de procedimento hospitalar.

#ajustada(rotulo: <fig-cobertura>, caption: [Cobertura vacinal municipal acima de 100% e salto na série estadual
  após a mudança de sistema de apuração em 2023])[
  #image("figuras/fig04_cobertura.png", width: 100%)
  #fonte[Elaboração própria.]
]

#ajustada(rotulo: <fig-populacao>, caption: [Degrau na série de população do IBGE em 2022 e a série revisada
  usada neste trabalho])[
  #image("figuras/fig03_populacao.png", width: 100%)
  #fonte[Elaboração própria.]
]

== Panorama descritivo do surto

Antes de qualquer modelagem, o comportamento descritivo dos dados já revela os três padrões que estruturam o
restante deste trabalho: a cobertura vacinal estadual oscilou por anos abaixo da meta de 95% mesmo antes do
surto, os casos de 2019\u{2013}2020 concentraram-se fortemente em municípios de maior porte populacional, e o
perfil etário dos casos mudou de forma marcante entre o início do surto e os anos mais recentes, com participação
crescente de crianças pequenas (@fig-eda).

#ajustada(rotulo: <fig-eda>, caption: [Cobertura vacinal e casos por ano, concentração por porte do município e
  perfil etário dos casos em cada período])[
  #image("figuras/fig06_eda_periodo.png", width: 100%)
  #fonte[Elaboração própria.]
]

= Modelagem e análise dos dados

A modelagem foi conduzida em seis frentes complementares, cada uma respondendo a uma pergunta distinta sobre o
surto \u{2014} onde ele ocorreu, em que municípios ele se concentrou, quem adoeceu e se o padrão observado é
estável o suficiente para sustentar previsão.

== Modelo de contagem municipal

Um modelo de contagem de casos por município foi ajustado em três especificações (Poisson, binomial negativa e
gradient boosting), validado espacialmente por exclusão sucessiva de uma Região Regional de Saúde por vez \u{2014}
ou seja, o modelo nunca é avaliado nos mesmos municípios usados para treiná-lo. O modelo binomial negativo
completo obteve o menor desvio médio (aproximadamente 13,3, uma redução de cerca de 60% frente a um modelo de
referência apenas populacional, cujo desvio foi 33,6), com coeficiente de determinação aproximado de 0,19 e soma
das previsões equivalente a 85% do total observado. Notavelmente, acrescentar a cobertura vacinal ao modelo
*piora* o ajuste (desvio +9% na especificação linear e +16% no boosting), indicando que, nessa escala de
agregação, a cobertura recente carrega pouca informação adicional além da que já está contida na estrutura
populacional e geográfica do município.

== Perfis municipais por agrupamento

Os 645 municípios foram agrupados por k-means em sete variáveis padronizadas, combinando cobertura vacinal,
intensidade do surto e indicadores demográficos. A seleção de três grupos (índice de silhueta de 0,325 contra
0,320 para dois grupos, diferença pequena o suficiente para ser testada por sensibilidade) revelou um grupo de 60
municípios com cobertura menor e crescente ao longo do período, um grupo de 321 municípios com cobertura maior e
baixa incidência, e um grupo de 264 municípios de maior densidade populacional que concentrou 18.017 dos 18.109
casos (@fig-clusters). A estabilidade dessa separação foi confirmada por subamostragem repetida, com índice de
Rand ajustado médio de aproximadamente 0,983 em 40 repetições.

#ajustada(rotulo: <fig-clusters>, caption: [Perfis municipais por densidade populacional, cobertura vacinal e
  casos de 2019])[
  #image("figuras/fig07_clusters.png", width: 100%)
  #fonte[Elaboração própria.]
]

== Classificador de risco municipal

Um classificador binário \u{2014} o município registrou ao menos um caso? \u{2014} foi treinado com regressão
logística e boosting sobre quatro definições possíveis do alvo, validado pela mesma exclusão espacial por Região
Regional de Saúde. A população municipal isolada já discrimina bem o risco (área sob a curva ROC de 0,868);
acrescentar cobertura vacinal e variáveis estruturais eleva essa métrica apenas marginalmente, para um intervalo
de 0,864 a 0,920 conforme a definição do alvo, e a razão de chances associada à cobertura da primeira dose
permanece próxima da neutralidade estatística (1,00; intervalo de confiança de 95% entre 0,80 e 1,27) \u{2014}
reforçando que o porte populacional, e não a cobertura vacinal recente, é o preditor dominante de onde o surto se
instalou.

== Geração de nascimento e sua combinação com o lugar

Recompondo a incidência por ano de nascimento, observou-se que indivíduos nascidos entre 1989 e 2001 \u{2014}
período em que a rotina de vacinação previa apenas uma dose \u{2014} tiveram incidência de 93 casos por 100 mil e
responderam por 44% de todos os casos confirmados; crianças nascidas em 2018\u{2013}2019, ainda no início do
calendário vacinal, tiveram incidência de 425 por 100 mil (26% dos casos); já os nascidos entre 2002 e 2013,
já cobertos pelo esquema de duas doses, tiveram incidência de apenas 16 por 100 mil (@fig-coortes). Quando lugar e
geração são combinados em um único modelo, no nível de município por coorte de nascimento, a deviance explicada
sobe de 13,9% (considerando apenas o lugar) para 33,9% (lugar e geração combinados), e a área sob a curva ROC para
a previsão de concentração de casos em um grupo município-geração sobe de 0,887 para 0,920 quando a geração é
incorporada \u{2014} evidência de que o risco individual acumulado ao longo da vida explica uma parcela do
problema que a cobertura vacinal do ano corrente, isoladamente, não captura.

#ajustada(rotulo: <fig-coortes>, caption: [Incidência de sarampo por ano de nascimento e cobertura vacinal
  histórica correspondente])[
  #image("figuras/fig08_coortes.png", width: 100%)
  #fonte[Elaboração própria.]
]

== Persistência histórica: a epidemia de 1997

Para testar se a vulnerabilidade municipal é um traço estrutural ou um efeito específico do surto de 2019, os
registros de internação hospitalar da epidemia de sarampo de 1997\u{2013}1998 foram reconstruídos a partir de
arquivos originais daquele período. Dos 72 municípios que registraram ao menos uma internação em 1997\u{2013}1998,
85% voltaram a ter caso confirmado em 2019\u{2013}2020, contra 45% dos demais municípios (razão de chances de
1,43; intervalo de confiança de 95% entre 1,13 e 1,81, para incidência igual ou superior a 20 por 100 mil em 2019)
\u{2014} indício de que a vulnerabilidade de um município ao sarampo persiste por mais de duas décadas, ainda que
esse histórico não melhore, isoladamente, a previsão binária de "teve caso" (@fig-historico).

#ajustada(rotulo: <fig-historico>, caption: [Municípios atingidos pela epidemia de 1997 e pelo surto de 2019,
  em mapas comparáveis])[
  #image("figuras/fig09_historico1997.png", width: 100%)
  #fonte[Elaboração própria.]
]

== Validação fora da amostra e projeção para 2026\u{2013}2027

Como teste adicional de robustez, o classificador treinado exclusivamente nos dados de 2019\u{2013}2020 foi
aplicado, sem reajuste, aos anos de 2021 a 2026: nos poucos municípios que voltaram a registrar casos em 2026,
todos ficaram entre as sete primeiras posições do ranking de risco produzido pelo modelo \u{2014} uma validação
fora da amostra e fora do próprio período de treinamento, mais exigente do que a validação espacial usada nas
demais etapas, e evidência de que o modelo captura uma característica estrutural do município, não um padrão
específico do surto que o originou. Partindo dos cenários de cobertura observados entre 2023 e 2025 (primeira
dose em 93,7%, 99,4% e 94,4%; segunda dose em 80,3%, 88,1% e 84,8%, respectivamente), a projeção para 2026 e 2027
indica que, mantida a tendência atual, cerca de 40 mil crianças ficarão sem a primeira dose e 148 mil sem a
segunda dose da tríplice viral no período (375 mil acumuladas sem a segunda dose desde 2023); caso todas as
Regiões Regionais de Saúde atinjam a meta de 95% de cobertura, esses números caem para 34 mil e 47 mil,
respectivamente (@fig-projecao).

#ajustada(rotulo: <fig-projecao>, caption: [Cenários de cobertura da tríplice viral e número de crianças
  projetadas sem cada dose entre 2026 e 2027])[
  #image("figuras/fig10_projecao.png", width: 100%)
  #fonte[Elaboração própria.]
]

= Apresentação e discussão dos resultados

Os resultados convergem para uma conclusão central e, à primeira vista, contraintuitiva: a cobertura vacinal
infantil *recente* tem baixo valor preditivo sobre onde e quantos casos de sarampo ocorreram em São Paulo em
2019\u{2013}2020. No modelo de contagem municipal, no classificador binário e no agrupamento por perfis, o porte
populacional e a densidade do município dominam a variação observada, enquanto a cobertura vacinal contemporânea
contribui pouco ou, em alguns casos, piora o ajuste. Isso não significa que a vacinação seja irrelevante:
significa que o risco individual está associado a um histórico vacinal acumulado por geração, não à cobertura do
ano corrente. A combinação de lugar e geração quase triplica a deviance explicada em relação ao lugar isolado
(de 13,9% para 33,9%), mostrando que os indivíduos nascidos no período de dose única (1989\u{2013}2001) e os
bebês ainda não totalmente vacinados (2018\u{2013}2019) concentram o risco de forma independente de onde moram.

A difusão espacial do surto ao longo do tempo mostra uma expansão a partir de focos concentrados na Região
Metropolitana de São Paulo em 2019, seguida de uma retração progressiva do número de municípios atingidos já em
2020 e de uma presença residual, restrita a poucos municípios, entre 2021 e 2026 (@fig-mapas-fases) \u{2014}
padrão de concentração inicial compatível com o descrito por @reis2024 para o Rio de Janeiro, embora a escala
municipal estadual aqui usada não alcance a mesma granularidade intraurbana daquele estudo. A robustez do achado
central é reforçada por duas evidências independentes: a persistência histórica entre a epidemia de 1997 e o
surto de 2019 (@fig-historico), e a validação de um classificador treinado apenas com dados de 2019\u{2013}2020
contra anos completamente fora desse período, incluindo 2026.

#ajustada(rotulo: <fig-mapas-fases>, caption: [Distribuição municipal dos casos confirmados em cada período,
  de 2007 a 2026])[
  #image("figuras/fig05_mapas_fases.png", width: 100%)
  #fonte[Elaboração própria.]
]

Esses achados respondem, com ressalvas, às hipóteses que motivaram o trabalho: a hipótese de que a baixa
cobertura vacinal *municipal corrente* explicaria diretamente a concentração de casos não se sustenta nos
modelos agregados, mas a hipótese ligada ao porte e à conectividade urbana é corroborada pela dominância do
tamanho populacional como preditor. Já a projeção de suscetibilidade acumulada para 2026\u{2013}2027 (entre 40
mil e 148 mil crianças sem a primeira e a segunda dose, respectivamente, sob a tendência atual) é consistente com
o quadro nacional de queda de cobertura descrito por @loureiro2024 e @santosluna2025, e com a lacuna em relação à
meta de 95% observada mesmo fora de São Paulo por @maciel2024, reforçando que o problema de suscetibilidade
acumulada não é uma particularidade paulista, mas um padrão nacional do qual São Paulo é um caso bem documentado.

= Conclusões

Este trabalho caracterizou o surto de sarampo de 2019 em São Paulo (18.109 casos confirmados em 307 municípios),
modelou o risco municipal por múltiplas abordagens complementares e projetou a suscetibilidade vacinal infantil
para 2026\u{2013}2027. A conclusão mais relevante para a formulação de políticas públicas é que o risco de
reemergência do sarampo não deve ser monitorado apenas pela cobertura vacinal do ano corrente em cada município
\u{2014} indicador que, isoladamente, tem baixo poder de previsão espacial \u{2014}, mas sim pelo acúmulo de
suscetíveis por geração de nascimento, fator que este trabalho mostrou ter o maior poder explicativo individual e
cuja combinação com o porte do município quase triplica a capacidade explicativa dos modelos testados. A
persistência do padrão de vulnerabilidade entre a epidemia de 1997 e o surto de 2019, validada adicionalmente por
um teste fora da amostra e fora do período de treinamento até os dados de 2026, sugere que esse resultado não é
um artefato do surto específico analisado, mas uma característica estrutural dos municípios paulistas. A
projeção de que, mantida a tendência atual de cobertura, entre 40 mil e 148 mil crianças ficarão sem a primeira e
a segunda dose da tríplice viral entre 2026 e 2027 indica uma janela de oportunidade concreta para ações
preventivas direcionadas, sobretudo nas regiões onde a projeção concentra o maior número de crianças não
vacinadas. Como trabalho futuro, destaca-se a necessidade de dados de cobertura vacinal em nível mais fino que o
municipal (por exemplo, por bairro ou unidade básica de saúde) para testar se o padrão de difusão intraurbana
identificado por @reis2024 no Rio de Janeiro também se manifesta dentro dos municípios paulistas de maior porte.

#bibliography("refs.bib")
