# 04_croisement.py
# Objectif : relier la référence HAS (molécule -> trouble) au stock ANSM (médicament -> statut),
# via la substance active. Résultat : pour chaque molécule de l'anxiété, sait-on si elle est en stock ?

import pandas as pd
from pathlib import Path

BASE = Path(r"C:\Users\Thierry\Desktop\Demoday")
DATA = BASE / "data"

# --- 1. Chargement des deux sources ---
ref = pd.read_csv(DATA / "reference_molecule_trouble_has.csv", encoding="utf-8-sig")
ansm = pd.read_csv(DATA / "medicaments_enrichi.csv", encoding="utf-8-sig")
print(f"Référence HAS : {len(ref)} molécules | Stock ANSM : {len(ansm)} médicaments")

# --- 2. Normalisation pour faire matcher les substances ---
# Les substances ANSM ont des précisions entre parenthèses : "venlafaxine (chlorhydrate de)".
# On garde juste le début (le nom de base) et on met tout en minuscules pour comparer.
def base_substance(s):
    if pd.isna(s):
        return ""
    s = str(s).lower().strip()
    s = s.split("(")[0].strip()   # "lithium (carbonate de)" -> "lithium"
    return s

ansm["substance_base"] = ansm["substance"].apply(base_substance)
ref["substance_base"] = ref["substance_norm"].apply(base_substance)

# --- 3. Pour chaque molécule HAS, on cherche ses présentations dans le stock ANSM ---
lignes = []
for _, r in ref.iterrows():
    sb = r["substance_base"]
    correspondances = ansm[ansm["substance_base"] == sb]
    if len(correspondances) == 0:
        # molécule connue de la HAS mais absente du fichier ANSM (donc pas signalée = a priori dispo normale)
        lignes.append({
            "substance": r["substance_norm"], "classe": r["classe"], "trouble": r["trouble"],
            "medicament_ansm": "(non listé ANSM)", "statut": "Non signalé"
        })
    else:
        for _, c in correspondances.iterrows():
            lignes.append({
                "substance": r["substance_norm"], "classe": r["classe"], "trouble": r["trouble"],
                "medicament_ansm": c["nom_court"], "statut": c["statut"]
            })

resultat = pd.DataFrame(lignes)
sortie = DATA / "croisement_anxiete_stock.csv"
resultat.to_csv(sortie, index=False, encoding="utf-8-sig")
print(f"\n✅ Croisement écrit : {sortie}  ({len(resultat)} lignes)")

# --- 4. Ce qui nous intéresse vraiment : les molécules de l'anxiété qui ONT un signalement ANSM ---
print("\n--- Molécules de l'anxiété avec un signalement de stock ANSM ---")
signalees = resultat[resultat["statut"] != "Non signalé"]
if len(signalees) == 0:
    print("  (aucune)")
else:
    for _, r in signalees.iterrows():
        print(f"  {r['substance']:<20} | {r['trouble']:<35} | {r['medicament_ansm']:<30} | {r['statut']}")