import pandas as pd
import pytest

from modellierstile import merkmale
from modellierstile.simulation import simuliere


@pytest.fixture(scope="session")
def simuliert():
    return simuliere()


@pytest.fixture(scope="session")
def kennzahlen(simuliert):
    log, _ = simuliert
    return merkmale.merkmale(log)


@pytest.fixture
def kleine_sitzung():
    """Von Hand gebaut: zwei Denkpausen, ein Modellierblock, ein Layoutblock."""
    folge = [
        (0, "Start", None),
        (20, "Knoten anlegen", "K1"),
        (25, "Knoten anlegen", "K2"),
        (28, "Kante anlegen", "E3"),
        (31, "Löschen", "E3"),
        (60, "Knoten anlegen", "K4"),
        (63, "Kante anlegen", "E5"),
        (66, "Verschieben", "K1"),
        (70, "Umbenennen", "K2"),
        (72, "Verschieben", "K4"),
    ]
    t0 = pd.Timestamp("2026-03-10 09:00")
    return pd.DataFrame(
        [
            {
                "sitzung": "T1",
                "zeitpunkt": t0 + pd.to_timedelta(s, unit="s"),
                "aktion": a,
                "element": e,
            }
            for s, a, e in folge
        ]
    )
