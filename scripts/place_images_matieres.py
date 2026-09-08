"""
Placement final des images matières
─────────────────────────────────────
Lit scripts/data/matieres_prompts_images.csv (référence niveau/semestre/code_mat/nom_fichier),
cherche l'image correspondante dans data/matieres_images/{code_mat}.* et la copie/renomme
vers static/img/matieres/{nom_fichier} — le nom exact attendu par les cartes.

Lancer depuis la racine du projet :
    python scripts/place_images_matieres.py
"""

import csv
import os
import shutil

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(RACINE, "scripts", "data", "matieres_prompts_images.csv")
DOSSIER_SOURCE = os.path.join(RACINE, "data", "matieres_images")
DOSSIER_DEST = os.path.join(RACINE, "static", "img", "matieres")

EXTENSIONS_ACCEPTEES = [".jpg", ".jpeg", ".png", ".webp"]


def trouver_source(code_mat: str):
    for ext in EXTENSIONS_ACCEPTEES:
        chemin = os.path.join(DOSSIER_SOURCE, f"{code_mat}{ext}")
        if os.path.isfile(chemin):
            return chemin
    return None


def main():
    os.makedirs(DOSSIER_DEST, exist_ok=True)

    with open(CSV_PATH, encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))

    trouvees, manquantes = [], []

    for ligne in lignes:
        code_mat = ligne["code_mat"]
        nom_fichier = ligne["nom_fichier"]
        source = trouver_source(code_mat)

        if source is None:
            manquantes.append(f"{code_mat} — {ligne['nom_mat']}")
            continue

        destination = os.path.join(DOSSIER_DEST, nom_fichier)
        shutil.copyfile(source, destination)
        trouvees.append(nom_fichier)

    print(f"✅ {len(trouvees)} image(s) placée(s) dans static/img/matieres/\n")

    if manquantes:
        print(f"⚠️  {len(manquantes)} manquante(s) :")
        for m in manquantes:
            print(f"   - {m}")
    else:
        print("🎉 Toutes les matières ont leur image !")


if __name__ == "__main__":
    main()