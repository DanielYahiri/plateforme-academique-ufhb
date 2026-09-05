"""
Pipeline "Beauté des Nombres"
─────────────────────────────
liens YouTube dans VIDEOS_A_AJOUTER, script en local :

    python scripts/sync_videos_ia.py

Pour chaque lien, le script :
  1. récupère le titre réel de la vidéo (oEmbed YouTube, gratuit, sans clé)
  2. récupère la transcription (sous-titres) via youtube-transcript-api
  3. envoie la transcription à Gemini pour générer résumé + tags + niveau
  4. insère (ou met à jour si déjà présent) la ligne dans culture.videos_culture

Nécessite dans .env : GEMINI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY
"""

import json
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY, GEMINI_API_KEY

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
)

# 👉 ici les liens des vidéos à ajouter
VIDEOS_A_AJOUTER = [
    # --- La Trilogie Originelle : « L'Épopée Fantastique » (2022 - 2023) ---
    "https://www.youtube.com/watch?v=O0pKb3-YTzU",
    "https://www.youtube.com/watch?v=qU24Zvs3mZM",
    "https://www.youtube.com/watch?v=lvB5uTwry9c",

    # --- Énigmes, Biographies et Beauté Pure (2023) ---
    "https://www.youtube.com/watch?v=HzSq7-CO0jI",
    "https://www.youtube.com/watch?v=M2VMQtYnwb4",
    "https://www.youtube.com/watch?v=x5ezPLbkdZ4",
    "https://www.youtube.com/watch?v=OjpA5TeIQ6s",

    # --- Théorèmes, Révolutions et Grands Mystères (2024) ---
    "https://www.youtube.com/watch?v=Zg3eLm4VY1A",
    "https://www.youtube.com/watch?v=_afUgCRBcIM",
    "https://www.youtube.com/watch?v=iogRnuz6gpo",

    # --- Géométrie, Crises de la Logique et Effondrements (2025 - 2026) ---
    "https://www.youtube.com/watch?v=idArGLZFkSQ",
    "https://www.youtube.com/watch?v=FqnT6x2NQCc",
    "https://www.youtube.com/watch?v=XhTOoLiGZfk",
]

DONNEES_MANUELLES = {
    "O0pKb3-YTzU": {
        "titre_fr": "L'histoire du chiffre 1",
        "resume": "Comment un simple trait est-il devenu le symbole universel de l'unite ? Cette video remonte aux premieres representations du chiffre 1 en Egypte, en Mesopotamie, en Chine et chez les Mayas. Elle suit ensuite la piste qui conduit jusqu'aux inscriptions indiennes de la grotte de Nanaghat. Au fil des siecles, ce signe s'est redresse et transforme pour donner naissance a notre graphie moderne. Un voyage surprenant pour decouvrir qu'un chiffre apparemment evident a une histoire extraordinairement riche.",
        "tags": ["histoire", "chiffre", "unite"],
        "niveau": "Débutant",
    },
    "HzSq7-CO0jI": {
        "titre_fr": "Srinivasa Ramanujan, le genie intuitif",
        "resume": "Comment un autodidacte indien a-t-il pu bouleverser les mathematiques sans formation universitaire classique ? Cet episode raconte le parcours hors du commun de Srinivasa Ramanujan et ses intuitions presque mystiques. De ses formules notees dans des carnets a sa rencontre decisive avec G. H. Hardy, son histoire ressemble a un veritable roman mathematique. Une invitation a decouvrir un esprit capable de voir des verites que personne n'avait encore imaginees.",
        "tags": ["biographie", "Ramanujan", "genie"],
        "niveau": "Débutant",
    },
    "M2VMQtYnwb4": {
        "titre_fr": "Les suites et les series",
        "resume": "Une suite de nombres peut-elle raconter une histoire ? Cette video explore les suites arithmetiques et geometriques, puis montre comment elles conduisent naturellement aux series. Les notions deviennent accessibles grace a des references au cinema et a la pop-culture. Derriere ces exemples amusants se cache un outil essentiel pour comprendre l'infini, les modeles et de nombreux phenomenes scientifiques. De quoi regarder les nombres qui se repetent avec un oeil nouveau.",
        "tags": ["suites", "series", "vulgarisation"],
        "niveau": "Intermédiaire",
    },
    "x5ezPLbkdZ4": {
        "titre_fr": "Pourquoi aimer les mathematiques ?",
        "resume": "Et si les mathematiques etaient bien plus qu'une matiere scolaire ? Cette video propose trois raisons de les aimer : elles sont partout dans notre quotidien, elles ressemblent parfois a un jeu et elles permettent de decrire les lois de l'Univers. Newton, Poincare et d'autres grands esprits montrent comment une idee abstraite peut devenir terriblement efficace. Un manifeste vivant pour changer son regard sur les mathematiques.",
        "tags": ["philosophie", "passion", "sciences"],
        "niveau": "Débutant",
    },
    "OjpA5TeIQ6s": {
        "titre_fr": "La beaute des mathematiques",
        "resume": "Les mathematiques sont-elles nees pour compter, ou pour comprendre le monde ? Ce voyage traverse les besoins pratiques de l'Antiquite, la rigueur d'Euclide et l'audace des Pythagoriciens. Zero, nombres negatifs, probabilites et infinis revelent peu a peu une architecture insoupconnee. Une exploration esthetique et historique qui donne envie de chercher la beaute derriere chaque formule.",
        "tags": ["histoire", "geometrie", "axiomes"],
        "niveau": "Débutant",
    },
    "Zg3eLm4VY1A": {
        "titre_fr": "Emmy Noether, la mathematicienne qui a revolutionne le monde",
        "resume": "Comment les symetries peuvent-elles expliquer les lois de la nature ? Cette video raconte le combat et les decouvertes d'Emmy Noether, une pionniere de l'algebre abstraite. Malgre les obstacles imposes aux femmes de son epoque, elle s'impose parmi les esprits les plus brillants de Gottingen. Son celebre theoreme relie symetries et lois de conservation, jusqu'a renforcer les fondations de la relativite. Une destinee scientifique aussi audacieuse qu'inspirante.",
        "tags": ["biographie", "Noether", "algebre"],
        "niveau": "Intermédiaire",
    },
    "_afUgCRBcIM": {
        "titre_fr": "Le plus grand mystere de l'Univers",
        "resume": "Pourquoi les nombres premiers semblent-ils suivre une regle invisible ? La video plonge dans l'un des grands mysteres de l'arithmetique, entre la preuve d'Euclide et la decomposition unique des entiers. Ces nombres servent de briques fondamentales, mais leur apparition parait presque aleatoire. Les chercheurs poursuivent encore l'ordre cache derriere ce chaos apparent. Une enigme qui transforme une suite de nombres en veritable aventure scientifique.",
        "tags": ["arithmetique", "premiers", "mystere"],
        "niveau": "Intermédiaire",
    },
    "iogRnuz6gpo": {
        "titre_fr": "Le casse-tete vieux de 2000 ans",
        "resume": "Pourquoi le cinquieme postulat d'Euclide a-t-il resiste pendant deux millenaires ? Des mathematiciens comme Omar Khayyam et Saccheri ont tente de le deduire des autres postulats, sans jamais parvenir a fermer le raisonnement. Leurs echecs ont finalement ouvert une porte inattendue. En acceptant de changer une regle, ils ont decouvert les geometries non euclidiennes. Une enigme historique qui montre que l'erreur apparente peut devenir une revolution.",
        "tags": ["postulat", "Euclide", "geometrie"],
        "niveau": "Avancé",
    },
    "idArGLZFkSQ": {
        "titre_fr": "Pourquoi l'angle droit est-il si puissant ?",
        "resume": "Un angle droit peut-il transformer toute notre maniere de decrire le monde ? Avec Rene Descartes, deux axes perpendiculaires ont permis de relier les figures geometriques aux equations. Droites, cercles et courbes deviennent alors des objets que l'on peut calculer. Cette video revele pourquoi le repere cartesien est au coeur des mathematiques modernes et de leurs applications. Une idee simple, mais d'une puissance vertigineuse.",
        "tags": ["Descartes", "repere", "algebre"],
        "niveau": "Intermédiaire",
    },
    "FqnT6x2NQCc": {
        "titre_fr": "Ils ont fait trembler les mathematiques",
        "resume": "Peut-on construire toutes les mathematiques a partir d'une logique parfaite ? La theorie des ensembles semblait offrir cette promesse, jusqu'a ce que des paradoxes viennent fissurer ses fondations. Cette crise a oblige les mathematiciens a reexaminer la notion de verite et les limites des demonstrations. L'episode raconte un moment ou la recherche de certitude absolue a failli faire s'effondrer tout l'edifice. Une plongee fascinante dans les coulisses de la logique.",
        "tags": ["logique", "ensembles", "paradoxe"],
        "niveau": "Avancé",
    },
    "XhTOoLiGZfk": {
        "titre_fr": "La nuit ou tout s'est effondre",
        "resume": "Si notre civilisation disparaissait demain, que faudrait-il reconstruire en premier ? Cette video imagine un monde prive de ses technologies et remonte les etapes qui ont permis a l'humanite de progresser. Du feu aux constructions complexes, chaque invention depend d'un savoir transmis. Le recit rappelle que nos connaissances sont un heritage fragile, mais aussi une force de survie. Une reflexion captivante sur la science, la memoire et l'avenir.",
        "tags": ["civilisation", "sciences", "transmission"],
        "niveau": "Débutant",
    },
   "qU24Zvs3mZM": {
  "titre_fr": "L'histoire du chiffre 0",
  "resume": "Comment une absence est-elle devenue l’un des nombres les plus puissants de notre civilisation ? Cette vidéo retrace l’apparition progressive du zéro, depuis les premières façons de représenter le vide jusqu’à son statut de véritable nombre. Elle montre pourquoi les anciennes civilisations ont longtemps eu du mal à lui donner une place dans leurs systèmes de calcul. Le récit s’intéresse notamment au rôle décisif des mathématiciens indiens dans la naissance du zéro moderne. Grâce à lui, les opérations deviennent plus souples et notre système de numération positionnelle peut enfin fonctionner pleinement. Une découverte en apparence simple, mais sans laquelle l’algèbre, l’informatique et les mathématiques modernes seraient méconnaissables.",
  "tags": [
    "zéro",
    "histoire",
    "numération"
  ],
  "niveau": "Débutant"
},

  "lvB5uTwry9c": {
  "titre_fr": "Sophie Germain : Madame la mathématicienne",
  "resume": "Comment une jeune femme du XVIIIe siècle a-t-elle réussi à se faire une place dans un monde qui refusait presque l'accès aux mathématiques aux femmes ? Cette vidéo raconte le parcours exceptionnel de Sophie Germain, qui étudia en secret avant de correspondre avec les plus grands savants sous le pseudonyme de Monsieur Le Blanc. Ses travaux sur la théorie des nombres l'ont conduite à étudier le dernier théorème de Fermat et à laisser son nom aux célèbres nombres premiers de Sophie Germain. Elle s'est également intéressée à la physique et à la théorie de l'élasticité, un domaine dans lequel ses recherches ont été longtemps sous-estimées. Son histoire révèle le courage, l'ingéniosité et la passion nécessaires pour poursuivre une vocation malgré les barrières de son époque.",
  "tags": [
    "Sophie Germain",
    "théorie des nombres",
    "égalité des femmes"
  ],
  "niveau": "Intermédiaire"
}
}


def extraire_id(url: str) -> str:
    match = re.search(r"(?:youtu\.be/|v=)([\w-]{11})", url)
    if not match:
        raise ValueError(f"Impossible d'extraire l'ID vidéo depuis : {url}")
    return match.group(1)


def recuperer_titre(youtube_id: str) -> str:
    r = httpx.get(
        "https://www.youtube.com/oembed",
        params={"url": f"https://www.youtube.com/watch?v={youtube_id}", "format": "json"},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["title"]


def recuperer_transcript(youtube_id: str) -> str:
    langues = ["fr", "fr-FR", "en", "en-US"]
    try:
        segments = YouTubeTranscriptApi.get_transcript(youtube_id, languages=langues)
        return " ".join(s["text"] for s in segments)
    except Exception as api_error:
        print(f"  ℹ️  API sous-titres indisponible, fallback yt-dlp ({api_error})")

    with YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
        info = ydl.extract_info(
            f"https://www.youtube.com/watch?v={youtube_id}",
            download=False,
        )

    pistes = info.get("subtitles") or info.get("automatic_captions") or {}
    piste = next((pistes[langue] for langue in langues if langue in pistes), None)
    if not piste:
        raise RuntimeError("aucune piste de sous-titres disponible")

    formats_vtt = [format_ for format_ in piste if format_.get("ext") == "vtt"]
    format_vtt = formats_vtt[0] if formats_vtt else piste[0]
    reponse = httpx.get(format_vtt["url"], timeout=30)
    reponse.raise_for_status()

    lignes = []
    for ligne in reponse.text.splitlines():
        ligne = re.sub(r"<[^>]+>", "", ligne).strip()
        if not ligne or ligne == "WEBVTT" or "-->" in ligne or ligne.isdigit():
            continue
        if not lignes or lignes[-1] != ligne:
            lignes.append(ligne)
    transcript = " ".join(lignes)
    if not transcript:
        raise RuntimeError("piste de sous-titres vide")
    return transcript


def generer_resume_ia(titre: str, transcript: str) -> dict:
    prompt = f"""Voici la transcription d'une vidéo de vulgarisation mathématique intitulée "{titre}".

Transcription :
{transcript[:12000]}

    La transcription peut être en français ou en anglais. Traduis en français le
    titre et le contenu avant de rédiger le résultat.
    Rédige en français un résumé structuré et captivant (5 à 8 phrases) adapté à
    des étudiants de niveau universitaire. Donne aussi 3 mots-clés (tags) courts
    en français et un niveau de difficulté parmi : Débutant, Intermédiaire, Avancé.

    Réponds UNIQUEMENT en JSON valide, sans texte ni balises autour, format exact :
    {{"titre_fr": "...", "resume": "...", "tags": ["...", "...", "..."], "niveau": "..."}}
"""
    r = httpx.post(GEMINI_URL, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
    r.raise_for_status()
    texte = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    texte = texte.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(texte)


def inserer_supabase(video: dict):
    url = f"{SUPABASE_URL}/rest/v1/videos_culture"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Accept-Profile": "culture",
        "Content-Profile": "culture",
        "Prefer": "resolution=merge-duplicates",
    }
    r = httpx.post(url, headers=headers, params={"on_conflict": "youtube_id"}, json=video, timeout=15)
    r.raise_for_status()


def main():
    for url in VIDEOS_A_AJOUTER:
        youtube_id = extraire_id(url)
        print(f"\n→ {youtube_id}")

        titre = recuperer_titre(youtube_id)
        print(f"  Titre : {titre}")

        donnees = DONNEES_MANUELLES.get(youtube_id)
        if not donnees:
            print("  ⚠️  Donnees manuelles absentes, video ignoree.")
            continue

        video = {
            "youtube_id": youtube_id,
            "titre_original": titre,
            "titre_affiche": donnees.get("titre_fr") or titre,
            "resume_ia": donnees.get("resume"),
            "tags": donnees.get("tags") or [],
            "niveau": donnees.get("niveau") or None,
            "publie": True,
        }

        inserer_supabase(video)
        print("  ✅ Insere / mis a jour dans Supabase.")


if __name__ == "__main__":
    main()
