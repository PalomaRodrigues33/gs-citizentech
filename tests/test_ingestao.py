"""Testes da ingestão do SP156 (CT-01 a CT-05)."""
import json

import pandas as pd
import pytest

from ingestion.sp156 import BRONZE_FILE, REPORT_FILE, classify, read_raw, run_ingestion

COLS = ["Data de Abertura", "Data de Finalização", "Meio de Comunicação", "Tema", "Assunto", "Serviço", "Status",
        "Órgão", "Logradouro", "Número", "CEP", "Latitude", "Longitude", "Prefeitura Operacional", "Distrito"]


def _linha(servico, **kw):
    base = dict.fromkeys(COLS, "x")
    base.update({"Data de Abertura": "2026-07-01", "Data de Finalização": "2026-07-03", "Serviço": servico})
    base.update(kw)
    return base


def _csv(tmp_path, servicos):
    p = tmp_path / "sp156.csv"
    pd.DataFrame([_linha(s) for s in servicos]).to_csv(p, index=False)
    return p


def test_ct01_classifica_os_cinco_grupos():
    assert classify("Tapa-buraco") == "Buraco"
    assert classify("Tapa-buraco em faixa exclusiva ou corredor de ônibus") == "Buraco"
    assert classify("Calçada pública - solicitar manutenção") == "Calçada e acessibilidade"
    assert classify("Acessibilidade - solicitar avaliação de obstáculo na calçada") == "Calçada e acessibilidade"
    assert classify("Entulho e grandes objetos em via pública - solicitar remoção") == "Entulho e lixo"
    assert classify("Fazer reclamação de falta de varrição") == "Varrição"
    assert classify("Solicitar limpeza de bueiros, boca de lobo e poços de visita") == "Bueiro"


def test_ct02_poda_de_arvore_em_calcada_nao_e_calcada():
    assert classify("Árvore – Solicitar avaliação em calçadas e praças para fins de poda ou remoção") is None
    assert classify("Denunciar Fiação solta na calçada") is None


def test_ct03_servico_ausente_ou_fora_do_escopo():
    assert classify(None) is None and classify(float("nan")) is None
    assert classify("Castrar Cães e Gatos Gratuitamente") is None


def test_ct04_ingestao_grava_bronze_e_relatorio(tmp_path):
    src = _csv(tmp_path, ["Tapa-buraco", "Tapa-buraco", "Fazer reclamação de falta de varrição", "Castrar Cães e Gatos"])
    rec, rep = run_ingestion(src, tmp_path / "bronze")
    assert len(rec) == 3 and rep["linhas_lidas"] == 4 and rep["linhas_fora_do_escopo"] == 1
    assert rep["por_grupo"] == {"Buraco": 2, "Varrição": 1}
    assert (tmp_path / "bronze" / BRONZE_FILE).exists()
    assert json.loads((tmp_path / "bronze" / REPORT_FILE).read_text(encoding="utf-8"))["linhas_no_recorte"] == 3


def test_ct05_arquivo_sem_colunas_obrigatorias_e_recusado(tmp_path):
    p = tmp_path / "ruim.csv"
    pd.DataFrame({"a": [1]}).to_csv(p, index=False)
    with pytest.raises(ValueError, match="Colunas ausentes"):
        read_raw(p)
