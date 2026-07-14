# 03_creer_reference_has.py
# Objectif : créer le fichier de référence "molécule -> trouble anxieux -> indication HAS".
# Source : HAS, ALD n°23 - Actes et prestations sur les troubles anxieux graves (actualisation janvier 2025), section 6.
# NB : ce document liste les médicaments remboursables ayant une AMM ; ce n'est pas une reco de bonne pratique.

import pandas as pd
from pathlib import Path

BASE = Path(r"C:\Users\Thierry\Desktop\Demoday")
DATA = BASE / "data"

# Chaque ligne = une molécule, sa classe, le trouble concerné, et l'indication telle que formulée par la HAS.
# "substance_norm" est la version simple qu'on utilisera pour faire le lien avec le fichier ANSM.
reference = [
    # --- ANXIOLYTIQUES : benzodiazépines (anxiété, usage court) ---
    {"substance_norm": "alprazolam",              "classe": "Anxiolytique (benzodiazépine)", "trouble": "Anxiété",                     "indication_has": "Traitement symptomatique des manifestations anxieuses sévères et/ou invalidantes"},
    {"substance_norm": "bromazépam",              "classe": "Anxiolytique (benzodiazépine)", "trouble": "Anxiété",                     "indication_has": "Traitement symptomatique des manifestations anxieuses sévères et/ou invalidantes"},
    {"substance_norm": "clobazam",                "classe": "Anxiolytique (benzodiazépine)", "trouble": "Anxiété",                     "indication_has": "Traitement symptomatique des manifestations anxieuses sévères et/ou invalidantes"},
    {"substance_norm": "clorazépate dipotassique","classe": "Anxiolytique (benzodiazépine)", "trouble": "Anxiété",                     "indication_has": "Traitement symptomatique des manifestations anxieuses sévères et/ou invalidantes"},
    {"substance_norm": "clotiazépam",             "classe": "Anxiolytique (benzodiazépine)", "trouble": "Anxiété",                     "indication_has": "Traitement symptomatique des manifestations anxieuses sévères et/ou invalidantes"},
    {"substance_norm": "diazépam",                "classe": "Anxiolytique (benzodiazépine)", "trouble": "Anxiété",                     "indication_has": "Traitement symptomatique des manifestations anxieuses sévères et/ou invalidantes"},
    {"substance_norm": "loflazépate d'éthyle",    "classe": "Anxiolytique (benzodiazépine)", "trouble": "Anxiété",                     "indication_has": "Traitement symptomatique des manifestations anxieuses sévères et/ou invalidantes"},
    {"substance_norm": "lorazépam",               "classe": "Anxiolytique (benzodiazépine)", "trouble": "Anxiété",                     "indication_has": "Traitement symptomatique des manifestations anxieuses sévères et/ou invalidantes"},
    {"substance_norm": "oxazépam",                "classe": "Anxiolytique (benzodiazépine)", "trouble": "Anxiété",                     "indication_has": "Traitement symptomatique des manifestations anxieuses sévères et/ou invalidantes"},
    {"substance_norm": "prazépam",                "classe": "Anxiolytique (benzodiazépine)", "trouble": "Anxiété",                     "indication_has": "Traitement symptomatique des manifestations anxieuses sévères et/ou invalidantes"},

    # --- ANXIOLYTIQUES : non-benzodiazépines ---
    {"substance_norm": "hydroxyzine",             "classe": "Anxiolytique (antihistaminique)","trouble": "Anxiété légère",             "indication_has": "Manifestations mineures de l'anxiété chez l'adulte"},
    {"substance_norm": "buspirone",               "classe": "Anxiolytique",                   "trouble": "Anxiété généralisée",        "indication_has": "Traitement de l'anxiété (trouble anxiété généralisée)"},

    # --- ANTIDÉPRESSEURS ISRS ---
    {"substance_norm": "citalopram",              "classe": "Antidépresseur (ISRS)",          "trouble": "Trouble panique",            "indication_has": "Trouble panique avec ou sans agoraphobie"},
    {"substance_norm": "escitalopram",            "classe": "Antidépresseur (ISRS)",          "trouble": "Anxiété généralisée / panique / anxiété sociale", "indication_has": "TAG, trouble panique, trouble anxiété sociale, TOC"},
    {"substance_norm": "fluoxétine",              "classe": "Antidépresseur (ISRS)",          "trouble": "TOC",                        "indication_has": "Troubles obsessionnels compulsifs"},
    {"substance_norm": "fluvoxamine",             "classe": "Antidépresseur (ISRS)",          "trouble": "TOC",                        "indication_has": "Troubles obsessionnels compulsifs"},
    {"substance_norm": "paroxétine",              "classe": "Antidépresseur (ISRS)",          "trouble": "Anxiété sociale / panique / TOC / ESPT / TAG", "indication_has": "TAG, trouble panique, anxiété sociale, TOC, ESPT"},
    {"substance_norm": "sertraline",              "classe": "Antidépresseur (ISRS)",          "trouble": "Trouble panique / TOC / anxiété sociale / ESPT", "indication_has": "Trouble panique, TOC, anxiété sociale, ESPT"},

    # --- ANTIDÉPRESSEURS autres ---
    {"substance_norm": "venlafaxine",             "classe": "Antidépresseur (IRSNa)",         "trouble": "Anxiété généralisée / panique / anxiété sociale", "indication_has": "TAG, trouble panique, trouble anxiété sociale"},
    {"substance_norm": "duloxétine",              "classe": "Antidépresseur (IRSNa)",         "trouble": "Anxiété généralisée",        "indication_has": "Trouble anxiété généralisée"},
    {"substance_norm": "clomipramine",            "classe": "Antidépresseur (tricyclique)",   "trouble": "TOC / trouble panique",      "indication_has": "TOC, prévention des attaques de panique"},

    # --- ANTIPSYCHOTIQUES (anxiété, 2e intention, courte durée) ---
    {"substance_norm": "cyamémazine",             "classe": "Antipsychotique",                "trouble": "Anxiété (2e intention)",     "indication_has": "Traitement de courte durée de l'anxiété de l'adulte en cas d'échec des thérapeutiques habituelles"},
    {"substance_norm": "sulpiride",               "classe": "Antipsychotique",                "trouble": "Anxiété (2e intention)",     "indication_has": "Traitement de courte durée de l'anxiété de l'adulte en cas d'échec des thérapeutiques habituelles"},
]

df = pd.DataFrame(reference)
sortie = DATA / "reference_molecule_trouble_has.csv"
df.to_csv(sortie, index=False, encoding="utf-8-sig")

print(f"✅ Référence HAS créée : {sortie}")
print(f"   {len(df)} molécules référencées.")
print("\nAperçu :")
print(df.to_string())