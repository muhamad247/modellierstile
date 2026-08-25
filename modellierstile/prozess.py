"""Wie die Aktionen aufeinander folgen: Directly-Follows-Graph je Cluster, als Mermaid.

Mermaid-Diagramme zeigt GitHub direkt in der README an, dafür braucht es kein Graphviz.
"""

from __future__ import annotations

from collections import Counter

import pandas as pd

from modellierstile.merkmale import PAUSE_SCHWELLE_S
from modellierstile.simulation import START

NACHDENKEN = "Nachdenken"
ENDE = "Ende"


def folge(sitzung: pd.DataFrame, schwelle: float = PAUSE_SCHWELLE_S) -> list[str]:
    """Aktionen einer Sitzung, mit „Nachdenken“ an jeder Pause über der Schwelle."""
    s = sitzung.sort_values("zeitpunkt")
    luecke = s["zeitpunkt"].diff().dt.total_seconds().fillna(0).to_numpy()
    ergebnis = []
    for aktion, l in zip(s["aktion"], luecke):
        if l >= schwelle:
            ergebnis.append(NACHDENKEN)
        ergebnis.append(aktion)
    return ergebnis + [ENDE]


def directly_follows(log: pd.DataFrame, schwelle: float = PAUSE_SCHWELLE_S) -> Counter:
    """Wie oft auf Aktion a direkt Aktion b folgt, über alle Sitzungen im Log."""
    paare: Counter = Counter()
    for _, sitzung in log.groupby("sitzung"):
        f = folge(sitzung, schwelle)
        paare.update(zip(f, f[1:]))
    return paare


def anteile(paare: Counter) -> pd.DataFrame:
    """Für jede Aktion: welcher Anteil ihrer Nachfolger auf welche Aktion entfällt."""
    df = pd.DataFrame([(a, b, n) for (a, b), n in paare.items()], columns=["von", "nach", "n"])
    df["anteil"] = df["n"] / df.groupby("von")["n"].transform("sum")
    return df.sort_values(["von", "anteil"], ascending=[True, False]).reset_index(drop=True)


def mermaid(paare: Counter, min_anteil: float = 0.1) -> str:
    """Flussdiagramm mit den häufigen Übergängen; Beschriftung = Anteil am Ausgang."""
    df = anteile(paare)
    df = df[df["anteil"] >= min_anteil]
    knoten = sorted(set(df["von"]) | set(df["nach"]))
    ids = {k: f"n{i}" for i, k in enumerate(knoten)}
    zeilen = ["flowchart LR"]
    for k in knoten:
        form = f'(["{k}"])' if k in (START, ENDE) else f'["{k}"]'
        zeilen.append(f"    {ids[k]}{form}")
    for _, r in df.iterrows():
        zeilen.append(f"    {ids[r['von']]} -->|{r['anteil']:.0%}| {ids[r['nach']]}")
    return "\n".join(zeilen)
