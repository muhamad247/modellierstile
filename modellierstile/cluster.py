"""Stile finden: Kennzahlen standardisieren, clustern, Ergebnis prüfen."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from modellierstile.merkmale import MERKMALE

# rechtsschief: Pausenlänge und Blockgröße werden vor dem Standardisieren logarithmiert
LOG_MERKMALE = ["median_pause_s", "blockgroesse", "loeschquote"]


def matrix(m: pd.DataFrame) -> np.ndarray:
    x = m[MERKMALE].copy()
    if not np.isfinite(x.to_numpy(dtype=float)).all():
        raise ValueError("Cluster-Merkmale müssen endlich und vollständig sein")
    for spalte in LOG_MERKMALE:
        x[spalte] = np.log1p(x[spalte])
    if not np.isfinite(x.to_numpy(dtype=float)).all():
        raise ValueError("Logarithmierte Cluster-Merkmale müssen endlich sein")
    return StandardScaler().fit_transform(x)


def kmeans(x: np.ndarray, k: int, seed: int = 0) -> np.ndarray:
    return KMeans(n_clusters=k, n_init=20, random_state=seed).fit_predict(x)


def ward(x: np.ndarray, k: int) -> np.ndarray:
    return AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(x)


def silhouette_je_k(x: np.ndarray, ks: range = range(2, 7)) -> pd.Series:
    """Wie klar die Cluster getrennt sind, für jede Clusterzahl; höher ist besser."""
    return pd.Series(
        {k: silhouette_score(x, kmeans(x, k)) for k in ks}, name="silhouette"
    ).rename_axis("k")


def stabilitaet(x: np.ndarray, k: int, wiederholungen: int = 50, seed: int = 1) -> float:
    """Mittlerer ARI zwischen dem Clustering aller Daten und dem auf 80-%-Stichproben."""
    rng = np.random.default_rng(seed)
    voll = kmeans(x, k)
    werte = []
    for _ in range(wiederholungen):
        idx = rng.choice(len(x), size=int(0.8 * len(x)), replace=False)
        werte.append(adjusted_rand_score(voll[idx], kmeans(x[idx], k)))
    return float(np.mean(werte))


def profile(m: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
    """Median jeder Kennzahl je Cluster, plus Größe."""
    p = m[MERKMALE].groupby(labels).median()
    p.insert(0, "sitzungen", pd.Series(labels).value_counts().sort_index())
    return p.rename_axis("cluster")


def benennen(p: pd.DataFrame) -> dict[int, str]:
    """Namen aus dem Profil: am meisten Löschen, am längsten Nachdenken, der Rest."""
    namen: dict[int, str] = {}
    rest = [int(c) for c in p.index]
    probieren = int(p.loc[rest, "loeschquote"].idxmax())
    namen[probieren] = "Ausprobieren und umbauen"
    rest.remove(probieren)
    denken = int(p.loc[rest, "median_pause_s"].idxmax())
    namen[denken] = "Erst denken, dann modellieren"
    rest.remove(denken)
    for i, c in enumerate(rest):
        namen[c] = "Zügig und linear" if i == 0 else f"Cluster {c}"
    return namen
