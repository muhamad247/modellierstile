"""Vom Ereignislog zu Phasen und Kennzahlen je Sitzung.

Die Phasen folgen der Idee aus der Forschung zum „Process of Process Modeling“:
Eine längere Pause ohne Aktion gilt als Verstehen (die Person liest oder denkt nach),
Abschnitte mit überwiegend neuen oder gelöschten Elementen als Modellieren,
Abschnitte mit überwiegend Verschieben und Umbenennen als Abstimmen.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from modellierstile.simulation import (
    KANTE,
    KNOTEN,
    LOESCHEN,
    START,
    UMBENENNEN,
    VERSCHIEBEN,
)

PAUSE_SCHWELLE_S = 15.0
ANLEGEN = {KNOTEN, KANTE}

MERKMALE = [
    "aktionen_pro_min",
    "anteil_verstehen",
    "median_pause_s",
    "blockgroesse",
    "loeschquote",
    "anteil_layout",
    "layout_am_ende",
]


def phasen(sitzung: pd.DataFrame, schwelle: float = PAUSE_SCHWELLE_S) -> pd.DataFrame:
    """Phasen einer Sitzung: Verstehen, Modellieren oder Abstimmen, mit Beginn und Ende."""
    s = sitzung.sort_values("zeitpunkt").reset_index(drop=True)
    luecke = s["zeitpunkt"].diff().dt.total_seconds().fillna(0)
    zeilen = []
    abschnitt: list[str] = []
    beginn = s.loc[0, "zeitpunkt"]

    def abschnitt_abschliessen(ende: pd.Timestamp) -> None:
        if not abschnitt:
            return
        anlegen = sum(a in ANLEGEN or a == LOESCHEN for a in abschnitt)
        art = "Modellieren" if anlegen >= len(abschnitt) / 2 else "Abstimmen"
        zeilen.append((art, beginn, ende, len(abschnitt)))

    for i in range(1, len(s)):
        if luecke[i] >= schwelle:
            abschnitt_abschliessen(s.loc[i - 1, "zeitpunkt"])
            zeilen.append(("Verstehen", s.loc[i - 1, "zeitpunkt"], s.loc[i, "zeitpunkt"], 0))
            abschnitt = []
            beginn = s.loc[i, "zeitpunkt"]
        abschnitt.append(s.loc[i, "aktion"])
    abschnitt_abschliessen(s.loc[len(s) - 1, "zeitpunkt"])
    return pd.DataFrame(zeilen, columns=["phase", "beginn", "ende", "aktionen"])


def merkmale_sitzung(sitzung: pd.DataFrame, schwelle: float = PAUSE_SCHWELLE_S) -> dict:
    s = sitzung.sort_values("zeitpunkt").reset_index(drop=True)
    aktionen = s.loc[s["aktion"] != START, "aktion"].reset_index(drop=True)
    luecke = s["zeitpunkt"].diff().dt.total_seconds().dropna()
    dauer_s = (s["zeitpunkt"].iloc[-1] - s["zeitpunkt"].iloc[0]).total_seconds()
    pausen = luecke[luecke >= schwelle]
    angelegt = int(aktionen.isin(ANLEGEN).sum())
    verschoben = aktionen == VERSCHIEBEN
    letztes_anlegen = aktionen[aktionen.isin(ANLEGEN)].index.max()
    layout = verschoben | (aktionen == UMBENENNEN)
    return {
        "dauer_min": dauer_s / 60,
        "aktionen": len(aktionen),
        "aktionen_pro_min": len(aktionen) / (dauer_s / 60),
        "anteil_verstehen": pausen.sum() / dauer_s,
        "median_pause_s": float(pausen.median()) if len(pausen) else 0.0,
        # neue Elemente je Denkpause: wie groß die Stücke sind, in denen modelliert wird
        "blockgroesse": angelegt / max(len(pausen), 1),
        "loeschquote": int((aktionen == LOESCHEN).sum()) / max(angelegt, 1),
        "anteil_layout": float(layout.mean()),
        # welcher Teil des Layouts erst am Schluss passiert, nachdem alles angelegt ist
        "layout_am_ende": float(layout[letztes_anlegen + 1 :].sum() / max(layout.sum(), 1)),
    }


def merkmale(log: pd.DataFrame, schwelle: float = PAUSE_SCHWELLE_S) -> pd.DataFrame:
    """Eine Zeile je Sitzung."""
    zeilen = {
        sitzung: merkmale_sitzung(gruppe, schwelle)
        for sitzung, gruppe in log.groupby("sitzung", sort=True)
    }
    return pd.DataFrame.from_dict(zeilen, orient="index").rename_axis("sitzung")


def elemente_im_zeitverlauf(sitzung: pd.DataFrame) -> pd.DataFrame:
    """Zahl der Elemente im Modell nach jeder Aktion, für das Phasendiagramm."""
    s = sitzung.sort_values("zeitpunkt").reset_index(drop=True)
    schritt = np.select([s["aktion"].isin(ANLEGEN), s["aktion"] == LOESCHEN], [1, -1], default=0)
    minuten = (s["zeitpunkt"] - s["zeitpunkt"].iloc[0]).dt.total_seconds() / 60
    return pd.DataFrame({"minute": minuten, "elemente": np.cumsum(schritt), "aktion": s["aktion"]})
