# 07_creer_contre_indications.py
# Table de contre-indications / vigilances, à partir de la reco HAS opioïdes (mars 2022).
# Chaque ligne : un contexte patient + une classe à risque + le niveau + l'alerte + la source.

import pandas as pd
from pathlib import Path

BASE = Path(r"C:\Users\Thierry\Desktop\Demoday")
DATA = BASE / "data"

contre_indications = [
    # --- Opioïdes + dépresseurs du SNC : risque de dépression respiratoire (§1.2.3.3) ---
    {"contexte_patient": "opioides", "classe_a_risque": "Anxiolytique (benzodiazépine)",
     "niveau": "Vigilance élevée",
     "alerte": "L'association opioïdes + benzodiazépines majore le risque de dépression respiratoire (pronostic vital). Association à éviter ou sous surveillance étroite.",
     "source": "HAS, Bon usage des opioïdes, mars 2022, §1.2.3.3"},

    {"contexte_patient": "opioides", "classe_a_risque": "Gabapentinoïde (prégabaline)",
     "niveau": "Vigilance élevée",
     "alerte": "L'association opioïdes + gabapentinoïdes (prégabaline) augmente le risque de dépression respiratoire.",
     "source": "HAS, Bon usage des opioïdes, mars 2022, §1.2.3.3"},

    {"contexte_patient": "opioides", "classe_a_risque": "Antidépresseur (tricyclique)",
     "niveau": "Vigilance",
     "alerte": "Les antidépresseurs tricycliques sont dépresseurs du SNC : prudence en association avec les opioïdes (risque respiratoire).",
     "source": "HAS, Bon usage des opioïdes, mars 2022, §3.1.2 / instauration MSO"},

    # --- Méthadone + allongement du QT (§1.2.3.3) ---
    {"contexte_patient": "opioides", "classe_a_risque": "Anxiolytique (antihistaminique)",
     "niveau": "Vigilance",
     "alerte": "Hydroxyzine + méthadone : risque d'allongement du QT / troubles du rythme. Prudence.",
     "source": "HAS, Bon usage des opioïdes, mars 2022, §1.2.3.3"},

    {"contexte_patient": "opioides", "classe_a_risque": "Antidépresseur (ISRS)",
     "niveau": "Vigilance ciblée",
     "alerte": "Escitalopram + méthadone : risque d'allongement du QT. Prudence (concerne surtout l'escitalopram).",
     "source": "HAS, Bon usage des opioïdes, mars 2022, §1.2.3.3"},

    # --- Alcool + opioïdes (rappel utile, §1.2.3.3) ---
    {"contexte_patient": "alcool", "classe_a_risque": "Anxiolytique (benzodiazépine)",
     "niveau": "Vigilance élevée",
     "alerte": "Alcool + benzodiazépines : majoration de la dépression du SNC. Association déconseillée.",
     "source": "HAS, Bon usage des opioïdes, mars 2022, §1.2.3.3 (principe dépresseurs SNC)"},
]

df = pd.DataFrame(contre_indications)
sortie = DATA / "contre_indications.csv"
df.to_csv(sortie, index=False, encoding="utf-8-sig")
print(f"✅ Table de contre-indications créée : {sortie}")
print(f"   {len(df)} règles.")
print("\nAperçu :")
print(df.to_string())