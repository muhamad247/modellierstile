import pytest

from modellierstile.merkmale import elemente_im_zeitverlauf, merkmale_sitzung, phasen


def test_kennzahlen_der_kleinen_sitzung(kleine_sitzung):
    m = merkmale_sitzung(kleine_sitzung)
    assert m["aktionen"] == 9
    assert m["dauer_min"] == pytest.approx(72 / 60)
    assert m["aktionen_pro_min"] == pytest.approx(9 / 1.2)
    assert m["anteil_verstehen"] == pytest.approx((20 + 29) / 72)
    assert m["median_pause_s"] == pytest.approx(24.5)
    assert m["blockgroesse"] == pytest.approx(5 / 2)
    assert m["loeschquote"] == pytest.approx(1 / 5)
    assert m["anteil_layout"] == pytest.approx(3 / 9)
    assert m["layout_am_ende"] == pytest.approx(1.0)


def test_hoehere_schwelle_findet_weniger_pausen(kleine_sitzung):
    m = merkmale_sitzung(kleine_sitzung, schwelle=25)
    assert m["median_pause_s"] == pytest.approx(29)
    assert m["anteil_verstehen"] == pytest.approx(29 / 72)


def test_phasen_der_kleinen_sitzung(kleine_sitzung):
    p = phasen(kleine_sitzung)
    assert p["phase"].tolist() == ["Verstehen", "Modellieren", "Verstehen", "Abstimmen"]
    dauer = (p["ende"] - p["beginn"]).dt.total_seconds().tolist()
    assert dauer == [20, 11, 29, 12]
    assert p["aktionen"].tolist() == [0, 4, 0, 5]


def test_elemente_im_zeitverlauf(kleine_sitzung):
    v = elemente_im_zeitverlauf(kleine_sitzung)
    assert v["elemente"].tolist() == [0, 1, 2, 3, 2, 3, 4, 4, 4, 4]
    assert v["minute"].iloc[-1] == pytest.approx(1.2)
