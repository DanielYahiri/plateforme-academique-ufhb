from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import httpx
import supabase_client as db

router = APIRouter(tags=["data"])

class FiltreDevoir(BaseModel):
    p_code_annee:  Optional[int] = None
    p_code_niveau: Optional[str] = None
    p_code_mat:    Optional[str] = None
    p_sem_mat:     Optional[int] = None

class FiltreExamen(BaseModel):
    p_code_annee:  Optional[int] = None
    p_code_niveau: Optional[str] = None
    p_code_mat:    Optional[str] = None
    p_sem_mat:     Optional[int] = None
    p_session:     Optional[int] = None

class FiltreTD(BaseModel):
    p_code_annee:  Optional[int] = None
    p_code_niveau: Optional[str] = None
    p_code_mat:    Optional[str] = None
    p_sem_mat:     Optional[int] = None

class FiltreSupport(BaseModel):
    p_niveau_scolaire: Optional[str] = None
    p_code_mat:        Optional[str] = None

class FiltreMatiere(BaseModel):
    p_niveau_scolaire: Optional[str] = None
    p_sem_mat:         Optional[int] = None

class FiltreEtudiant(BaseModel):
    p_licence_obtenue: Optional[int] = None
    p_genre:           Optional[str] = None

async def safe(coro):
    try:
        return await coro
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

@router.get("/devoirs")
async def get_devoirs():
    return await safe(db.fetch_view("liste_des_devoirs_par_niveau_et_matiere", "controles"))

@router.post("/devoirs/filter")
async def filter_devoirs(f: FiltreDevoir):
    return await safe(db.call_rpc("filtre_devoir_par_filtres", "controles", f.model_dump()))

@router.get("/examens")
async def get_examens():
    return await safe(db.fetch_view("Liste_examens_niveau_matiere", "controles"))

@router.post("/examens/filter")
async def filter_examens(f: FiltreExamen):
    return await safe(db.call_rpc("filtre_examen_par_filtre", "controles", f.model_dump()))

@router.get("/td")
async def get_td():
    return await safe(db.fetch_view("Liste_travaux_dirigés_niveau", "pedagogie"))

@router.post("/td/filter")
async def filter_td(f: FiltreTD):
    return await safe(db.call_rpc("filtre_travaux_dirige_par_filtre", "pedagogie", f.model_dump()))

@router.get("/supports")
async def get_supports():
    return await safe(db.fetch_view("Liste_supports_cours_niveau", "pedagogie"))

@router.post("/supports/filter")
async def filter_supports(f: FiltreSupport):
    return await safe(db.call_rpc("filtre_support_cours_par_filtre", "pedagogie", f.model_dump()))

@router.get("/matieres")
async def get_matieres():
    return await safe(db.fetch_view("Liste_matiere_niveau", "referentiel"))

@router.post("/matieres/filter")
async def filter_matieres(f: FiltreMatiere):
    return await safe(db.call_rpc("filtre_matiere", "referentiel", f.model_dump()))

@router.get("/etudiants")
async def get_etudiants():
    return await safe(db.fetch_view("Liste_etudiants_admis_annee_promo", "referentiel"))

@router.post("/etudiants/filter")
async def filter_etudiants(f: FiltreEtudiant):
    return await safe(db.call_rpc("filtre_etudiant_admis", "referentiel", f.model_dump()))

@router.get("/promotions")
async def get_promotions():
    return await safe(db.fetch_view("Nombre_admis_promotion_sortante", "referentiel"))

@router.get("/acces")
async def get_acces():
    return await safe(db.fetch_view("Condition_acces_niveau", "referentiel",100))

@router.get("/download")
async def download_file(url: str, filename: str):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
    if r.status_code != 200:
        raise HTTPException(status_code=404, detail="Fichier introuvable.")
    return StreamingResponse(
        iter([r.content]),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )