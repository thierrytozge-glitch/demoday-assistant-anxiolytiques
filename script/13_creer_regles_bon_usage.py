# 13_creer_regles_bon_usage.py
# Table des règles de bon usage des benzodiazépines.
# Source : ANSM, Dossier thématique "Bon usage des benzodiazépines"
#          (publié 08/04/2025, mis à jour 03/09/2025)
#          https://ansm.sante.fr/dossiers-thematiques/bon-usage-des-benzodiazepines
#
# À VÉRIFIER contre la source avant la soutenance.

import pandas as pd
from pathlib import Path

BASE = Path(r"C:\Users\Thierry\Desktop\Demoday")
DATA = BASE / "data"

SOURCE = "ANSM, Bon usage des benzodiazépines, mis à jour 03/09/2025"

regles = [
    # --- Durée de traitement ---
    {"contexte": "toujours", "classe_concernee": "Anxiolytique (benzodiazépine)",
     "niveau": "Règle de bon usage",
     "regle": "Durée maximale : 12 semaines dans l'anxiété. Le traitement doit être le plus court possible et réévalué régulièrement.",
     "source": SOURCE},

    {"contexte": "toujours", "classe_concernee": "Anxiolytique (benzodiazépine)",
     "niveau": "Règle de bon usage",
     "regle": "L'arrêt doit être programmé dès l'initiation du traitement, avec une diminution progressive des doses (risque d'effet rebond en cas d'arrêt brutal).",
     "source": SOURCE},

    {"contexte": "toujours", "classe_concernee": "Anxiolytique (benzodiazépine)",
     "niveau": "Règle de bon usage",
     "regle": "Débuter par les doses les plus faibles adaptées à la situation clinique. Ne pas dépasser la dose maximale recommandée.",
     "source": SOURCE},

    # --- Dépendance / tolérance ---
    {"contexte": "toujours", "classe_concernee": "Anxiolytique (benzodiazépine)",
     "niveau": "Vigilance",
     "regle": "Risque de dépendance physique et psychique, et de tolérance (nécessité d'augmenter les doses). Le risque augmente avec la dose et la durée.",
     "source": SOURCE},

    # --- Cumul de benzodiazépines ---
    {"contexte": "toujours", "classe_concernee": "Anxiolytique (benzodiazépine)",
     "niveau": "Vigilance élevée",
     "regle": "Il est recommandé de NE PAS associer plusieurs benzodiazépines : leurs effets indésirables s'additionnent.",
     "source": SOURCE},

    # --- Aptitude à conduire ---
    {"contexte": "toujours", "classe_concernee": "Anxiolytique (benzodiazépine)",
     "niveau": "Vigilance",
     "regle": "Diminution forte de la capacité à conduire un véhicule ou à utiliser des machines. Troubles de la mémoire, somnolence, réactions paradoxales possibles.",
     "source": SOURCE},

    # --- DÉPRESSION : contre-indication majeure ---
    {"contexte": "depression", "classe_concernee": "Anxiolytique (benzodiazépine)",
     "niveau": "Vigilance élevée",
     "regle": "En cas de dépression, les benzodiazépines ne doivent PAS être prescrites seules (sans psychothérapie et/ou antidépresseur) : elles masquent les symptômes et laissent la dépression évoluer, avec persistance voire augmentation du risque suicidaire.",
     "source": SOURCE},

    # --- PERSONNE ÂGÉE 65+ ---
    {"contexte": "personne_agee", "classe_concernee": "Anxiolytique (benzodiazépine)",
     "niveau": "Vigilance élevée",
     "regle": "Chez la personne de 65 ans et plus : éviter d'initier un traitement par benzodiazépine.",
     "source": SOURCE},

    {"contexte": "personne_agee", "classe_concernee": "Anxiolytique (benzodiazépine)",
     "niveau": "Vigilance élevée",
     "regle": "Si un traitement est nécessaire chez la personne âgée : privilégier une benzodiazépine à demi-vie courte (clotiazépam, oxazépam) et DIVISER LA POSOLOGIE PAR DEUX par rapport à un adulte plus jeune.",
     "source": SOURCE},

    {"contexte": "personne_agee", "classe_concernee": "Anxiolytique (benzodiazépine)",
     "niveau": "Vigilance élevée",
     "regle": "Sensibilité accrue de la personne âgée aux effets indésirables : risque de chute, perturbation cognitive, réaction paradoxale.",
     "source": SOURCE},

    # --- GROSSESSE ---
    {"contexte": "grossesse", "classe_concernee": "Anxiolytique (benzodiazépine)",
     "niveau": "Vigilance élevée",
     "regle": "Benzodiazépines déconseillées pendant la grossesse (risques pour l'enfant). Informer tous les professionnels de santé consultés.",
     "source": "ANSM, brochure Anxiété et médicaments (2025)"},

    # --- Opioïdes : confirmation de la source ANSM ---
    {"contexte": "opioides", "classe_concernee": "Anxiolytique (benzodiazépine)",
     "niveau": "Vigilance élevée",
     "regle": "En cas de surdosage ou d'association à un opioïde (morphine, tramadol, codéine), la somnolence induite par les benzodiazépines peut aller jusqu'au COMA.",
     "source": SOURCE},
]

# --- Demi-vies (utile pour la personne âgée) ---
demi_vies = [
    {"substance": "clotiazépam", "demi_vie": "courte (< 10 h)"},
    {"substance": "oxazépam", "demi_vie": "courte (< 10 h)"},
    {"substance": "alprazolam", "demi_vie": "intermédiaire (10-24 h)"},
    {"substance": "bromazépam", "demi_vie": "intermédiaire (10-24 h)"},
    {"substance": "lorazépam", "demi_vie": "intermédiaire (10-24 h)"},
    {"substance": "clobazam", "demi_vie": "longue (> 24 h)"},
    {"substance": "diazépam", "demi_vie": "longue (> 24 h)"},
    {"substance": "loflazépate d'éthyle", "demi_vie": "longue (> 24 h)"},
]

df_regles = pd.DataFrame(regles)
df_demi = pd.DataFrame(demi_vies)

s1 = DATA / "regles_bon_usage.csv"
s2 = DATA / "demi_vies_benzodiazepines.csv"
df_regles.to_csv(s1, index=False, encoding="utf-8-sig")
df_demi.to_csv(s2, index=False, encoding="utf-8-sig")

print(f"✅ Règles de bon usage : {s1}  ({len(df_regles)} règles)")
print(f"✅ Demi-vies : {s2}  ({len(df_demi)} molécules)")
print("\n--- Règles par contexte ---")
for ctx, grp in df_regles.groupby("contexte"):
    print(f"\n[{ctx}] ({len(grp)} règle(s))")
    for _, r in grp.iterrows():
        print(f"  • [{r['niveau']}] {r['regle'][:90]}...")