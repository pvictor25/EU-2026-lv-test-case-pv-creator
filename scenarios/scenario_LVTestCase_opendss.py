"""Execução direta do cenário IEEE European LV Test Feeder (LVTestCase) apenas com OpenDSS (sem Mosaik).

Simula 24 horas (288 passos de 5 minutos) aplicando os perfis de carga (LoadShapes de 1 min)
e as curvas de irradiância e temperatura (5 min) geradas pelo PVCreator, salvando os resultados
consolidados em CSV na pasta `output/`.
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import py_dss_interface

from simulators.util.topologia import exportar_topologia

# ==============================================================================
# 1. CAMINHOS E PARÂMETROS DA SIMULAÇÃO
# ==============================================================================
CURRENT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = CURRENT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data" / "LVTestCase"
CIRCUITO_DSS = DATA_DIR / "run_LVTestCase.dss"
IRRADIANCE_CSV = DATA_DIR / "LVTestCase_shape_pv_5min.csv"
TEMPERATURE_CSV = DATA_DIR / "LVTestCase_temperature_5min.csv"

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ARQUIVO_RESULTADOS_CSV = OUTPUT_DIR / "result_run_LVTestCase.csv"
ARQUIVO_RESULTADOS_OPENDSS_CSV = OUTPUT_DIR / "result_run_LVTestCase_opendss.csv"
JSON_SAIDA = str(OUTPUT_DIR / "topologia_LVTestCase.json")

START_DATE = "2026-01-01 00:00:00"
STEP_SIZE = 60 * 5  # 300 segundos (5 minutos)
N_PASSOS = 288


def run_scenario_opendss(
    circuito_dss: Path = CIRCUITO_DSS,
    output_csv: Path = ARQUIVO_RESULTADOS_CSV,
    export_json: bool = True,
) -> pd.DataFrame:
    """Executa a simulação temporal de 24h (passo de 5 min) diretamente no OpenDSS."""
    if not circuito_dss.exists():
        raise FileNotFoundError(f"[ERRO]: Arquivo DSS não encontrado em: {circuito_dss}")

    orig_cwd = Path.cwd()
    try:
        if export_json:
            print("Gerando topologia do cenário LV Test Case...")
            exportar_topologia(circuito_dss, JSON_SAIDA)

        print("--- Inicializando Simulação Direta no OpenDSS (Sem Mosaik) ---")
        dss = py_dss_interface.DSS()
        dss.text("Clear")
        dss.text(f"set datapath={circuito_dss.parent}")
        dss.text(f'Redirect "{circuito_dss}"')

        if dss.circuit.num_buses == 0:
            raise RuntimeError(f"Falha ao compilar o circuito OpenDSS: {circuito_dss}")

        # Vincula os perfis Yearly (Shape_1..Shape_55) à propriedade Daily das cargas
        # para que o modo Daily do OpenDSS atualize simultaneamente Cargas (1 min) e PVs (5 min)
        idx_load = dss.loads.first()
        while idx_load > 0:
            y_shape = dss.loads.yearly
            if y_shape:
                dss.loads.daily = y_shape
            idx_load = dss.loads.next()

        # Configura simulação passo a passo no modo Daily (mode=1)
        dss.solution.mode = 1
        dss.solution.number = 1
        dss.solution.step_size = STEP_SIZE
        dss.solution.max_iterations = 100
        dss.solution.max_control_iterations = 30

        # Mapeia os nós de cada barra no vetor dss.circuit.buses_vmag_pu
        bus_names = list(dss.circuit.buses_names)
        node_names = list(dss.circuit.nodes_names)
        bus_node_pos: dict[str, dict[int, int]] = {b.lower(): {} for b in bus_names}
        for pos, nname in enumerate(node_names):
            b_part, _, ph_part = nname.rpartition(".")
            if ph_part in ("1", "2", "3"):
                bus_node_pos.setdefault(b_part.lower(), {})[int(ph_part)] = pos

        pv_names = list(dss.pvsystems.names) if dss.pvsystems.count > 0 else []
        if pv_names and pv_names[0].upper() == "NONE":
            pv_names = []

        print(
            f"Circuito compilado: '{dss.circuit.name}' | "
            f"{len(bus_names)} barras | {dss.loads.count} cargas | {len(pv_names)} PVs"
        )
        print(f"Executando {N_PASSOS} passos de {STEP_SIZE}s (24h)...")

        dates = pd.date_range(start=START_DATE, periods=N_PASSOS, freq=f"{STEP_SIZE}s")
        records: list[dict] = []

        for step_idx in range(N_PASSOS):
            dss.solution.solve()
            if not dss.solution.converged:
                print(f"[AVISO] Passo {step_idx} não convergiu no limite de iterações.")

            row: dict = {
                "date": dates[step_idx].strftime("%Y-%m-%d %H:%M:%S"),
            }

            # 1. Tensões em todas as barras (V1_pu, V2_pu, V3_pu)
            vmag_pu = dss.circuit.buses_vmag_pu
            for b in bus_names:
                ph_map = bus_node_pos.get(b.lower(), {})
                row[f"DSS.Bus-{b}-V1_pu"] = vmag_pu[ph_map[1]] if 1 in ph_map else np.nan
                row[f"DSS.Bus-{b}-V2_pu"] = vmag_pu[ph_map[2]] if 2 in ph_map else np.nan
                row[f"DSS.Bus-{b}-V3_pu"] = vmag_pu[ph_map[3]] if 3 in ph_map else np.nan

            # 2. Medições na linha tronco LINE1 (terminal 1)
            dss.circuit.set_active_element("Line.LINE1")
            l_powers = dss.cktelement.powers
            l_currents = dss.cktelement.currents_mag_ang
            row["DSS.Line-LINE1-P1_w"] = l_powers[0]
            row["DSS.Line-LINE1-Q1_var"] = l_powers[1]
            row["DSS.Line-LINE1-P2_w"] = l_powers[2]
            row["DSS.Line-LINE1-Q2_var"] = l_powers[3]
            row["DSS.Line-LINE1-P3_w"] = l_powers[4]
            row["DSS.Line-LINE1-Q3_var"] = l_powers[5]
            row["DSS.Line-LINE1-I1_A"] = l_currents[0]
            row["DSS.Line-LINE1-I1_ang"] = l_currents[1]
            row["DSS.Line-LINE1-I2_A"] = l_currents[2]
            row["DSS.Line-LINE1-I2_ang"] = l_currents[3]
            row["DSS.Line-LINE1-I3_A"] = l_currents[4]
            row["DSS.Line-LINE1-I3_ang"] = l_currents[5]

            # 3. Potências AC injetadas por cada PVSystem (convenção positiva para geração)
            for pv_name in pv_names:
                dss.circuit.set_active_element(f"PVSystem.{pv_name}")
                pv_pq = dss.cktelement.powers
                p_inj = -sum(pv_pq[0:6:2])
                q_inj = -sum(pv_pq[1:6:2])
                row[f"InverterSim.Inverter-{pv_name}-P_ac"] = p_inj
                row[f"InverterSim.Inverter-{pv_name}-Q_ac"] = q_inj
                row[f"DSS.PVSystem-{pv_name}-P_meas"] = p_inj
                row[f"DSS.PVSystem-{pv_name}-Q_meas"] = q_inj

            records.append(row)

        df_res = pd.DataFrame(records)
        df_res.to_csv(output_csv, index=False)
        if output_csv != ARQUIVO_RESULTADOS_OPENDSS_CSV:
            df_res.to_csv(ARQUIVO_RESULTADOS_OPENDSS_CSV, index=False)

        print("Simulação OpenDSS concluída com sucesso!")
        print(f"Resultados salvos em: {output_csv}")
        return df_res
    finally:
        os.chdir(orig_cwd)


# Alias para compatibilidade direta com chamadas `run_scenario()`
run_scenario = run_scenario_opendss


if __name__ == "__main__":
    run_scenario_opendss()
