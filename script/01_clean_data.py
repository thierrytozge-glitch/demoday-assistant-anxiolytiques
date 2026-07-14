# 01_clean_data.py
# Objectif : lire le XLS brut de l'ANSM et produire un CSV propre.
# On ne garde que ce qui nous sert, on nettoie, on sauvegarde.

import pandas as pd
from pathlib import Path

# --- Chemins (on part du dossier Demoday, quel que soit l'endroit d'où on lance) ---
BASE = Path(r"C:\Users\Thierry\Desktop\Demoday")
DATA = BASE / "data"
FICHIER_XLS = DATA / "export_disponibilites-des-medicaments_08-07-2026_23-36-04.xls"

# --- 1. Lecture du fichier brut ---
print(f"Lecture de : {FICHIER_XLS}")
df = pd.read_excel(FICHIER_XLS, engine="calamine")   # calamine lit ce format d'export ANSM
print(f"OK : {df.shape[0]} lignes, {df.shape[1]} colonnes")
print("Colonnes trouvées :", list(df.columns))

# --- 2. On renomme les colonnes en noms courts et pratiques ---
renommage = {
    "Titre": "medicament",
    "Date de mise à jour": "date_maj",
    "Date de début de situation": "date_debut",
    "Date de remise à disposition": "date_remise",
    "Statut": "statut",
    "Domaine(s) médical(aux)": "domaine",
    "URL de la page": "url",
}
df = df.rename(columns=renommage)

# --- 3. On garde seulement les colonnes utiles ---
colonnes_gardees = ["medicament", "statut", "domaine", "date_maj", "date_debut", "date_remise", "url"]
df = df[[c for c in colonnes_gardees if c in df.columns]]

# --- 4. Nettoyage : espaces en trop, lignes vides ---
df["medicament"] = df["medicament"].str.strip()
df["statut"] = df["statut"].str.strip()
df = df.dropna(subset=["medicament"])   # on jette les lignes sans nom de médicament

# --- 5. Sauvegarde ---
sortie = DATA / "medicaments_propre.csv"
df.to_csv(sortie, index=False, encoding="utf-8-sig")   # utf-8-sig = accents OK dans Excel
print(f"\n✅ Fichier propre écrit : {sortie}")
print(f"   {df.shape[0]} médicaments conservés.")
print("\nAperçu des 5 premières lignes :")
print(df.head().to_string())