"""Zwei Grafiken für die README: Phasendiagramm je Stil und Profil der Cluster."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from modellierstile.merkmale import MERKMALE, elemente_im_zeitverlauf, phasen  # noqa: E402
from modellierstile.simulation import UMBENENNEN, VERSCHIEBEN  # noqa: E402

FARBEN = ["#2a78d6", "#eb6834", "#1baf7a"]  # Kategorienfarben, auf Farbsehschwäche geprüft
FLAECHE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
RASTER = "#e6e5e1"
PAUSE = "#ebeae6"

BESCHRIFTUNG = {
    "aktionen_pro_min": "Aktionen pro Minute",
    "anteil_verstehen": "Zeitanteil Nachdenken",
    "median_pause_s": "Länge einer Denkpause",
    "blockgroesse": "Neue Elemente je Denkpause",
    "loeschquote": "Löschen je neues Element",
    "anteil_layout": "Anteil Layout-Aktionen",
    "layout_am_ende": "Layout erst am Schluss",
}


def _stil(ax: plt.Axes) -> None:
    ax.set_facecolor(FLAECHE)
    for seite in ("top", "right"):
        ax.spines[seite].set_visible(False)
    for seite in ("left", "bottom"):
        ax.spines[seite].set_color(RASTER)
    ax.tick_params(colors=TEXT_2, labelsize=9, length=0)
    ax.grid(color=RASTER, linewidth=1)
    ax.set_axisbelow(True)


def phasendiagramm(
    log: pd.DataFrame, beispiele: dict[str, str], farbe: dict[str, str], ziel: Path
) -> None:
    """Elemente im Modell über die Zeit; graue Bänder sind Denkpausen, Striche unten Layout."""
    fig, achsen = plt.subplots(
        1, len(beispiele), figsize=(11, 3.6), sharex=True, sharey=True, facecolor=FLAECHE
    )
    laengste = 0.0
    for ax, (name, sitzung) in zip(achsen, beispiele.items()):
        s = log[log["sitzung"] == sitzung]
        verlauf = elemente_im_zeitverlauf(s)
        beginn = s["zeitpunkt"].min()
        _stil(ax)
        ax.grid(axis="x", visible=False)
        for _, p in phasen(s).query("phase == 'Verstehen'").iterrows():
            von = (p["beginn"] - beginn).total_seconds() / 60
            bis = (p["ende"] - beginn).total_seconds() / 60
            ax.axvspan(von, bis, color=PAUSE, linewidth=0, zorder=0)
        ax.step(
            verlauf["minute"],
            verlauf["elemente"],
            where="post",
            color=farbe[name],
            linewidth=2,
            solid_capstyle="round",
        )
        layout = verlauf[verlauf["aktion"].isin([VERSCHIEBEN, UMBENENNEN])]
        ax.plot(
            layout["minute"],
            np.full(len(layout), -3),
            "|",
            color=farbe[name],
            markersize=8,
            markeredgewidth=1.5,
        )
        ax.set_title(name, loc="left", fontsize=11, color=TEXT, pad=14)
        dauer = verlauf["minute"].iloc[-1]
        ax.text(
            0,
            1.02,
            f"Sitzung {sitzung}, {dauer:.0f} Minuten",
            transform=ax.transAxes,
            fontsize=9,
            color=TEXT_2,
        )
        ax.set_xlabel("Minuten seit Start", fontsize=9, color=TEXT_2)
        laengste = max(laengste, dauer)
    # gemeinsame Zeitachse, damit man die Dauer der Sitzungen direkt vergleichen kann
    achsen[0].set_xlim(0, laengste * 1.02)
    achsen[0].set_ylim(-6, None)
    achsen[0].set_ylabel("Elemente im Modell", fontsize=9, color=TEXT_2)
    fig.legend(
        handles=[
            Patch(color=PAUSE, label="Denkpause (mind. 15 s ohne Aktion)"),
            Line2D(
                [],
                [],
                color=TEXT_2,
                marker="|",
                linestyle="",
                markersize=8,
                label="Verschieben oder Umbenennen",
            ),
        ],
        loc="lower center",
        ncol=2,
        frameon=False,
        fontsize=9,
        labelcolor=TEXT_2,
        bbox_to_anchor=(0.5, -0.02),
    )
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(ziel, dpi=150, facecolor=FLAECHE)
    plt.close(fig)


def profile(z: pd.DataFrame, farbe: dict[str, str], ziel: Path) -> None:
    """Median der standardisierten Kennzahlen je Cluster; 0 ist der Durchschnitt aller."""
    fig, ax = plt.subplots(figsize=(8, 4.2), facecolor=FLAECHE)
    _stil(ax)
    ax.grid(axis="y", visible=False)
    zeilen = list(reversed(MERKMALE))
    y = np.arange(len(zeilen))
    ax.axvline(0, color="#c9c8c3", linewidth=1, zorder=1)
    for name in z.index:
        werte = z.loc[name, zeilen].to_numpy()
        ax.plot(werte, y, color=farbe[name], linewidth=0, zorder=2)
        ax.scatter(
            werte,
            y,
            s=70,
            color=farbe[name],
            edgecolors=FLAECHE,
            linewidths=2,
            zorder=3,
            label=name,
        )
    ax.set_yticks(y, [BESCHRIFTUNG[m] for m in zeilen], fontsize=9, color=TEXT)
    ax.set_xlabel(
        "Abweichung vom Durchschnitt in Standardabweichungen (Median je Cluster)",
        fontsize=9,
        color=TEXT_2,
    )
    ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.4, 1.0),
        ncol=len(z),
        frameon=False,
        fontsize=9,
        labelcolor=TEXT,
        handletextpad=0.3,
        columnspacing=1.5,
    )
    fig.tight_layout()
    fig.savefig(ziel, dpi=150, facecolor=FLAECHE)
    plt.close(fig)
