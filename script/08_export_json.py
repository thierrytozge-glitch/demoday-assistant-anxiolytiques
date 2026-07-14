# 08_export_json.py
# Convertit les CSV nécessaires en un seul fichier JSON, prêt à coller dans le nœud Code JS de n8n.

import pandas as pd
from pathlib import Path
import json

BASE = Path(r"C:\Users\Thierry\Desktop\Demoday")
DATA = BASE / "data"

# On charge les 3 tables utiles
ref = pd.read_csv(DATA / "reference_molecule_trouble_has.csv", encoding="utf-8-sig")
ansm = pd.read_csv(DATA / "medicaments_enrichi.csv", encoding="utf-8-sig")
ci = pd.read_csv(DATA / "contre_indications.csv", encoding="utf-8-sig")

# Pour l'ANSM, on ne garde que psychiatrie + les colonnes utiles (plus léger)
ansm_psy = ansm[ansm["domaine"].fillna("").str.contains("Psychiatrie")]
ansm_light = ansm_psy[["nom_court", "substance", "statut"]].copy()

data = {
    "reference": ref.to_dict(orient="records"),
    "ansm": ansm_light.to_dict(orient="records"),
    "contre_indications": ci.to_dict(orient="records"),
}

sortie = DATA / "donnees_pour_n8n.json"
with open(sortie, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ JSON créé : {sortie}")
print(f"   {len(data['reference'])} molécules de référence")
print(f"   {len(data['ansm'])} médicaments ANSM (psychiatrie)")
print(f"   {len(data['contre_indications'])} règles de contre-indication")
print("\n--- Aperçu du début du JSON ---")
print(json.dumps(data, ensure_ascii=False, indent=2)[:800])