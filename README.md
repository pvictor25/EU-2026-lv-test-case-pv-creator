# Estudo de Alocação Automatizada de Geradores Fotovoltaicos — IEEE European LV Test Feeder (`tsre-der-opentes`)

Repositório dedicado à simulação e análise de Recursos Energéticos Distribuídos (DER) na rede de distribuição secundária **IEEE European Low Voltage Test Feeder (`LVTestCase`)**, integrando **OpenDSS** e **Mosaik** (execução local *in-process*, sem necessidade de Docker) com a ferramenta **`PVCreator`** para alocação automatizada e reprodutível de sistemas fotovoltaicos (SFVs).

**[Documentação base do projeto TSRE-DER-OpenTES](https://grei-ufc.github.io/tsre-der-opentes/)**

---

## 📋 Visão Geral

Este projeto implementa:
1. **Alocação Automatizada de SFVs (`PVCreator`)**:
   - Mapeamento das barras e cargas da rede **IEEE European LV Test Feeder** (906 barras, 55 consumidores monofásicos em $0{,}416\text{ kV}$).
   - Sorteio pseudoaleatório controlado por semente (`seed`) para reprodutibilidade científica.
   - Dimensionamento automático da potência instalada ($\text{kWp}$) e do inversor ($\text{kVA}$) baseado no consumo da unidade consumidora, nas diretrizes da **ANEEL** e em portes comerciais de inversores.
   - Associação de curvas reais de irradiância solar ($\text{W/m}^2$) e temperatura de operação ($^\circ\text{C}$) da base **BR-PVGen** (`data/InfoPV/`), com tratamento de anomalias e reamostragem monotônica via **interpolação PCHIP** ($15\text{ min} \rightarrow 5\text{ min}$).
2. **Co-simulação Mosaik + OpenDSS (`scenarios/scenario_LVTestCase.py`)**:
   - Execução local (*in-process*) acoplando o simulador da rede elétrica (`OpenDSSSimulator`), painéis fotovoltaicos (`PVPanelSimulator`), inversores inteligentes (`InverterSimulator`), coletores de dados (`Collector`) e visualização topológica web (`WebVisSimulator`).
3. **Notebook de Estudo e Geração de Gráficos para Banner Acadêmico (`notebooks/estudo_LVTestCase.ipynb`)**:
   - Reproduz os experimentos de alocação espacial, dimensionamento comercial, análise temporal de 24 horas e estudo paramétrico em função da **porcentagem de barras da rede com geração fotovoltaica** ($p_{\text{rede}} \in \\{0\\%, 2\\%, 5\\%, 8\\%, 10\\%\\}$) das 906 barras elegíveis, correspondendo a 0, 18, 45, 72 e 91 PVs, com **5%** como caso base da co-simulação), avaliando elevação de tensão frente aos limites do **PRODIST Módulo 8** ($0{,}92\text{ a }1{,}05\text{ p.u.}$) e inversão de fluxo de potência no alimentador principal.

---

## 📁 Estrutura do Repositório

```text
├── main.py                              # Ponto de entrada principal (executa scenario_LVTestCase)
├── scenarios/
│   └── scenario_LVTestCase.py           # Cenário de co-simulação Mosaik + OpenDSS (execução local)
├── notebooks/
│   └── estudo_LVTestCase.ipynb          # Notebook de análise e geração de gráficos (300 DPI) para banner
├── src/
│   └── simulators/                      # Adaptadores Mosaik (API v3) e modelos de domínio
│       ├── opendss/                     # Wrapper OpenDSS, construtor de topologia e modelos
│       ├── pv/                          # Simulador de painel fotovoltaico
│       ├── inverter/                    # Simulador de inversor inteligente (OpenDER / IEEE 1547)
│       ├── battery/                     # Simulador de armazenamento em baterias
│       ├── controller/                  # Controladores de tensão e subestação
│       ├── collector/                   # Coletores de séries temporais (CSV)
│       ├── webvis/                      # Visualização interativa em navegador via WebSocket
│       └── util/
│           ├── pv_creator.py            # Ferramenta PVCreator para alocação automatizada de PVs
│           └── topologia.py             # Exportação de topologia da rede
├── data/
│   ├── LVTestCase/                      # Arquivos OpenDSS (.dss, .txt, .csv) da rede IEEE European LV
│   └── InfoPV/                          # Perfis de irradiância e temperatura (base BR-PVGen)
├── output/                              # Resultados de simulação (.csv) e figuras exportadas (.png/.pdf)
├── tests/                               # Testes automatizados (pytest)
└── pyproject.toml                       # Dependências e configuração do projeto (uv)
```

---

## 🚀 Instalação e Configuração

### 1. Instalar dependências com `uv`

Certifique-se de ter o gerenciador de pacotes [`uv`](https://docs.astral.sh/uv/) instalado. Na raiz do projeto, execute:

```bash
uv sync
```

### 2. Configuração específica para Linux / WSL (`py-dss-interface`)

O OpenDSS possui binários pré-compilados nativos para Windows e Linux. Caso esteja em uma distribuição Linux/WSL em que o binário padrão do `py-dss-interface` necessite de compilação local da *engine* C++:

```bash
sudo apt update && sudo apt install build-essential cmake
cd ..
git clone https://github.com/PauloRadatz/py_dss_interface.git
cd py_dss_interface
bash OpenDSSLinuxCPPForRepo.sh
cd ../EU-2026-lv-test-case-pv-creator
uv pip install ../py_dss_interface
```

---

## ▶️ Como Executar

### 1. Rodar o cenário de co-simulação (sem Docker)

O cenário executa todos os simuladores localmente no mesmo processo Python via Mosaik:

```bash
uv run python scenarios/scenario_LVTestCase.py
```

Ou através do ponto de entrada principal:

```bash
uv run python main.py
```

- **Saída da co-simulação**: `output/result_run_LVTestCase.csv`
- **Arquivos OpenDSS/CSV gerados pelo `PVCreator`**: `data/LVTestCase/` (`LVTestCase_pv.dss`, `LVTestCase_shape_pv_5min.csv`, `LVTestCase_temperature_5min.csv`)

### 2. Executar o Notebook e gerar os gráficos para o Banner Acadêmico

Para abrir e executar o notebook interativo:

```bash
uv run jupyter notebook notebooks/estudo_LVTestCase.ipynb
```

Ao executar todas as células do notebook, as figuras prontas para publicação em banner (**300 DPI**, formatos `.png` e `.pdf` vetorial) serão salvas automaticamente em `output/figuras_banner/`:

| Arquivo gerado | Conteúdo |
| :--- | :--- |
| `fig1_topologia_alocacao_fv` | Mapa espacial da rede BT para **5% de penetração na rede** (45/906 barras) e participação percentual dos portes comerciais ($\text{kVA}$). |
| `fig2_curvas_brpvgen_pchip` | Envelope de diversidade das curvas **BR-PVGen** (5% da rede) e comparação entre interpolação PCHIP vs. Linear ($15\text{ min} \rightarrow 5\text{ min}$). |
| `fig3_evolucao_tensao_24h` | Evolução diária (24h) das tensões na rede: **0% (Sem FV)** vs. **5% de penetração FV (Co-simulação Mosaik)** frente ao limite de $1{,}05\text{ p.u.}$ do PRODIST. |
| `fig4_perfil_longitudinal_tensao` | Perfil longitudinal de tensão vs. distância da subestação no pico solar (12h30) e elevação percentual de tensão ($\Delta V\%$) para **5% de penetração**. |
| `fig5_impacto_penetracao_fv_tensao` | Estudo paramétrico por porcentagem da rede (**0%, 2%, 5%, 8% e 10% das barras**): violino/boxplot das tensões e curva de violações ($V > 1{,}05\text{ p.u.}$). |
| `fig6_inversao_fluxo_potencia` | Potência ativa no alimentador principal (`LINE1`) para **0%, 2%, 5%, 8% e 10% de penetração na rede**, evidenciando a inversão do fluxo de potência. |
| `tabela_sintese_banner.csv` | Tabela consolidada com todos os indicadores técnicos por faixa percentual de penetração. |

---

## 🧪 Testes e Qualidade de Código

Para executar a suíte de testes unitários:

```bash
uv run --no-sync python -m pytest tests/ -v
```

Para verificar lint e formatação com `ruff`:

```bash
uv run ruff check src/simulators/ scenarios/ tests/
uv run ruff format src/simulators/ scenarios/ tests/
```
