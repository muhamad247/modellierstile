"""Komplette Analyse: Kennzahlen, Clustering, Prüfung gegen die wahren Stile, Grafiken.

python analyse.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kruskal
from sklearn.metrics import adjusted_rand_score

from modellierstile import cluster, grafiken, prozess
from modellierstile.merkmale import MERKMALE, merkmale
from modellierstile.simulation import lade

ERGEBNISSE = Path("ergebnisse")
BILDER = Path("docs/bilder")
K = 3
KURZ = {
    "Zügig und linear": "zuegig",
    "Ausprobieren und umbauen": "ausprobieren",
    "Erst denken, dann modellieren": "erst_denken",
}


def main() -> None:
    ERGEBNISSE.mkdir(exist_ok=True)
    BILDER.mkdir(parents=True, exist_ok=True)
    log, sitzungen = lade()
    m = merkmale(log)
    x = cluster.matrix(m)

    sil = cluster.silhouette_je_k(x)
    sil.round(3).to_csv(ERGEBNISSE / "silhouette.csv")
    print("Silhouette je Clusterzahl:", sil.round(3).to_dict())

    labels = cluster.kmeans(x, K)
    namen = cluster.benennen(cluster.profile(m, labels))
    m["cluster"] = [namen[c] for c in labels]
    reihenfolge = [namen[c] for c in sorted(namen)]
    farbe = dict(zip(reihenfolge, grafiken.FARBEN))

    wahr = sitzungen.set_index("sitzung").loc[m.index]
    print(f"ARI k-Means gegen wahre Stile: {adjusted_rand_score(wahr['stil'], labels):.3f}")
    print(
        f"ARI Ward gegen wahre Stile:    {adjusted_rand_score(wahr['stil'], cluster.ward(x, K)):.3f}"
    )
    print(f"ARI k-Means gegen Ward:        {adjusted_rand_score(labels, cluster.ward(x, K)):.3f}")
    print(f"Stabilität (80-%-Stichproben): {cluster.stabilitaet(x, K):.3f}")
    print(pd.crosstab(wahr["stil"], m["cluster"]).to_string())

    profil = m.groupby("cluster")[MERKMALE + ["dauer_min"]].median().loc[reihenfolge]
    profil.insert(0, "sitzungen", m["cluster"].value_counts())
    profil["fehler_mittel"] = wahr.groupby(m["cluster"])["fehler"].mean()
    profil.round(3).to_csv(ERGEBNISSE / "clusterprofile.csv")
    print(profil.round(2).T.to_string())

    gruppen = [wahr.loc[m["cluster"] == n, "fehler"] for n in reihenfolge]
    print(
        f"Kruskal-Wallis Fehler je Cluster: H = {kruskal(*gruppen).statistic:.1f}, "
        f"p = {kruskal(*gruppen).pvalue:.1e}"
    )
    m.round(4).to_csv(ERGEBNISSE / "merkmale.csv")

    z = pd.DataFrame(x, index=m.index, columns=MERKMALE).groupby(m["cluster"]).median()
    grafiken.profile(z.loc[reihenfolge], farbe, BILDER / "clusterprofile.png")

    # typische Sitzung je Cluster: die mit dem kleinsten Abstand zum Clusterzentrum
    beispiele = {}
    for name in reihenfolge:
        teil = x[m["cluster"].to_numpy() == name]
        abstand = np.linalg.norm(teil - teil.mean(axis=0), axis=1)
        beispiele[name] = m.index[m["cluster"] == name][abstand.argmin()]
    grafiken.phasendiagramm(log, beispiele, farbe, BILDER / "phasendiagramm.png")

    log["cluster"] = log["sitzung"].map(m["cluster"])
    with open(ERGEBNISSE / "prozessgraphen.md", "w", encoding="utf-8") as f:
        for name in reihenfolge:
            paare = prozess.directly_follows(log[log["cluster"] == name])
            f.write(f"## {name}\n\n```mermaid\n{prozess.mermaid(paare, 0.2)}\n```\n\n")
            prozess.anteile(paare).round(3).to_csv(
                ERGEBNISSE / f"uebergaenge_{KURZ[name]}.csv", index=False
            )
    print(f"Ergebnisse in {ERGEBNISSE}/, Grafiken in {BILDER}/")


if __name__ == "__main__":
    main()
