# 02_enrichir_data.py
# Objectif : partir du CSV propre, extraire la substance active (entre crochets),
# et créer un fichier dédié aux médicaments de psychiatrie.

import pandas as pd
from pathlib import Path

# --- Chemins ---
BASE = Path(r"C:\Users\Thierry\Desktop\Demoday")
DATA = BASE / "data"

# --- 1. On repart du fichier propre créé à l'étape précédente ---
df = pd.read_csv(DATA / "medicaments_propre.csv", encoding="utf-8-sig")
print(f"Chargé : {len(df)} médicaments")

# --- 2. Extraction de la substance active (le texte entre crochets) ---
# str.extract prend ce qui est entre [ et ]. On enlève ensuite les espaces.
df["substance"] = df["medicament"].str.extract(r"\[(.*?)\]")
df["substance"] = df["substance"].str.strip()

# Petit contrôle : combien de lignes sans substance trouvée ?
sans_substance = df["substance"].isna().sum()
print(f"Lignes sans substance détectée : {sans_substance} (sur {len(df)})")

# --- 3. Extraction du nom commercial (ce qui est AVANT la virgule ou le tiret) ---
# Utile pour l'affichage : "Oracilline" au lieu du nom complet à rallonge.
df["nom_court"] = df["medicament"].str.split(r"[,–-]").str[0].str.strip()

# --- 4. Sauvegarde du fichier enrichi complet (tous domaines) ---
sortie_complet = DATA / "medicaments_enrichi.csv"
df.to_csv(sortie_complet, index=False, encoding="utf-8-sig")
print(f"\n✅ Fichier enrichi complet : {sortie_complet}")

# --- 5. Filtre PSYCHIATRIE uniquement ---
psy = df[df["domaine"].fillna("").str.contains("Psychiatrie")].copy()
sortie_psy = DATA / "medicaments_psychiatrie.csv"
psy.to_csv(sortie_psy, index=False, encoding="utf-8-sig")
print(f"✅ Fichier psychiatrie : {sortie_psy}")
print(f"   {len(psy)} médicaments en psychiatrie.")

# --- 6. Aperçu de ce qu'on a en psychiatrie ---
print("\n--- Médicaments psychiatrie (nom court | substance | statut) ---")
for _, r in psy.iterrows():
    print(f"  {r['nom_court']:<35} | {str(r['substance']):<40} | {r['statut']}")