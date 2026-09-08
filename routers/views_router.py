from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import supabase_client as db
import config

router = APIRouter()
templates = Jinja2Templates(directory="templates")
templates.env.globals["ASSET_VERSION"] = config.ASSET_VERSION

@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/devoirs")
async def devoirs(request: Request):
    return templates.TemplateResponse("devoirs.html", {"request": request})

@router.get("/examens")
async def examens(request: Request):
    return templates.TemplateResponse("examens.html", {"request": request})

@router.get("/td")
async def td(request: Request):
    return templates.TemplateResponse("td.html", {"request": request})

@router.get("/supports")
async def supports(request: Request):
    return templates.TemplateResponse("supports.html", {"request": request})

@router.get("/matieres")
async def matieres(request: Request):
    return templates.TemplateResponse("matieres.html", {"request": request})

@router.get("/matieres/{code_mat}")
async def matiere_pochette(request: Request, code_mat: str):
    try:
        matieres_liste = await db.fetch_view("Liste_matiere_niveau", "referentiel")
        matiere = next((m for m in matieres_liste if str(m.get("code_mat")) == code_mat), None)
    except Exception as e:
        print(f"ERREUR MATIERE POCHETTE: {e}")
        matiere = None

    async def compter(func, schema, params):
        try:
            resultats = await db.call_rpc(func, schema, params)
            return len(resultats) if isinstance(resultats, list) else 0
        except Exception as e:
            print(f"ERREUR COMPTEUR {func}: {e}")
            return 0

    compteurs = {
        "td": await compter("filtre_travaux_dirige_par_filtre", "pedagogie",
            {"p_code_annee": None, "p_code_niveau": None, "p_code_mat": code_mat, "p_sem_mat": None}),
        "devoirs": await compter("filtre_devoir_par_filtres", "controles",
            {"p_code_annee": None, "p_code_niveau": None, "p_code_mat": code_mat, "p_sem_mat": None}),
        "examens": await compter("filtre_examen_par_filtre", "controles",
            {"p_code_annee": None, "p_code_niveau": None, "p_code_mat": code_mat, "p_sem_mat": None, "p_session": None}),
        "supports": await compter("filtre_support_cours_par_filtre", "pedagogie",
            {"p_niveau_scolaire": None, "p_code_mat": code_mat}),
    }

    return templates.TemplateResponse("matiere_pochette.html", {
        "request": request,
        "matiere": matiere,
        "code_mat": code_mat,
        "compteurs": compteurs,
    })

@router.get("/etudiants")
async def etudiants(request: Request):
    return templates.TemplateResponse("etudiants.html", {"request": request})

@router.get("/promotions")
async def promotions(request: Request):
    return templates.TemplateResponse("promotions.html", {"request": request})

@router.get("/acces")
async def acces(request: Request):
    return templates.TemplateResponse("acces.html", {"request": request})

@router.get("/soumettre")
async def soumettre(request: Request):
    return templates.TemplateResponse("soumettre.html", {"request": request})

@router.get("/feedback")
async def feedback(request: Request):
    return templates.TemplateResponse("feedback.html", {"request": request})

@router.get("/inscription")
async def inscription(request: Request):
    return templates.TemplateResponse("inscription.html", {"request": request})

@router.get("/connexion")
async def connexion(request: Request):
    return templates.TemplateResponse("connexion.html", {"request": request})

@router.get("/mot-de-passe-oublie")
async def mot_de_passe_oublie(request: Request):
    return templates.TemplateResponse("mot_de_passe_oublie.html", {"request": request})

@router.get("/reinitialiser-mot-de-passe")
async def reinitialiser_mot_de_passe(request: Request):
    return templates.TemplateResponse("reinitialiser_mot_de_passe.html", {"request": request})

@router.get("/profil")
async def profil(request: Request):
    return templates.TemplateResponse("profil.html", {"request": request})

@router.get("/dashboard-admin")
async def dashboard_admin(request: Request):
    user = request.cookies.get("user_role")
    if user != "admin":
        return RedirectResponse(url="/connexion", status_code=302)
    return templates.TemplateResponse("dashboard_admin.html", {"request": request})

# ✅ ROUTE NOUVEAUTÉS
from datetime import datetime

@router.get("/nouveautes")
async def nouveautes(request: Request):
    try:
        matieres_actives = await db.fetch_recent(
            "Liste_matiere_niveau", "referentiel", "nom_mat", 5
        )
    except Exception as e:
        print(f"ERREUR MATIERES: {e}")
        matieres_actives = []

    return templates.TemplateResponse("nouveautes.html", {
        "request":          request,
        "matieres_actives": matieres_actives,
        "now":              datetime.now(),
    })

# ✅ ROUTES BEAUTÉ DES NOMBRES (culture mathématique)
NIVEAU_CLASSES = {
    "Débutant":       "niveau-debutant",
    "Intermédiaire":  "niveau-intermediaire",
    "Avancé":         "niveau-avance",
}

@router.get("/beaute-des-nombres")
async def beaute_des_nombres(request: Request):
    try:
        videos = await db.fetch_filtered("videos_culture", "culture", {"publie": "true"}, limit=100)
        videos.sort(key=lambda v: v.get("ordre_affichage") or 0)
        for v in videos:
            v["niveau_classe"] = NIVEAU_CLASSES.get(v.get("niveau"), "")
    except Exception as e:
        print(f"ERREUR VIDEOS CULTURE: {e}")
        videos = []
    return templates.TemplateResponse("beaute_des_nombres.html", {
        "request": request,
        "videos":  videos,
    })

@router.get("/beaute-des-nombres/{youtube_id}")
async def beaute_des_nombres_detail(request: Request, youtube_id: str):
    try:
        results = await db.fetch_filtered("videos_culture", "culture", {"youtube_id": youtube_id, "publie": "true"}, limit=1)
        video = results[0] if results else None
        if video:
            video["niveau_classe"] = NIVEAU_CLASSES.get(video.get("niveau"), "")
    except Exception as e:
        print(f"ERREUR VIDEO DETAIL: {e}")
        video = None
    return templates.TemplateResponse("beaute_des_nombres_detail.html", {
        "request": request,
        "video":   video,
    })