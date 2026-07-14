# 06_assistant.py
# Le cerveau : croise reco HAS + stock ANSM + contre-indications + règles de bon usage ANSM,
# détecte les incohérences de la question, puis fait rédiger une synthèse par Claude
# (informative, non prescriptive, strictement sourcée).

import os
import re
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import anthropic

BASE = Path(r"C:\Users\Thierry\Desktop\Demoday")
DATA = BASE / "data"
load_dotenv(BASE / ".env", encoding="utf-8-sig")
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# --- Chargement des données ---
ref = pd.read_csv(DATA / "reference_molecule_trouble_has.csv", encoding="utf-8-sig")
ansm = pd.read_csv(DATA / "medicaments_enrichi.csv", encoding="utf-8-sig")
ci = pd.read_csv(DATA / "contre_indications.csv", encoding="utf-8-sig")
regles = pd.read_csv(DATA / "regles_bon_usage.csv", encoding="utf-8-sig")
demi_vies = pd.read_csv(DATA / "demi_vies_benzodiazepines.csv", encoding="utf-8-sig")

def base_substance(s):
    if pd.isna(s): return ""
    return str(s).lower().split("(")[0].strip()

ansm["substance_base"] = ansm["substance"].apply(base_substance)
ref["substance_base"] = ref["substance_norm"].apply(base_substance)

NOMS_COMMERCIAUX = {
    "xanax": "alprazolam", "lexomil": "bromazépam", "urbanyl": "clobazam",
    "likozam": "clobazam",
    "tranxene": "clorazépate dipotassique", "tranxène": "clorazépate dipotassique",
    "veratran": "clotiazépam", "valium": "diazépam", "victan": "loflazépate d'éthyle",
    "temesta": "lorazépam", "seresta": "oxazépam", "lysanxia": "prazépam",
    "atarax": "hydroxyzine", "buspar": "buspirone",
    "seropram": "citalopram", "seroplex": "escitalopram", "prozac": "fluoxétine",
    "floxyfral": "fluvoxamine", "deroxat": "paroxétine", "zoloft": "sertraline",
    "effexor": "venlafaxine", "cymbalta": "duloxétine", "anafranil": "clomipramine",
    "tercian": "cyamémazine", "dogmatil": "sulpiride",
}

MOTS_OPIOIDES = ["opio", "morphine", "tramadol", "méthadone", "methadone",
                 "codéine", "codeine", "oxycodone", "fentanyl", "buprénorphine"]


# ============================================================
# DÉTECTION DE L'ÂGE DU PATIENT
# ============================================================

def extraire_age_patient(question):
    """
    Extrait l'âge du PATIENT, en le distinguant d'une durée de traitement.

    Problème : "patient de 20 ans, sous morphine depuis 3 ans" contient deux nombres suivis
    de "ans". Une simple regex confondrait l'âge et la durée.

    Méthode : on repère d'abord les DURÉES ("depuis X ans", "pendant X ans"...) pour les
    écarter, puis on récupère les "X ans" restants comme âges du patient.
    """
    q = question.lower()

    motifs_duree = [
        r"depuis\s+(\d{1,3})\s*ans",
        r"pendant\s+(\d{1,3})\s*ans",
        r"il y a\s+(\d{1,3})\s*ans",
        r"durant\s+(\d{1,3})\s*ans",
        r"pour\s+(\d{1,3})\s*ans",
        r"sur\s+(\d{1,3})\s*ans",
    ]
    positions_duree = set()
    for motif in motifs_duree:
        for m in re.finditer(motif, q):
            positions_duree.add(m.start(1))

    ages = []
    for m in re.finditer(r"(\d{1,3})\s*ans", q):
        if m.start(1) in positions_duree:
            continue
        ages.append(int(m.group(1)))

    return [a for a in ages if 1 <= a <= 120]


# ============================================================
# DÉTECTION DES CONTEXTES ET INCOHÉRENCES
# ============================================================

def detecter_contextes(question):
    """
    Identifie les contextes patient à risque évoqués dans la question.
    Ces contextes déclenchent des alertes, indépendamment des molécules sélectionnées.

    Gestion de la NÉGATION : un mot-clé précédé d'une négation dans la MÊME PHRASE
    ("aucune addiction à l'alcool", "sans traitement opioïde") ne déclenche PAS l'alerte.
    La négation ne traverse pas une fin de phrase : "aucun traitement. Il est sous morphine"
    ne nie PAS la morphine.

    Détection de l'ÂGE : seul un âge patient chiffré >= 65 ans déclenche les alertes
    gériatriques. Le mot "âgé" seul ne suffit pas : "âgé de 20 ans" ne doit rien déclencher.
    """
    q = question.lower()
    contextes = []

    def nie(mot):
        """Le mot-clé est-il précédé d'une négation, dans la même phrase ?"""
        for m in re.finditer(re.escape(mot), q):
            debut = max(0, m.start() - 40)
            avant = q[debut:m.start()]
            coupure = max(avant.rfind("."), avant.rfind(";"),
                          avant.rfind("!"), avant.rfind("?"))
            if coupure != -1:
                avant = avant[coupure + 1:]
            if any(n in avant for n in ["aucun", "aucune", "pas d", "pas de", "sans ",
                                        "ni ", "jamais", "non "]):
                return True
        return False

    if any(m in q and not nie(m) for m in MOTS_OPIOIDES):
        contextes.append("opioides")

    if "alcool" in q and not nie("alcool"):
        contextes.append("alcool")

    if any(m in q and not nie(m) for m in ["dépress", "depress", "idées noires", "suicid"]):
        contextes.append("depression")

    if any(m in q and not nie(m) for m in ["enceinte", "grossesse", "allaite"]):
        contextes.append("grossesse")

    ages = extraire_age_patient(question)
    est_age = any(a >= 65 for a in ages)
    if not ages and any(m in q for m in ["senior", "gériatri", "geriatri", "ehpad",
                                         "personne âgée", "sujet âgé"]):
        est_age = True
    if est_age:
        contextes.append("personne_agee")

    return list(dict.fromkeys(contextes))


def detecter_incoherences(question):
    """
    Repère les contradictions internes et les situations hors périmètre.
    Ces éléments sont remontés au modèle pour qu'il les signale explicitement,
    au lieu de trancher silencieusement à la place du clinicien.
    """
    q = question.lower()
    incoherences = []
    ages = extraire_age_patient(question)

    # 1. Patient mineur — les sources portent sur l'adulte
    mineurs = [a for a in ages if a < 18]
    if mineurs:
        incoherences.append(
            f"PATIENT MINEUR ({min(mineurs)} ans). Les sources de cet outil (HAS ALD n°23 ; "
            "ANSM bon usage des benzodiazépines) portent sur l'ADULTE. Les indications, posologies "
            "et contre-indications PÉDIATRIQUES ne sont PAS couvertes. Tu ne dois PAS te prononcer "
            "sur la prise en charge de ce patient : renvoie vers les recommandations pédiatriques "
            "et un avis spécialisé."
        )

    # 2. Contradiction de sévérité
    severes = ["sévère", "severe", "grave", "invalidant"]
    legers = ["légè", "leger", "léger", "mineur", "passag"]
    if any(m in q for m in severes) and any(m in q for m in legers):
        incoherences.append(
            "La sévérité du trouble est décrite à la fois comme SÉVÈRE et comme LÉGÈRE/PASSAGÈRE. "
            "Ces qualifications sont incompatibles et orientent vers des classes thérapeutiques différentes."
        )

    # 3. Plusieurs âges patient contradictoires
    if len(set(ages)) > 1:
        incoherences.append(
            f"Plusieurs âges différents sont mentionnés pour le patient : {sorted(set(ages))} ans. "
            "L'âge est déterminant (les recommandations changent à partir de 65 ans)."
        )

    # 4. "Aucun traitement" alors qu'un traitement opioïde est cité
    dit_aucun_traitement = any(m in q for m in ["aucun traitement", "pas de traitement",
                                                "sans traitement", "aucun médicament"])
    cite_traitement = any(m in q for m in MOTS_OPIOIDES)
    if dit_aucun_traitement and cite_traitement:
        incoherences.append(
            "La question indique 'aucun traitement en cours' MAIS mentionne un traitement opioïde. "
            "Cette contradiction doit être levée : la présence d'un opioïde change radicalement l'analyse."
        )

    # 5. "Aucune addiction" alors qu'une dépendance est citée
    dit_aucune_addiction = any(m in q for m in ["aucune addiction", "pas d'addiction",
                                                "sans addiction", "aucune dépendance"])
    cite_addiction = any(m in q for m in ["alcoolodépendant", "alcoolique", "dépendance à"])
    if dit_aucune_addiction and cite_addiction:
        incoherences.append(
            "La question indique 'aucune addiction' MAIS mentionne une dépendance. Contradiction à lever."
        )

    # 6. Incohérence de genre (masculin + grossesse)
    masculin = any(m in q for m in [" il ", "monsieur", "homme"])
    grossesse = any(m in q for m in ["enceinte", "grossesse"])
    if masculin and grossesse and "patiente" not in q and "femme" not in q:
        incoherences.append(
            "La question désigne le patient au masculin MAIS mentionne une grossesse. Contradiction à lever."
        )

    return incoherences


# ============================================================
# CONSTRUCTION DES FAITS ET DES ALERTES
# ============================================================

def detecter_molecules_citees(question):
    """Repère les molécules ou noms commerciaux cités dans la question."""
    q = question.lower()
    citees = set()
    for nom, molecule in NOMS_COMMERCIAUX.items():
        if nom in q:
            citees.add(molecule)
    for _, r in ref.iterrows():
        if r["substance_base"] in q:
            citees.add(r["substance_norm"])
    return citees


def faits_pour_trouble(mot_cle):
    """Pour un trouble donné, renvoie les molécules HAS correspondantes,
    leur statut de stock ANSM, et leur demi-vie si c'est une benzodiazépine."""
    sel = ref[ref["trouble"].str.contains(mot_cle, case=False, na=False)]
    faits = []
    for _, r in sel.iterrows():
        presentations = ansm[ansm["substance_base"] == r["substance_base"]]
        statut = " / ".join(presentations["statut"].unique()) if len(presentations) else "Disponible (aucun problème signalé par l'ANSM)"
        dv = demi_vies[demi_vies["substance"] == r["substance_norm"]]
        info_dv = f" — demi-vie : {dv.iloc[0]['demi_vie']}" if len(dv) else ""
        faits.append(
            f"- {r['substance_norm']} ({r['classe']}) — indication HAS : {r['indication_has']} — stock ANSM : {statut}{info_dv}"
        )
    return sel, "\n".join(faits)


def alertes_pour_contexte(question, molecules_selectionnees):
    """
    Règle de sécurité : dès qu'un contexte patient à risque est détecté, TOUTES les alertes
    liées à ce contexte sont remontées — indépendamment des molécules sélectionnées.

    Raison : un patient sous opioïdes doit être averti du risque lié aux benzodiazépines même
    si la question porte sur un trouble dont la sélection ne remonte aucune benzodiazépine.
    Filtrer les alertes selon les molécules affichées créerait un angle mort.
    """
    contextes = detecter_contextes(question)
    if not contextes:
        return "", []

    lignes = []
    for ctx in contextes:
        for _, r in ci[ci["contexte_patient"] == ctx].iterrows():
            lignes.append(f"- [{r['niveau']}] {r['alerte']} (source : {r['source']})")
    for ctx in contextes:
        for _, r in regles[regles["contexte"] == ctx].iterrows():
            lignes.append(f"- [{r['niveau']}] {r['regle']} (source : {r['source']})")

    return "\n".join(lignes), contextes


def regles_generales():
    """Les règles de bon usage qui s'appliquent TOUJOURS aux benzodiazépines."""
    lignes = []
    for _, r in regles[regles["contexte"] == "toujours"].iterrows():
        lignes.append(f"- [{r['niveau']}] {r['regle']} (source : {r['source']})")
    return "\n".join(lignes)


# ============================================================
# PROMPT SYSTÈME
# ============================================================

SYSTEM = """Tu es un assistant d'information pharmaceutique destiné à des professionnels de santé.

PÉRIMÈTRE DOCUMENTAIRE STRICT — RÈGLE ABSOLUE :
Tes seules sources sont les faits fournis dans le message (HAS ALD n°23 - troubles anxieux graves ; base ANSM des disponibilités ; reco HAS bon usage des opioïdes ; dossier ANSM bon usage des benzodiazépines). Ces sources portent sur l'ADULTE. Tu n'as AUCUNE autre source.

Si le professionnel évoque un médicament ou une molécule qui NE FIGURE PAS dans les faits fournis :
- Tu dois le signaler explicitement : "⚠️ [nom] ne figure pas dans les sources documentaires de cet outil. Je ne peux pas me prononcer sur cette molécule."
- Tu ne donnes AUCUNE information sur elle (ni indication, ni posologie, ni interaction, ni classe), MÊME SI tu la connais par ailleurs.
- Tu invites à consulter le RCP du médicament ou la Base de données publique des médicaments.
- Si le nom saisi ressemble à une molécule de tes sources (possible faute de frappe), tu peux le signaler MAIS tu dois avertir : "⚠️ Vérifiez l'orthographe exacte : un médicament au nom similaire mais différent pourrait exister hors de ma base documentaire."
- Tu ajoutes systématiquement : "⚠️ Cette molécule étant hors de mon périmètre, je ne peux vérifier AUCUNE contre-indication la concernant."

AUTRES RÈGLES :
1. Tu ne prescris JAMAIS. Tu informes.
2. Ne cite que les molécules présentes dans les faits fournis.
3. Signale clairement les molécules en rupture ou en tension d'approvisionnement.
4. Si des alertes de contre-indication sont fournies, présente-les EN PREMIER, de façon visible.
5. Si la sévérité évoquée ne correspond pas à l'indication HAS d'une molécule, signale-le.
6. Tu n'as accès à AUCUNE donnée du patient (allergies, antécédents, traitements en cours non mentionnés). Ne fais aucune supposition à leur sujet.
7. Termine TOUJOURS par : "Cette information ne remplace pas la décision du prescripteur."
8. Quand une alerte liée au contexte patient est fournie (opioïdes, alcool, dépression, grossesse, personne âgée), tu la présentes TOUJOURS, même si aucune molécule de la classe concernée n'est proposée dans les faits.
9. Quand une benzodiazépine est évoquée ou proposée, rappelle les règles de bon usage fournies (durée maximale, arrêt progressif programmé, risque de dépendance, interdiction d'associer plusieurs benzodiazépines).
10. Si des informations déterminantes ne sont PAS fournies dans la question (âge du patient — les règles changent à partir de 65 ans ; traitements en cours ; grossesse ; syndrome dépressif associé ; comorbidités), tu DOIS le signaler explicitement en fin de réponse sous la forme : "⚠️ Informations non fournies pouvant modifier cette analyse : [liste]. Ces éléments changeraient les recommandations applicables."
11. Si des INCOHÉRENCES sont signalées dans le message, tu DOIS les présenter EN TOUT PREMIER, avant toute recommandation, et demander au professionnel de les lever. Tu ne tranches JAMAIS à sa place entre deux informations contradictoires.
12. Si le professionnel énonce une affirmation FAUSSE au regard de tes sources (ex : "les benzodiazépines sont sans risque avec les opioïdes", "le Xanax est un opioïde", "telle molécule est disponible alors qu'elle est en rupture"), tu DOIS la corriger explicitement en citant ta source. Tu ne valides JAMAIS une prémisse fausse.
13. PATIENT MINEUR : si le patient a moins de 18 ans, tu ne dois PAS te prononcer sur sa prise en charge médicamenteuse. Tes sources portent sur l'adulte. Signale-le et renvoie vers les recommandations pédiatriques et un avis spécialisé.
14. Ne cite JAMAIS une source que tu n'as pas reçue dans le message. Si une information n'est accompagnée d'aucune source dans les faits fournis, ne l'attribue à aucun document.

Sois concis et structuré."""


def rediger(question, tableau_faits, alertes, regles_gen, incoherences):
    """Envoie les faits à Claude et récupère la synthèse rédigée.
    Retourne (texte, tronquee) — tronquee=True si la limite de tokens a été atteinte."""
    bloc_alertes = f"\n\nALERTES LIÉES AU CONTEXTE PATIENT — À SIGNALER EN PRIORITÉ :\n{alertes}" if alertes else ""
    bloc_regles = f"\n\nRÈGLES DE BON USAGE DES BENZODIAZÉPINES (à rappeler si une benzodiazépine est évoquée) :\n{regles_gen}" if regles_gen else ""

    bloc_incoherences = ""
    if incoherences:
        liste = "\n".join(f"- {i}" for i in incoherences)
        bloc_incoherences = (
            f"\n\n⚠️ INCOHÉRENCES / SITUATIONS HORS PÉRIMÈTRE DÉTECTÉES — À SIGNALER EN TOUT PREMIER :\n{liste}\n"
            "Tu DOIS signaler ces éléments au professionnel AVANT toute recommandation. "
            "Ne tranche PAS à sa place entre des informations contradictoires."
        )

    user = (
        f"Question du professionnel : {question}\n\n"
        f"Faits disponibles (SOURCES : HAS ALD n°23 + base ANSM disponibilités) :\n{tableau_faits}"
        f"{bloc_incoherences}{bloc_alertes}{bloc_regles}"
    )
    reponse = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        system=SYSTEM,
        messages=[{"role": "user", "content": user}],
    )
    tronquee = (reponse.stop_reason == "max_tokens")
    return reponse.content[0].text, tronquee


def detecter_trouble(question):
    """
    Identifie le type de trouble anxieux évoqué dans la question.

    En cas de CONTRADICTION de sévérité (ex : "sévère mais léger"), on retient le périmètre
    le PLUS LARGE ("anxiété") pour ne pas priver le professionnel d'options thérapeutiques.
    La contradiction est signalée séparément via detecter_incoherences().
    """
    q = question.lower()

    severes = ["sévère", "severe", "grave", "invalidant"]
    legers = ["légè", "leger", "léger", "mineur", "passag"]
    a_severe = any(m in q for m in severes)
    a_leger = any(m in q for m in legers)

    if a_severe and a_leger:
        return "anxiété"

    if "généralis" in q or "tag" in q: return "généralis"
    if "panique" in q: return "panique"
    if "toc" in q or "obsession" in q: return "toc"
    if "sociale" in q: return "sociale"
    if a_leger: return "légère"
    return "anxiété"


def repondre(question):
    """Fonction principale : prend une question, renvoie la réponse complète et ses métadonnées."""
    mot_cle = detecter_trouble(question)
    sel, tableau = faits_pour_trouble(mot_cle)
    alertes, contextes = alertes_pour_contexte(question, sel)
    citees = detecter_molecules_citees(question)
    reg_gen = regles_generales()
    incoherences = detecter_incoherences(question)
    texte, tronquee = rediger(question, tableau, alertes, reg_gen, incoherences)
    return {
        "question": question,
        "trouble_cible": mot_cle,
        "nb_molecules": len(sel),
        "faits": tableau,
        "alertes": alertes,
        "contextes_detectes": contextes,
        "incoherences": incoherences,
        "molecules_citees_reconnues": sorted(citees),
        "reponse": texte,
        "tronquee": tronquee,
    }


if __name__ == "__main__":
    q = ("Mon patient est âgé de 20 ans, il n'a aucun traitement. Il est sous morphine depuis "
         "3 ans pour des douleurs chroniques. Il présente des troubles anxieux sévères, mais très "
         "légers et passagers. Quels médicaments seraient adéquats ?")
    r = repondre(q)
    print(f"--- Trouble : {r['trouble_cible']} | {r['nb_molecules']} molécules ---")
    print(f"--- Âges patient : {extraire_age_patient(q)} ---")
    print(f"--- Contextes : {r['contextes_detectes'] or '(aucun)'} ---")
    print(f"--- Incohérences : {len(r['incoherences'])} ---")
    print(f"\n--- Alertes ---\n{r['alertes'] or '(AUCUNE — PROBLÈME !)'}")
    print(f"\n--- Réponse ---\n{r['reponse'][:800]}...")