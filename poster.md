# Automatização em Python da Alocação de Geradores Fotovoltaicos para Estudos na Rede Elétrica com o OpenDSS

**Autor:** Paulo Victor Pereira Lima  
**Orientador:** Lucas Silveira Melo  
**Co-autores:** Ruth Pastora Saraiva Leão, Raquel Cristina Filiagi Gregory, Janaína Barbosa Almada, Luis Felipe Carneiro de Souza, Caio Lucas Nascimento Silva  
**Instituição:** Universidade Federal do Ceará (UFC) — Departamento de Engenharia Elétrica  

---

## 📌 COLUNA 1

### Introdução
- **Expansão de REDs:** Crescimento acelerado da microgeração fotovoltaica (FV) em redes de Baixa Tensão (BT).
- **Desafios Operativos:** Sobretensões acentuadas em regime permanente e inversão do fluxo de potência.
- **Gargalo no OpenDSS:** Declaração manual de cada elemento é lenta e inviabiliza simulações em larga escala.

---

### Objetivos
- Desenvolver ferramenta em **Python** para leitura da rede e alocação pseudo-aleatória de FV no OpenDSS via `py-dss-interface`.
- Integrar dados reais do **BR-PVGen** em co-simulação temporal via **Mosaik** sob limites do PRODIST.
- Quantificar impactos de penetrações de 0% a 10% no alimentador **IEEE European LV Test Case** (906 barras).

---

### Metodologia
- **Varredura Topológica:** Mapeamento automático dos circuitos e identificação de barras elegíveis.
- **Alocação Pseudo-Aleatória:** Sorteio reprodutível em 4 faixas comerciais (1 a 10 kVA), somando 91 FV (470,7 kVA).
- **Co-Simulação 24h:** Séries temporais reais com passo de 1 min (1 440 passos) em fluxo de potência trifásico.

#### Topologia e Alocação dos Geradores FV
![Figura 1a — Topologia IEEE LV Test Case](./output/figuras_banner/fig1a_topologia_rede_pior_caso.png)
*Figura 1a: Alocação de 91 geradores FV (10% das barras) na rede IEEE LV Test Case.*

#### Portes Comerciais dos Geradores FV (Cenário 10%)
![Tabela 1b — Portes Comerciais FV](./output/figuras_banner/tab1b_portes_comerciais_pv.png)

| Faixa Comercial (kVA) | Capacidade Total (kVA) | Fração Potência (%) | Qtd. Geradores | Fração Geradores (%) |
| :--- | :---: | :---: | :---: | :---: |
| 1,0 a 3,6 kVA | 103,2 | 21,9% | 41 un. | 45,1% |
| 4,0 a 7,0 kVA | 114,0 | 24,2% | 22 un. | 24,2% |
| 7,5 a 9,0 kVA | 123,5 | 26,2% | 15 un. | 16,5% |
| 10,0 kVA | 130,0 | 27,6% | 13 un. | 14,3% |
| **Total** | **470,7** | **100,0%** | **91 un.** | **100,0%** |

> **Agilidade:** Script OpenDSS completo gerado em menos de **3 segundos**.

---
---

## 📌 COLUNA 2

### Resultados

#### Perfil Espacial de Tensão e Barra Crítica
![Figura 1c — Perfil Espacial de Tensão](./output/figuras_banner/fig1c_perfil_tensao_rede_pior_caso.png)
*Figura 1c: Perfil espacial às 12h00; Barra Crítica 890 (fase 1) destacada em 'X'.*

- **Pico Global na Barra 890:** Máxima sobretensão de **1,0964 p.u.** às 12h00 (+0,0469 p.u. sobre o caso base).
- **Violação Normativa:** **100% das 906 barras** superam o limite PRODIST (1,05 p.u.) no pico solar de 10% FV.

#### Dinâmica Temporal na Barra Crítica (24h)
![Figura 3b — Tensão na Barra Crítica ao Longo de 24h](./output/figuras_banner/fig3b_tensao_barra_critica_890.png)
*Figura 3b: Curvas diárias de tensão na Barra 890 para penetrações de 0% a 10%.*

- **Sensibilidade a Baixa Penetração:** Apenas 2% de nós com FV (86,5 kVA) já viola 1,05 p.u. em **97,35% das barras**.
- **Inversão Severa de Fluxo:** Potência líquida no transformador TR1 reverte de +3,0 kW para **-242,9 kW** injetados na média tensão.

---

### Conclusão
- **Ferramenta Validada:** Automação em Python reduz tempo de montagem de cenários de horas para segundos com repetibilidade total.
- **Impactos Críticos:** Sobretensões generalizadas (>1,05 p.u.) e fluxo reverso massivo exigem controle ativo em inversores (Volt-VAr/Volt-Watt).
- **Aplicação Prática:** Metodologia essencial para estudos de capacidade de hospedagem (*hosting capacity*) e planejamento de REDs na BT.

---

### Agradecimentos
À **Universidade Federal do Ceará (UFC)**, ao **Departamento de Engenharia Elétrica**, ao orientador, coautores e às agências **CAPES, CNPq e FUNCAP** pelo apoio financeiro à pesquisa.
