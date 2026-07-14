# 05_test_claude.py
# Test minimal : vérifier que la clé API fonctionne et que Claude répond.
# Aucune logique métier ici, juste la connexion.

import os
from pathlib import Path
from dotenv import load_dotenv
import anthropic

# --- 1. Charger la clé depuis le .env (situé à la racine Demoday) ---
BASE = Path(r"C:\Users\Thierry\Desktop\Demoday")
load_dotenv(BASE / ".env")

cle = os.environ.get("ANTHROPIC_API_KEY")
if not cle:
    print("❌ Clé introuvable. Vérifie que .env contient ANTHROPIC_API_KEY=... à la racine Demoday.")
    raise SystemExit

print("✅ Clé chargée (elle commence par :", cle[:10], "...)")

# --- 2. Créer le client et envoyer un message test ---
client = anthropic.Anthropic(api_key=cle)

reponse = client.messages.create(
    model="claude-sonnet-4-5",          # modèle rapide et économique, parfait pour un MVP
    max_tokens=200,
    messages=[
        {"role": "user", "content": "Réponds juste 'Connexion OK' si tu me reçois."}
    ],
)

# --- 3. Afficher la réponse ---
print("\nRéponse de Claude :")
print(reponse.content[0].text)