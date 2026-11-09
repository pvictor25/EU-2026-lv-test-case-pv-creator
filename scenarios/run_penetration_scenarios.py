"""Script para Execução Paramétrica de Cenários de Penetração FV na Rede IEEE LV Test Case.

Metodologia:
1. O Cenário Base é definido com 0 PVs (0% de penetração da rede).
2. Os cenários de penetração variam a porcentagem de barras elegíveis ocupadas
   por sistemas fotovoltaicos: p_rede in {0%, 2%, 5%, 8%, 10%}.
3. Para cada nível percentual:
   - Aloca os geradores via PVCreator (dimensão comercial + BR-PVGen + PCHIP 5 min).
   - Executa a co-simulação temporal completa de 24h (288 passos de 5 min) no Mosaik + OpenDSS.
   - Salva os resultados detalhados em `output/result_penetracao_{pct}pct.csv`.
4. Salva uma tabela resumo consolidada em `output/tabela_cenarios_penetracao.csv`
   e `output/resumo_cenarios_penetracao.json` para que o notebook de estudo
   possa simplesmente carregar os CSVs e gerar as análises e figuras do banner.
"""

import json
import sys
import time
from pathlib import Path

import pandas as pd

# Ajusta sys.path para garantir importação dos pacotes em src/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from scenarios.scenario_LVTestCase import run_scenario  # noqa: E402
from simulators.util.pv_creator import PVCreator, PVGenerator  # noqa: E402

DATA_DIR = (PROJECT_ROOT / "data" / "LVTestCase").resolve()
OUTPUT_DIR = (PROJECT_ROOT / "output").resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CIRCUITO_MASTER = DATA_DIR / "Master.dss"
ARQUIVO_PV_DSS = DATA_DIR / "LVTestCase_pv.dss"

# Base de barras da rede IEEE European LV Test Feeder (excluindo sourcebus)
TOTAL_BARRAS_REDE = 906

# Níveis percentuais de penetração fotovoltaica a simular
# O cenário base é 0% (0 PVs), seguido de 2%, 5%, 8% e 10%
NIVEIS_PENETRACAO_PCT = [0, 2, 5, 8, 10]


def calcular_qtd_pvs_por_percentual(pct_rede: float, total_barras: int = TOTAL_BARRAS_REDE) -> int:
    """Converte a taxa percentual de penetração na rede (%) em quantidade inteira de PVs."""
    return round((pct_rede / 100.0) * total_barras)


def configurar_cenario_pv(qtd_pvs: int, seed_val: int = 25):
    """Aloca os PVs e gera os arquivos DSS/CSV em data/LVTestCase/ para o cenário."""
    if qtd_pvs == 0:
        # Cenário Base: 0 PVs na rede
        header_0pct = (
            "! ====================================================================\n"
            "! CENÁRIO BASE: 0% DE PENETRAÇÃO FV (0 GERADORES FOTOVOLTAICOS)\n"
            "! Rede IEEE European LV Test Feeder sem geração distribuída.\n"
            "! ====================================================================\n"
        )
        ARQUIVO_PV_DSS.write_text(header_0pct, encoding="utf-8")
        return []

    # Alocação automatizada via PVCreator com dimensionamento comercial e BR-PVGen (apenas monofásicos BT)
    pv_generators = PVCreator(
        QtdPVs=qtd_pvs,
        SCRIPT_DSS=CIRCUITO_MASTER,
        step="5min",
        my_seed=seed_val,
        bus_multi_PV=False,
        only_1phase_BT=True,
    )
    PVGenerator.GenerateCSV(pv_generators, OUTPUT_DIR=DATA_DIR)
    PVGenerator.GenerateDSS(pv_generators, OUTPUT_DIR=DATA_DIR)
    return pv_generators


def executar_todos_cenarios():
    """Executa sequencialmente todos os cenários de penetração FV e exporta os resultados."""
    print("=" * 80)
    print("INICIANDO EXECUÇÃO PARAMÉTRICA DE CENÁRIOS DE PENETRAÇÃO FV (MOSAIK + OPENDSS)")
    print(f"Rede de Teste: IEEE European LV Test Feeder ({TOTAL_BARRAS_REDE} barras elegíveis)")
    print("Cenário Base : 0% de penetração (0 PVs)")
    print(f"Cenários FV  : {NIVEIS_PENETRACAO_PCT}% das barras da rede")
    print("=" * 80)

    registro_cenarios = []
    t_inicio_total = time.perf_counter()

    for pct in NIVEIS_PENETRACAO_PCT:
        qtd_pvs = calcular_qtd_pvs_por_percentual(pct, TOTAL_BARRAS_REDE)
        pct_efetivo = (qtd_pvs / TOTAL_BARRAS_REDE) * 100.0
        csv_saida = OUTPUT_DIR / f"result_penetracao_{pct}pct.csv"

        print(
            f"\n>>> [CENÁRIO {pct}%] Alocando {qtd_pvs} PVs ({pct_efetivo:.2f}% efetivo da rede)..."
        )
        t0_cenario = time.perf_counter()

        # 1. Configura arquivos DSS/CSV para a quantidade de PVs deste cenário
        pvs_alocados = configurar_cenario_pv(qtd_pvs, seed_val=25)
        kva_total = sum(float(pv.kva) for pv in pvs_alocados) if pvs_alocados else 0.0

        # 2. Executa co-simulação no Mosaik e salva CSV específico do cenário
        print(f"    Executando co-simulação temporal 24h -> {csv_saida.name} ...")
        # Para evitar regerar o mesmo grafo JSON 5 vezes, apenas geramos no primeiro cenário
        run_scenario(output_csv=csv_saida, export_topo=(pct == 0))

        tempo_cenario = time.perf_counter() - t0_cenario
        print(f"    [OK] Cenário {pct}% concluído em {tempo_cenario:.2f} s.")

        registro_cenarios.append(
            {
                "pct_alvo": pct,
                "pct_efetivo": round(pct_efetivo, 2),
                "qtd_pvs": qtd_pvs,
                "kva_total": round(kva_total, 1),
                "arquivo_csv": str(csv_saida.relative_to(PROJECT_ROOT)),
                "tempo_simulacao_s": round(tempo_cenario, 2),
            }
        )

    # 3. Mantém os arquivos do pior caso (10% / 91 PVs) ativos em data/LVTestCase/
    print("\nMantendo arquivos DSS/CSV do Pior Caso (10% / 91 PVs) em data/LVTestCase/ ...")
    configurar_cenario_pv(calcular_qtd_pvs_por_percentual(10, TOTAL_BARRAS_REDE), seed_val=25)

    # 4. Salva tabela e JSON de resumo dos cenários executados
    df_resumo = pd.DataFrame(registro_cenarios)
    caminho_tabela = OUTPUT_DIR / "tabela_cenarios_penetracao.csv"
    caminho_json = OUTPUT_DIR / "resumo_cenarios_penetracao.json"

    df_resumo.to_csv(caminho_tabela, index=False)
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(registro_cenarios, f, indent=4, ensure_ascii=False)

    tempo_total = time.perf_counter() - t_inicio_total
    print("\n" + "=" * 80)
    print(f"TODOS OS CENÁRIOS FORAM EXECUTADOS COM SUCESSO! (Tempo total: {tempo_total:.2f} s)")
    print("=" * 80)
    print(df_resumo.to_string(index=False))
    print(f"\nTabela consolidada salva em : {caminho_tabela}")
    print(f"Metadados em JSON salvos em : {caminho_json}")


if __name__ == "__main__":
    executar_todos_cenarios()
