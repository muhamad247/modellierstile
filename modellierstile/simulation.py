"""Simulierte Editor-Logs: Personen modellieren denselben Prozess in einem BPMN-Editor.

Jede Person hat einen von drei Stilen, den die Analyse nicht kennt. Der wahre Stil steht
nur in sitzungen.csv, damit man am Ende prüfen kann, ob das Clustering ihn wiederfindet.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"

START = "Start"
KNOTEN = "Knoten anlegen"
KANTE = "Kante anlegen"
LOESCHEN = "Löschen"
VERSCHIEBEN = "Verschieben"
UMBENENNEN = "Umbenennen"
AKTIONEN = [KNOTEN, KANTE, LOESCHEN, VERSCHIEBEN, UMBENENNEN]


@dataclass(frozen=True)
class Stil:
    name: str
    anteil: float  # Anteil der Personen mit diesem Stil
    block: float  # mittlere Zahl neuer Elemente zwischen zwei Denkpausen
    pause_s: float  # Median einer Denkpause
    abstand_s: float  # Median zwischen zwei Aktionen ohne Pause
    p_verschieben: float  # Wahrscheinlichkeit, dass eine Aktion während des Modellierens Layout ist
    p_loeschen: float
    p_umbenennen: float
    layout_ende: float  # mittlere Zahl an Verschiebungen nach dem letzten neuen Element
    fehler: float  # mittlere Zahl an Fehlern im fertigen Modell


STILE = [
    Stil("zügig", 0.35, 6, 20, 4.0, 0.06, 0.03, 0.04, 12, 0.8),
    Stil("nachdenklich", 0.30, 9, 60, 5.0, 0.07, 0.03, 0.04, 6, 0.5),
    Stil("ausprobierend", 0.35, 3, 25, 4.5, 0.25, 0.12, 0.07, 2, 1.8),
]


def _variiert(rng: np.random.Generator, wert: float, streuung: float = 0.3) -> float:
    """Persönliche Abweichung vom Stil: multiplikativ, damit Werte positiv bleiben."""
    return wert * float(np.exp(rng.normal(0, streuung)))


def simuliere_sitzung(
    rng: np.random.Generator, stil: Stil, sitzung: str, beginn: datetime
) -> tuple[list[dict], dict]:
    """Ein Durchgang vom Öffnen der Aufgabe bis zum fertigen Modell."""
    block = _variiert(rng, stil.block)
    pause_s = _variiert(rng, stil.pause_s)
    abstand_s = _variiert(rng, stil.abstand_s, 0.2)
    # Obergrenzen, damit auch bei starker Streuung mehr angelegt als gelöscht wird
    p_verschieben = min(_variiert(rng, stil.p_verschieben, 0.25), 0.4)
    p_loeschen = min(_variiert(rng, stil.p_loeschen, 0.25), 0.18)
    p_umbenennen = stil.p_umbenennen
    layout_ende = _variiert(rng, stil.layout_ende)

    ziel_knoten = int(rng.integers(16, 26))
    ziel_kanten = ziel_knoten + int(rng.integers(1, 5))
    knoten: list[str] = []
    kanten: list[str] = []
    nummer = 0
    t = beginn
    events = [{"sitzung": sitzung, "zeitpunkt": t, "aktion": START, "element": None}]

    def neu(prefix: str) -> str:
        nonlocal nummer
        nummer += 1
        return f"{prefix}{nummer}"

    def log(aktion: str, element: str) -> None:
        events.append({"sitzung": sitzung, "zeitpunkt": t, "aktion": aktion, "element": element})

    def fertig() -> bool:
        return len(knoten) >= ziel_knoten and len(kanten) >= ziel_kanten

    erste = True
    while not fertig():
        # Denkpause vor jedem Block; beim ersten Mal wird zusätzlich die Aufgabe gelesen
        laenge = rng.lognormal(np.log(pause_s), 0.5) * (2.0 if erste else 1.0)
        t += timedelta(seconds=float(laenge))
        erste = False
        ziel_block = 1 + int(rng.poisson(max(block - 1, 0)))
        angelegt = 0
        while angelegt < ziel_block and not fertig():
            t += timedelta(seconds=float(rng.lognormal(np.log(abstand_s), 0.4)))
            r = rng.random()
            if r < p_verschieben and knoten:
                log(VERSCHIEBEN, str(rng.choice(knoten)))
            elif r < p_verschieben + p_loeschen and knoten:
                if kanten and rng.random() < len(kanten) / (len(knoten) + len(kanten)):
                    log(LOESCHEN, kanten.pop(int(rng.integers(len(kanten)))))
                else:
                    log(LOESCHEN, knoten.pop(int(rng.integers(len(knoten)))))
            elif r < p_verschieben + p_loeschen + p_umbenennen and knoten:
                log(UMBENENNEN, str(rng.choice(knoten)))
            else:
                kante_moeglich = len(knoten) >= 2 and len(kanten) < len(knoten) + 3
                kante = kante_moeglich and (len(knoten) >= ziel_knoten or rng.random() < 0.45)
                if kante:
                    kanten.append(neu("E"))
                    log(KANTE, kanten[-1])
                else:
                    knoten.append(neu("K"))
                    log(KNOTEN, knoten[-1])
                angelegt += 1

    # Aufräumen am Schluss: Elemente zurechtschieben, ein paar Namen korrigieren
    for _ in range(int(rng.poisson(layout_ende))):
        t += timedelta(seconds=float(rng.lognormal(np.log(abstand_s), 0.4)))
        aktion = UMBENENNEN if rng.random() < 0.15 else VERSCHIEBEN
        log(aktion, str(rng.choice(knoten)))

    info = {
        "sitzung": sitzung,
        "stil": stil.name,
        "knoten": len(knoten),
        "kanten": len(kanten),
        "fehler": int(rng.poisson(_variiert(rng, stil.fehler, 0.2))),
    }
    return events, info


def simuliere(n: int = 120, seed: int = 7) -> tuple[pd.DataFrame, pd.DataFrame]:
    """n Sitzungen an drei Übungsterminen; liefert Ereignislog und Sitzungsinfos."""
    rng = np.random.default_rng(seed)
    stile = rng.choice(len(STILE), size=n, p=[s.anteil for s in STILE])
    termine = [datetime(2026, 3, 10, 9), datetime(2026, 3, 17, 9), datetime(2026, 3, 24, 9)]
    alle_events, infos = [], []
    for i, s in enumerate(stile):
        beginn = termine[i % 3] + timedelta(minutes=int(rng.integers(0, 120)))
        events, info = simuliere_sitzung(rng, STILE[s], f"S{i + 1:03d}", beginn)
        alle_events.extend(events)
        infos.append(info)
    log = pd.DataFrame(alle_events)
    log["zeitpunkt"] = log["zeitpunkt"].dt.round("ms")
    return log, pd.DataFrame(infos)


def schreibe(ordner: Path = DATA, n: int = 120, seed: int = 7) -> None:
    log, sitzungen = simuliere(n, seed)
    ordner.mkdir(parents=True, exist_ok=True)
    log.to_csv(ordner / "modellierlog.csv", index=False)
    sitzungen.to_csv(ordner / "sitzungen.csv", index=False)


def lade(ordner: Path = DATA) -> tuple[pd.DataFrame, pd.DataFrame]:
    log = pd.read_csv(ordner / "modellierlog.csv", parse_dates=["zeitpunkt"])
    return log, pd.read_csv(ordner / "sitzungen.csv")


if __name__ == "__main__":
    schreibe()
    print(f"geschrieben nach {DATA}")
