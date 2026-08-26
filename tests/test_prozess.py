import pytest

from modellierstile import prozess


def test_folge_mit_denkpausen(kleine_sitzung):
    assert prozess.folge(kleine_sitzung) == [
        "Start",
        "Nachdenken",
        "Knoten anlegen",
        "Knoten anlegen",
        "Kante anlegen",
        "Löschen",
        "Nachdenken",
        "Knoten anlegen",
        "Kante anlegen",
        "Verschieben",
        "Umbenennen",
        "Verschieben",
        "Ende",
    ]


def test_directly_follows_zaehlt_uebergaenge(kleine_sitzung):
    paare = prozess.directly_follows(kleine_sitzung)
    assert paare[("Knoten anlegen", "Kante anlegen")] == 2
    assert paare[("Nachdenken", "Knoten anlegen")] == 2
    assert paare[("Verschieben", "Ende")] == 1
    assert sum(paare.values()) == 12


def test_anteile_summieren_je_aktion_auf_eins(simuliert):
    df = prozess.anteile(prozess.directly_follows(simuliert[0]))
    assert df.groupby("von")["anteil"].sum().to_numpy() == pytest.approx(1)
    assert "Ende" not in set(df["von"])


def test_mermaid_zeigt_nur_haeufige_uebergaenge(kleine_sitzung):
    text = prozess.mermaid(prozess.directly_follows(kleine_sitzung), min_anteil=0.6)
    assert text.startswith("flowchart LR")
    # Start, Löschen, Nachdenken und Umbenennen haben je nur eine Art Nachfolger
    assert text.count("-->|100%|") == 4
    # auf „Knoten anlegen“ folgt zweimal eine Kante und einmal ein Knoten: nur 67 % bleibt
    assert text.count("-->|67%|") == 1
    # Verschieben verteilt sich auf Umbenennen und Ende (je 50 %) und fällt weg
    assert "-->|50%|" not in text
