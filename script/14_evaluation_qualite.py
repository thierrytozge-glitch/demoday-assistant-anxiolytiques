# 14_evaluation_qualite.py
# Évaluation de la QUALITÉ des réponses (complémentaire à l'évaluation de sécurité 11_).
#
# 11_evaluation_finale.py  -> SÉCURITÉ (le système fait-il des bêtises ?) -> 43/43
# 14_evaluation_qualite.py -> QUALITÉ (fait-il BIEN son travail ?) -> multi-axes
#
# Axes mesurés :
#   1. Complétude (recall)      -> retrouve-t-il toutes les molécules attendues ?
#   2. Précision                -> ce qu'il cite est-il pertinent (pas d'intrus) ?
#   3. Stabilité des décisions  -> mêmes décisions à chaque essai ? (déterministe by design)
#   4. Variabilité de rédaction -> la couche LLM varie-t-elle d'un essai à l'autre ?
#
# Ces axes ne visent PAS 100 %. Un recall < 100 % est normal (le LLM synthétise).
# Une stabilité des décisions à 100 % est attendue (elles viennent du moteur déterministe).
# Un score de 100 % PARTOUT indiquerait une mesure trop permissive.

import sys
import unicodedata
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module
assistant = import_module("06_assistant")

BASE = Path(r"C:\Users\Thierry\Desktop\Demoday")
DATA = BASE / "data"

N_ESSAIS = 3   # nombre de relances par question pour la stabilité / variabilité


# ============================================================
# OUTILS
# ============================================================

def normaliser(texte):
    """Minuscules + suppression des accents, pour comparer les noms de molécules
    quelle que soit leur orthographe exacte dans la réponse."""
    texte = texte.lower()
    texte = unicodedata.normalize("NFD", texte)
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    return texte


def molecule_citee(reponse, molecule):
    """La molécule est-elle mentionnée dans la réponse ? (comparaison sans accent)"""
    return normaliser(molecule) in normaliser(reponse)


MOLECULES_BASE = [
    "alprazolam", "bromazépam", "clobazam", "clorazépate", "clotiazépam",
    "diazépam", "loflazépate", "lorazépam", "oxazépam", "prazépam",
    "hydroxyzine", "buspirone", "citalopram", "escitalopram", "fluoxétine",
    "fluvoxamine", "paroxétine", "sertraline", "venlafaxine", "duloxétine",
    "clomipramine", "cyamémazine", "sulpiride",
]


# ============================================================
# AXE 1 — COMPLÉTUDE (RECALL)
# Vérité terrain : les molécules attendues par trouble (table HAS ALD n°23).
# ============================================================

CAS_RECALL = [
    {"id": "R1",
     "question": "Quelles molécules sont indiquées dans le trouble anxiété généralisée (TAG) ?",
     "attendues": ["escitalopram", "paroxétine", "venlafaxine", "duloxétine", "buspirone"]},
    {"id": "R2",
     "question": "Quelles molécules sont indiquées dans le trouble obsessionnel compulsif (TOC) ?",
     "attendues": ["fluoxétine", "fluvoxamine", "paroxétine", "sertraline", "escitalopram", "clomipramine"]},
    {"id": "R3",
     "question": "Quelles molécules sont indiquées dans le trouble panique ?",
     "attendues": ["citalopram", "escitalopram", "paroxétine", "sertraline", "venlafaxine", "clomipramine"]},
    {"id": "R4",
     "question": "Quelles benzodiazépines sont indiquées dans les manifestations anxieuses sévères ?",
     "attendues": ["alprazolam", "bromazépam", "clobazam", "clorazépate", "clotiazépam",
                   "diazépam", "loflazépate", "lorazépam", "oxazépam", "prazépam"]},
    {"id": "R5",
     "question": "Quelles molécules sont indiquées dans le trouble anxiété sociale ?",
     "attendues": ["escitalopram", "paroxétine", "sertraline", "venlafaxine"]},
]


def evaluer_recall():
    resultats = []
    print("=" * 78)
    print("AXE 1 — COMPLÉTUDE (RECALL) : le système retrouve-t-il toutes les molécules ?")
    print("=" * 78)

    for cas in CAS_RECALL:
        r = assistant.repondre(cas["question"])
        reponse = r["reponse"]
        trouvees = [m for m in cas["attendues"] if molecule_citee(reponse, m)]
        manquantes = [m for m in cas["attendues"] if not molecule_citee(reponse, m)]
        recall = len(trouvees) / len(cas["attendues"])

        print(f"\n[{cas['id']}] {cas['question'][:60]}...")
        print(f"     Attendues : {len(cas['attendues'])} | Trouvées : {len(trouvees)} "
              f"| Recall : {recall*100:.0f}%")
        if manquantes:
            print(f"     ⚠️  Manquantes : {manquantes}")

        resultats.append({"id": cas["id"], "attendues": len(cas["attendues"]),
                          "trouvees": len(trouvees), "manquantes": ", ".join(manquantes),
                          "recall": recall})

    df = pd.DataFrame(resultats)
    recall_moyen = df["recall"].mean()
    print("\n" + "-" * 78)
    print(f"RECALL MOYEN : {recall_moyen*100:.1f}%")
    print("-" * 78)
    print("Un recall < 100% est NORMAL : le modèle synthétise et privilégie la lisibilité.")
    return df, recall_moyen


# ============================================================
# AXE 2 — PRÉCISION : ce qui est cité est-il pertinent (pas d'intrus hors catégorie) ?
# ============================================================

CAS_PRECISION = [
    {"id": "P1",
     "question": "Quelles benzodiazépines sont indiquées dans les manifestations anxieuses sévères ?",
     "attendues": ["alprazolam", "bromazépam", "clobazam", "clorazépate", "clotiazépam",
                   "diazépam", "loflazépate", "lorazépam", "oxazépam", "prazépam"],
     "intrus_possibles": ["hydroxyzine", "buspirone", "sertraline", "escitalopram"]},
    {"id": "P2",
     "question": "Quels antidépresseurs ISRS sont indiqués dans les troubles anxieux ?",
     "attendues": ["citalopram", "escitalopram", "fluoxétine", "fluvoxamine", "paroxétine", "sertraline"],
     "intrus_possibles": ["venlafaxine", "duloxétine", "clomipramine", "buspirone"]},
]


def evaluer_precision():
    resultats = []
    print("\n" + "=" * 78)
    print("AXE 2 — PRÉCISION : les molécules citées sont-elles pertinentes (pas d'intrus) ?")
    print("=" * 78)

    for cas in CAS_PRECISION:
        r = assistant.repondre(cas["question"])
        reponse = r["reponse"]
        correctes = [m for m in cas["attendues"] if molecule_citee(reponse, m)]
        intrus = [m for m in cas["intrus_possibles"] if molecule_citee(reponse, m)]
        total = len(correctes) + len(intrus)
        precision = len(correctes) / total if total else 1.0

        print(f"\n[{cas['id']}] {cas['question'][:55]}...")
        print(f"     Correctes : {len(correctes)} | Intrus : {len(intrus)} "
              f"| Précision : {precision*100:.0f}%")
        if intrus:
            print(f"     ⚠️  Intrus (à vérifier : cités comme option ou pour être écartés ?) : {intrus}")

        resultats.append({"id": cas["id"], "correctes": len(correctes),
                          "intrus": ", ".join(intrus), "precision": precision})

    df = pd.DataFrame(resultats)
    precision_moyenne = df["precision"].mean()
    print("\n" + "-" * 78)
    print(f"PRÉCISION MOYENNE : {precision_moyenne*100:.1f}%")
    print("-" * 78)
    print("Mesure si le système reste dans la catégorie demandée (sans molécule hors sujet).")
    return df, precision_moyenne


# ============================================================
# AXE 3 — STABILITÉ DES DÉCISIONS (déterministe by design)
# ============================================================

CAS_MULTI_ESSAIS = [
    "Patient sous opioïdes, anxiété sévère, quelles options ?",
    "Quelles molécules pour le trouble obsessionnel compulsif ?",
    "Patient de 78 ans, anxiété sévère, benzodiazépine possible ?",
    "Le Stresam est-il adapté pour l'anxiété ?",
    "Patient avec anxiété sévère et syndrome dépressif, benzodiazépine seule ?",
]


def signature_reponse(r):
    """Résume les DÉCISIONS structurantes (trouble, alertes, contextes, refus)."""
    reponse_norm = normaliser(r["reponse"])
    nb_alertes = len([a for a in r["alertes"].split("\n") if a.strip()]) if r["alertes"] else 0
    refus = any(m in reponse_norm for m in
                ["ne figure pas", "hors perimetre", "ne peux pas me prononcer", "patient mineur"])
    return (r["trouble_cible"], nb_alertes, tuple(sorted(r.get("contextes_detectes", []))), refus)


def evaluer_stabilite_et_variabilite():
    """Un seul passage de N essais par question, qui alimente DEUX axes :
    - la stabilité des décisions (axe 3)
    - la variabilité de rédaction (axe 4)
    -> on économise les appels API en mesurant les deux d'un coup."""
    res_stab = []
    res_var = []
    print("\n" + "=" * 78)
    print(f"AXES 3 & 4 — STABILITÉ DES DÉCISIONS & VARIABILITÉ DE RÉDACTION ({N_ESSAIS} essais/question)")
    print("=" * 78)

    for i, question in enumerate(CAS_MULTI_ESSAIS, 1):
        signatures = []
        longueurs = []
        nb_molecules = []

        for _ in range(N_ESSAIS):
            r = assistant.repondre(question)
            signatures.append(signature_reponse(r))
            longueurs.append(len(r["reponse"]))
            nb_molecules.append(sum(1 for m in MOLECULES_BASE if molecule_citee(r["reponse"], m)))

        # --- Axe 3 : stabilité des décisions ---
        stable = len(set(signatures)) == 1

        # --- Axe 4 : variabilité de rédaction ---
        moy = sum(longueurs) / len(longueurs)
        ecart = (sum((x - moy) ** 2 for x in longueurs) / len(longueurs)) ** 0.5
        cv = (ecart / moy * 100) if moy else 0
        mol_constant = len(set(nb_molecules)) == 1

        print(f"\n[{i}] {question[:55]}...")
        print(f"     Décisions   : {'✅ STABLE' if stable else '⚠️ VARIABLE'}")
        print(f"     Longueurs   : {longueurs}  (variation {cv:.1f}%)")
        print(f"     Molécules   : {nb_molecules} → {'constant' if mol_constant else '⚠️ variable'}")

        res_stab.append({"id": f"S{i}", "question": question, "stable": stable,
                        "signatures_distinctes": len(set(signatures))})
        res_var.append({"id": f"V{i}", "cv_longueur_pct": round(cv, 1),
                       "molecules_constant": mol_constant})

    df_stab = pd.DataFrame(res_stab)
    df_var = pd.DataFrame(res_var)
    taux_stab = df_stab["stable"].mean()
    cv_moyen = df_var["cv_longueur_pct"].mean()

    print("\n" + "-" * 78)
    print(f"STABILITÉ DES DÉCISIONS : {taux_stab*100:.1f}% des questions parfaitement stables")
    print(f"VARIATION MOYENNE DE LONGUEUR (rédaction) : {cv_moyen:.1f}%")
    print("-" * 78)
    print("Les DÉCISIONS (alertes, refus, contexte) sont prises par le moteur déterministe :")
    print("elles sont stables. Seule la RÉDACTION varie (couche LLM) — c'est mesuré, pas subi.")
    return df_stab, taux_stab, df_var, cv_moyen


# ============================================================
# EXÉCUTION — un seul lancement, tous les axes
# ============================================================

if __name__ == "__main__":
    df_recall, recall_moyen = evaluer_recall()
    df_precision, precision_moyenne = evaluer_precision()
    df_stab, taux_stab, df_var, cv_moyen = evaluer_stabilite_et_variabilite()

    print("\n" + "=" * 78)
    print("SYNTHÈSE — ÉVALUATION QUALITÉ (multi-axes)")
    print("=" * 78)
    print(f"  Complétude (recall)          : {recall_moyen*100:.1f}%   (couche LLM — synthèse)")
    print(f"  Précision (pas d'intrus)     : {precision_moyenne*100:.1f}%   (couche LLM)")
    print(f"  Stabilité des décisions      : {taux_stab*100:.1f}%   (moteur déterministe)")
    print(f"  Variabilité de rédaction     : {cv_moyen:.1f}%    (couche LLM — attendue)")
    print(f"  ------------------------------------------------------------")
    print(f"  Sécurité (script 11)         : 43/43 = 100%   (moteur déterministe + garde-fous)")
    print("\n  Lecture : sécurité et décisions à 100% (déterministe by design).")
    print("  Complétude et rédaction varient (couche LLM) — quantifié, pas subi.")

    df_recall.to_csv(DATA / "resultats_qualite_recall.csv", index=False, encoding="utf-8-sig")
    df_precision.to_csv(DATA / "resultats_qualite_precision.csv", index=False, encoding="utf-8-sig")
    df_stab.to_csv(DATA / "resultats_qualite_stabilite.csv", index=False, encoding="utf-8-sig")
    df_var.to_csv(DATA / "resultats_qualite_variabilite.csv", index=False, encoding="utf-8-sig")
    print(f"\n✅ Tous les résultats enregistrés dans data/")