from modellierstile.simulation import (
    KANTE,
    KNOTEN,
    LOESCHEN,
    START,
    UMBENENNEN,
    VERSCHIEBEN,
    simuliere,
)


def test_gleicher_seed_gleiche_daten(simuliert):
    log, sitzungen = simuliere()
    assert log.equals(simuliert[0])
    assert sitzungen.equals(simuliert[1])


def test_jede_sitzung_beginnt_mit_start_und_ist_zeitlich_sortiert(simuliert):
    log, sitzungen = simuliert
    assert log["sitzung"].nunique() == len(sitzungen) == 120
    for _, s in log.groupby("sitzung", sort=False):
        assert s["aktion"].iloc[0] == START
        assert (s["aktion"] == START).sum() == 1
        assert s["zeitpunkt"].is_monotonic_increasing


def test_log_ist_in_sich_stimmig(simuliert):
    """Nachspielen: nur vorhandene Elemente werden bearbeitet, das Endmodell passt zu sitzungen.csv."""
    log, sitzungen = simuliert
    soll = sitzungen.set_index("sitzung")
    for sitzung, s in log.groupby("sitzung"):
        knoten, kanten = set(), set()
        for aktion, element in zip(s["aktion"], s["element"]):
            if aktion == KNOTEN:
                knoten.add(element)
            elif aktion == KANTE:
                kanten.add(element)
            elif aktion == LOESCHEN:
                assert element in knoten | kanten
                knoten.discard(element)
                kanten.discard(element)
            elif aktion in (VERSCHIEBEN, UMBENENNEN):
                assert element in knoten
        assert len(knoten) == soll.loc[sitzung, "knoten"] >= 16
        assert len(kanten) == soll.loc[sitzung, "kanten"] > len(knoten)


def test_sitzungen_dauern_realistisch_lang(kennzahlen):
    assert kennzahlen["dauer_min"].between(3, 60).all()
