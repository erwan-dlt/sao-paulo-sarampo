# Sarampo no estado de São Paulo — 2019

Projeto PTC3567. Caracterização e modelagem preditiva municipal de 18.025 notificações de sarampo de residentes paulistas com exantema em 2019, incluindo 55 notificadas em 2020. O relatório é exclusivamente o notebook `sarampo_sp_2019.ipynb`, na raiz.

## Organização

| Caminho | Conteúdo |
|---|---|
| `sarampo_sp_2019.ipynb` | Análise em português, tabelas e 28 figuras já executadas |
| `data/raw/` | Arquivos recebidos e fontes auxiliares preservados |
| `data/processed/` | Arquivos derivados lidos pelo notebook e manifesto de hashes |
| `scripts/prepare_data.py` | Reconstrução de todos os dados processados |
| `scripts/modelagem.py` | Modelos, validação aninhada, previsões externas e sensibilidades |
| `scripts/clustering.py` | Tipologia municipal, clustering e testes de estabilidade |
| `results/clustering/` | Rótulos, perfis, comparação com quadrantes e sensibilidades |
| `results/ml/` | Base municipal, métricas, previsões e auditoria da execução ML |
| `scripts/leitura_fontes.py` | Leitores das tabelas TabNet e da malha IBGE |
| `FONTES.md` | Proveniência, filtros, transformações e limitações |
| `requirements.txt` | Dependências do processamento e da análise |

## Instalar e executar com ambiente virtual (venv)

Use **Python 3.12 de 64 bits**, versão validada neste projeto. A indicação anterior de “3.11 ou superior” era ampla demais: versões mais novas podem não ter pacotes pré-compilados para as dependências fixadas. Descompacte o projeto inteiro e abra um terminal na pasta que contém este README e `requirements.txt`.

### Windows — PowerShell

Na primeira execução:

```powershell
# Verificar a versão do Python
py --version

# Criar e ativar o ambiente virtual
py -3.12 -m venv .venv312
.\.venv312\Scripts\Activate.ps1

# Instalar as dependências no ambiente virtual
python -m pip install -r requirements.txt

# Iniciar o JupyterLab
python -m jupyterlab
```

Se o PowerShell bloquear a ativação, não é necessário alterar a política de execução. Use diretamente o Python do ambiente:

```powershell
.\.venv312\Scripts\python.exe -m pip install -r requirements.txt
.\.venv312\Scripts\python.exe -m jupyterlab
```

Se `py -3.12` não encontrar o Python, instale Python 3.12 de 64 bits e tente novamente. Use `py -0p` para listar as versões instaladas. Se já estiver em outro ambiente, execute `deactivate` antes. A pasta `.venv312` permite manter separado um ambiente anterior incompatível.

### Linux / macOS

Na primeira execução:

```bash
# Verificar a versão do Python
python3 --version

# Criar e ativar o ambiente virtual
python3.12 -m venv .venv312
source .venv312/bin/activate

# Instalar as dependências e iniciar o JupyterLab
python -m pip install -r requirements.txt
python -m jupyterlab
```

No Ubuntu/Debian, se a criação do ambiente informar que `venv` ou `ensurepip` está indisponível, instale o suporte à versão de Python utilizada. Para o Python padrão do sistema:

```bash
sudo apt install python3-venv
```

Depois, execute novamente o comando de criação do ambiente.

### Abrir o notebook

O JupyterLab abre no navegador. Se isso não ocorrer, copie a URL local exibida no terminal.

1. Abra `sarampo_sp_2019.ipynb` na raiz do projeto.
2. Use o kernel Python do ambiente virtual.
3. Selecione **Run → Run All Cells** para executar a análise inteira.

O notebook deve usar a raiz do projeto como diretório de trabalho. Os dados processados já estão incluídos: não é necessário prepará-los novamente para ler ou executar a análise. Não há dados Base64 incorporados ao notebook.

### Nas próximas sessões

Não é necessário recriar o ambiente nem reinstalar as dependências. Abra um terminal na raiz do projeto e execute:

**Windows — PowerShell:**

```powershell
.\.venv312\Scripts\Activate.ps1
python -m jupyterlab
```

Se a ativação estiver bloqueada:

```powershell
.\.venv312\Scripts\python.exe -m jupyterlab
```

**Linux / macOS:**

```bash
source .venv312/bin/activate
python -m jupyterlab
```

Para encerrar, salve o notebook e pressione **Ctrl+C** no terminal do Jupyter; confirme o encerramento se solicitado. Se tiver ativado o ambiente, execute `deactivate` para sair dele. Fechar apenas a aba do navegador não encerra o servidor.

## Reconstruir os dados processados

Com o ambiente virtual ativado, execute na raiz do projeto:

```bash
python scripts/prepare_data.py
```

No Windows, sem ativar o ambiente, o comando equivalente é:

```powershell
.\.venv312\Scripts\python.exe scripts/prepare_data.py
```

O script funciona também quando `data/processed` não existe. Lê somente as fontes locais de `data/raw`, cria a pasta de saída e sobrescreve os arquivos derivados conhecidos. Não modifica os arquivos raw nem precisa de rede. Os DBF descompactados são temporários e removidos automaticamente. Em seguida, reinicie o kernel e execute o notebook inteiro.

O manifesto registra os hashes das fontes e dos derivados; o notebook verifica esses hashes antes da análise. Se uma fonte for substituída por outra versão, execute novamente a preparação e examine as divergências: o controle de 18.025 casos impede alterações silenciosas do recorte de referência. Não remova controles apenas para forçar a execução.

## Executar ou recalcular o machine learning

A seção 12 do notebook compara sete modelos com validação espacial aninhada. Os resultados já estão incluídos em `results/ml`; o notebook verifica os hashes das entradas, do script e dos resultados. Se estiverem válidos, reutiliza os cálculos e refaz as tabelas e figuras. Se houver mudança, recalcula automaticamente.

Para forçar uma execução completa, com o venv ativo:

```bash
python scripts/modelagem.py
```

No PowerShell, sem ativação:

```powershell
.\.venv312\Scripts\python.exe scripts/modelagem.py
```

Também é possível definir `RECALCULAR_ML=True` no notebook. O treinamento usa uma única thread para limitar consumo e favorecer reprodutibilidade. A duração depende do computador. Não altera as fontes raw nem os dados processed; atualiza somente `results/ml`. Após recalcular, execute o notebook para atualizar suas saídas.

O modelo com menor desvio no protocolo espacial é Poisson com demografia e PIB, mas apresenta R² de incidência de apenas 0,085 e forte subestimação da carga. O ganho com vacinação não é estável. Esses resultados negativos e suas limitações são parte da conclusão, não um erro de execução. As saídas são previsões retrospectivas fora da amostra; não são previsões futuras ou efeitos causais.

## Observações

As análises são descritivas. Cobertura administrativa não é imunidade individual; associação municipal não demonstra causalidade. Dados ausentes e datas discordantes são examinados no notebook. Consulte `FONTES.md` antes de interpretar ou reutilizar os resultados.

## Gráfico simples e clustering

A seção 13 começa com o gráfico de D2 média de 2016–2018 versus incidência de 2019 e uma tipologia descritiva em quatro quadrantes. Os limiares são a mediana de cobertura e a incidência estadual, não metas de vacinação.

Em seguida, compara k-means com 2 a 6 grupos usando vacinação, intensidade da epidemia e demografia. A solução escolhida tem três grupos (silhueta 0,323), mas dois grupos têm score quase igual (0,321). Há 40 subamostragens, reescolha de k, comparação com Ward e sensibilidades ao tratamento de valores >100%. O agrupamento descreve a epidemia passada; não prevê risco futuro nem demonstra causalidade.

Para recalcular, com o venv ativo:

```bash
python scripts/clustering.py
```

No PowerShell sem ativação:

```powershell
.\.venv312\Scripts\python.exe scripts/clustering.py
```

Também é possível definir `RECALCULAR_CLUSTERING=True` no notebook. Os resultados prontos estão em `results/clustering`, com hashes verificados antes da leitura. Depois de recalcular, execute o notebook para atualizar suas saídas. Nenhuma dependência adicional foi acrescentada às já usadas na seção 12.
