# 12_interface.py
# Interface Streamlit : assistant d'information pharmaceutique - troubles anxieux.
# Deux modes : appel direct du cerveau Python, ou appel de la pipeline n8n en production.
# Lancement : streamlit run script\12_interface.py

import sys
from pathlib import Path
import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module
assistant = import_module("06_assistant")

URL_N8N = "https://n8n-for-students.jedha.education/webhook/assistant"

st.set_page_config(page_title="Assistant Anxiolytiques — HAS/ANSM", page_icon="💊", layout="wide")

# --- En-tête ---
st.title("💊 Assistant d'information pharmaceutique")
st.caption("Troubles anxieux — sources officielles HAS et ANSM")

st.warning(
    "**Outil d'information destiné aux professionnels de santé.** "
    "Il ne constitue pas une aide à la prescription et n'accède à aucune donnée patient. "
    "La décision thérapeutique relève exclusivement du prescripteur."
)

# --- Barre latérale ---
with st.sidebar:
    st.header("⚙️ Mode d'exécution")
    mode = st.radio(
        "Comment la requête est traitée",
        ["Pipeline n8n (production)", "Cerveau Python (local)"],
        help="La pipeline n8n orchestre : webhook → croisement → Claude → PostgreSQL. Le mode local appelle directement le script Python.",
    )
    if mode.startswith("Pipeline"):
        st.success("✅ Requête envoyée au workflow n8n\n\nLe résultat est stocké en base PostgreSQL.")
    else:
        st.info("💻 Traitement local (mode secours)")

    st.divider()
    st.header("📚 Sources documentaires")
    st.markdown("""
**Disponibilité des médicaments**
- **ANSM** — Base des disponibilités des médicaments
  *(export du 08/07/2026 — 274 médicaments)*

**Indications thérapeutiques**
- **HAS** — ALD n°23, Actes et prestations sur les troubles anxieux graves
  *(actualisation janvier 2025 — 23 molécules)*

**Contre-indications**
- **HAS** — Bon usage des opioïdes
  *(mars 2022 — interactions à risque)*

**Règles de bon usage**
- **ANSM** — Dossier thématique « Bon usage des benzodiazépines »
  *(mis à jour 03/09/2025 — durée, personne âgée, dépendance, demi-vies)*
- **ANSM** — Brochure « Anxiété et médicaments »
  *(2025 — grossesse, gradation de l'anxiété)*
    """)

    st.divider()
    st.header("🔍 Ce que fait l'outil")
    st.markdown("""
1. Identifie le **trouble** anxieux évoqué
2. Remonte les **molécules** ayant une AMM (HAS)
3. Vérifie leur **statut de stock** (ANSM)
4. Détecte le **contexte patient** à risque
   *(opioïdes, alcool, dépression, grossesse, 65 ans et +)*
5. Signale les **contre-indications** et les **règles de bon usage**
6. Rédige une **synthèse sourcée**
    """)

    st.divider()
    st.header("⚠️ Limites")
    st.markdown("""
- Périmètre : **troubles anxieux uniquement**
- Aucune molécule hors sources n'est commentée
- Aucune donnée patient (allergies, antécédents)
- Contre-indications **non exhaustives**
  *(interactions principales seulement)*
- Ne remplace pas le RCP ni le prescripteur
    """)

# --- Exemples ---
st.subheader("Poser une question")

exemples = {
    "🚨 Sous opioïdes": "Patient sous opioïdes, trouble anxieux sévère. Je pensais à une benzodiazépine. Quelles options et précautions ?",
    "👴 Personne âgée": "Patient de 78 ans, anxiété sévère. Je pensais à une benzodiazépine. Quelles précautions ?",
    "📦 Rupture de stock": "Je voulais prescrire du Tranxène pour une anxiété sévère, est-ce disponible ?",
    "🧠 Dépression associée": "Patient avec anxiété sévère et syndrome dépressif. Une benzodiazépine seule convient-elle ?",
    "❓ Hors périmètre": "Le Stresam est-il adapté pour un trouble anxieux ?",
}

if "question" not in st.session_state:
    st.session_state.question = ""

cols = st.columns(len(exemples))
for i, (label, texte) in enumerate(exemples.items()):
    if cols[i].button(label, use_container_width=True):
        st.session_state.question = texte

question = st.text_area(
    "Décrivez la situation clinique",
    value=st.session_state.question,
    height=100,
    placeholder="Ex : Patient de 72 ans, anxiété généralisée sévère, sous morphine. Quelles options ?",
)

lancer = st.button("🔎 Interroger l'assistant", type="primary")


def appeler_n8n(q):
    """Envoie la question au webhook de production n8n."""
    r = requests.post(URL_N8N, json={"question": q}, timeout=120)
    r.raise_for_status()
    return r.json()


# --- Traitement ---
if lancer and question.strip():
    spinner_txt = "Appel de la pipeline n8n..." if mode.startswith("Pipeline") else "Traitement local..."
    with st.spinner(spinner_txt):
        try:
            if mode.startswith("Pipeline"):
                data = appeler_n8n(question)
                resultat = {
                    "reponse": data.get("reponse", ""),
                    "trouble_cible": data.get("trouble_cible", "—"),
                    "nb_molecules": data.get("nb_molecules", 0),
                    "alertes": data.get("alertes", "") or "",
                    "contextes": [],
                    "faits": "(traitement effectué côté n8n)",
                    "id_base": data.get("id"),
                }
            else:
                r = assistant.repondre(question)
                resultat = {
                    "reponse": r["reponse"],
                    "trouble_cible": r["trouble_cible"],
                    "nb_molecules": r["nb_molecules"],
                    "alertes": r["alertes"],
                    "contextes": r.get("contextes_detectes", []),
                    "faits": r["faits"],
                    "id_base": None,
                }
        except Exception as e:
            st.error(f"Erreur : {e}")
            st.stop()

    # --- Métadonnées ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Trouble identifié", resultat["trouble_cible"])
    c2.metric("Molécules analysées", resultat["nb_molecules"])
    nb_alertes = len([a for a in resultat["alertes"].split("\n") if a.strip()]) if resultat["alertes"] else 0
    c3.metric("Alertes déclenchées", nb_alertes)
    c4.metric("Enregistrement BDD", f"#{resultat['id_base']}" if resultat["id_base"] else "—")

    # --- Contextes détectés ---
    if resultat["contextes"]:
        libelles = {
            "opioides": "🚨 Opioïdes", "alcool": "🍷 Alcool",
            "depression": "🧠 Dépression", "grossesse": "🤰 Grossesse",
            "personne_agee": "👴 Personne âgée (65+)",
        }
        badges = " · ".join(libelles.get(c, c) for c in resultat["contextes"])
        st.info(f"**Contexte patient détecté :** {badges}")

    # --- Alertes en évidence ---
    if resultat["alertes"]:
        st.error("### 🚨 Alertes et règles de vigilance\n\n" + resultat["alertes"])

    # --- Réponse ---
    st.markdown("---")
    st.markdown(resultat["reponse"])

    # --- Traçabilité ---
    with st.expander("🔬 Données brutes transmises au modèle (traçabilité)"):
        st.caption("Le modèle ne peut rédiger qu'à partir de ces faits, extraits des sources HAS/ANSM.")
        st.code(resultat["faits"], language=None)

elif lancer:
    st.info("Merci de saisir une question.")