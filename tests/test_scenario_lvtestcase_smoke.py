"""Smoke test para a rede IEEE European LV Test Feeder (LVTestCase).

Valida a compilação do circuito no OpenDSS, integridade dos arquivos de entrada,
validação de caminhos do PVCreator e consistência dos resultados de simulação.
"""

import datetime as dt
import sys

import pandas as pd
import pytest

sys.path.insert(0, ".")

from simulators.opendss.opendss_wrapper import OpenDSS
from simulators.util.pv_creator import BASE_DIR, INFO_PV_FILE, SCRIPT_DSS


class TestLVTestCaseSmoke:
    """Testes rápidos de integridade e fumaça para o cenário LVTestCase."""

    def test_arquivos_base_existem(self):
        """Verifica se os arquivos essenciais da rede LVTestCase e InfoPV existem."""
        assert INFO_PV_FILE.is_file(), f"Metadados BR-PVGen não encontrados: {INFO_PV_FILE}"
        assert SCRIPT_DSS.is_file(), f"Master.dss da LVTestCase não encontrado: {SCRIPT_DSS}"
        run_dss = BASE_DIR / "data" / "LVTestCase" / "run_LVTestCase.dss"
        assert run_dss.is_file(), f"run_LVTestCase.dss não encontrado: {run_dss}"

    def test_compilacao_opendss(self):
        """Valida se o circuito OpenDSS compila e possui as barras e cargas esperadas."""
        run_dss = BASE_DIR / "data" / "LVTestCase" / "run_LVTestCase.dss"
        wrapper = OpenDSS(
            topofile=run_dss,
            time_step=dt.timedelta(seconds=300),
            start_time=dt.datetime(2026, 1, 1),
        )

        num_buses = wrapper.dss.circuit.num_buses
        assert num_buses >= 900, f"Esperado >= 900 barras no LVTestCase, obtido {num_buses}"

        num_loads = wrapper.dss.loads.count
        assert num_loads == 55, f"Esperado 55 cargas de consumidores, obtido {num_loads}"

    def test_topologia_exportada_json(self):
        """Verifica se a topologia exportada existe e contém os nós e elementos."""
        json_path = BASE_DIR / "data" / "LVTestCase" / "topologia_LVTestCase.json"
        if not json_path.exists():
            json_path = BASE_DIR / "output" / "topologia_LVTestCase.json"

        assert json_path.exists(), f"Arquivo de topologia JSON não encontrado em {json_path}"
        import json

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        assert "nodes" in data or "total_nodes" in data or "elements" in data
        assert len(data.get("nodes", [])) >= 900 or data.get("total_nodes", 0) >= 900

    def test_resultados_simulacao_consistentes(self):
        """Verifica se o CSV de saída da simulação de 24h contém 288 passos e tensões válidas."""
        res_csv = BASE_DIR / "output" / "result_penetracao_10pct.csv"
        if not res_csv.exists():
            res_csv = BASE_DIR / "output" / "result_run_LVTestCase.csv"

        if not res_csv.exists():
            pytest.skip("Arquivo de resultado de simulação ainda não gerado em output/")

        df = pd.read_csv(res_csv, nrows=300)
        assert len(df) == 288, f"Esperado 288 passos temporais (24h a 5 min), obtido {len(df)}"

        v_cols = [c for c in df.columns if c.endswith("_pu")]
        assert len(v_cols) > 0, "Nenhuma coluna de tensão em p.u. encontrada nos resultados"
        min_v = df[v_cols].min().min()
        max_v = df[v_cols].max().max()
        assert 0.7 <= min_v <= 1.1, f"Tensão mínima fora dos limites físicos: {min_v} p.u."
        assert 0.9 <= max_v <= 1.2, f"Tensão máxima fora dos limites físicos: {max_v} p.u."
