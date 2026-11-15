import numpy as np
import pytest
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from modellierstile import cluster

NAME_ZU_STIL = {
    "Zügig und linear": "zügig",
    "Ausprobieren und umbauen": "ausprobierend",
    "Erst denken, dann modellieren": "nachdenklich",
}


def _wahr(simuliert, kennzahlen):
    return simuliert[1].set_index("sitzung").loc[kennzahlen.index, "stil"]


def test_silhouette_waehlt_drei_cluster(kennzahlen):
    sil = cluster.silhouette_je_k(cluster.matrix(kennzahlen))
    assert sil.idxmax() == 3


def test_clustering_findet_die_stile_weitgehend(simuliert, kennzahlen):
    x = cluster.matrix(kennzahlen)
    wahr = _wahr(simuliert, kennzahlen)
    assert adjusted_rand_score(wahr, cluster.kmeans(x, 3)) > 0.7
    assert adjusted_rand_score(wahr, cluster.ward(x, 3)) > 0.6
    assert cluster.stabilitaet(x, 3, wiederholungen=20) > 0.9


def test_namen_passen_zum_haeufigsten_wahren_stil(simuliert, kennzahlen):
    x = cluster.matrix(kennzahlen)
    labels = cluster.kmeans(x, 3)
    namen = cluster.benennen(cluster.profile(kennzahlen, labels))
    assert sorted(namen.values()) == sorted(NAME_ZU_STIL)
    wahr = _wahr(simuliert, kennzahlen).to_numpy()
    for c, name in namen.items():
        haeufigster = pd.Series(wahr[labels == c]).mode()[0]
        assert NAME_ZU_STIL[name] == haeufigster


def test_matrix_ist_standardisiert(kennzahlen):
    x = cluster.matrix(kennzahlen)
    assert abs(x.mean(axis=0)).max() < 1e-9
    assert abs(x.std(axis=0) - 1).max() < 1e-9


def test_matrix_lehnt_fehlende_werte_ab(kennzahlen):
    unvollstaendig = kennzahlen.copy()
    unvollstaendig.loc[unvollstaendig.index[0], "median_pause_s"] = np.nan
    with pytest.raises(ValueError, match="endlich und vollständig"):
        cluster.matrix(unvollstaendig)


def test_matrix_lehnt_unendliche_werte_ab(kennzahlen):
    ungueltig = kennzahlen.copy()
    ungueltig.loc[ungueltig.index[0], "blockgroesse"] = np.inf
    with pytest.raises(ValueError, match="endlich und vollständig"):
        cluster.matrix(ungueltig)
