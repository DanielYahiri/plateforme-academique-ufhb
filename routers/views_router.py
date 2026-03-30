from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import supabase_client as db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

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
@router.get("/nouveautes")
async def nouveautes(request: Request):
    try:
        derniers_devoirs  = await db.fetch_recent("devoir",        "controles", "code_annee", 5)
    except Exception:
        derniers_devoirs  = []
    try:
        derniers_examens  = await db.fetch_recent("examen",        "controles", "code_annee", 5)
    except Exception:
        derniers_examens  = []
    try:
        derniers_tds      = await db.fetch_recent("td",            "pedagogie", "code_annee", 5)
    except Exception:
        derniers_tds      = []
    try:
        derniers_supports = await db.fetch_recent("support_cours", "pedagogie", "code_support", 5)
    except Exception:
        derniers_supports = []
    try:
        nouvelle_maquette = await db.fetch_filtered("Matiere (UE)", "referentiel", {"actif": "true"})
    except Exception:
        nouvelle_maquette = []

    return templates.TemplateResponse("nouveautes.html", {
        "request":           request,
        "derniers_devoirs":  derniers_devoirs,
        "derniers_examens":  derniers_examens,
        "derniers_tds":      derniers_tds,
        "derniers_supports": derniers_supports,
        "nouvelle_maquette": nouvelle_maquette,
    })