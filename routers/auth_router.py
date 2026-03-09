from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import bcrypt
import supabase_client as db
from config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_HEADERS
import httpx
from fastapi.responses import JSONResponse, RedirectResponse

router = APIRouter(tags=["auth"])

# ── Modèles ───────────────────────────────────────────────────────────────────

class InscriptionForm(BaseModel):
    nom:           str
    prenoms:       str
    email:         EmailStr
    mot_de_passe:  str
    role:          Optional[str] = "visiteur"

class ConnexionForm(BaseModel):
    email:        EmailStr
    mot_de_passe: str

# ── Helpers ───────────────────────────────────────────────────────────────────

def hasher_mdp(mdp: str) -> str:
    return bcrypt.hashpw(mdp.encode(), bcrypt.gensalt()).decode()

def verifier_mdp(mdp: str, hash: str) -> bool:
    return bcrypt.checkpw(mdp.encode(), hash.encode())

async def get_user_by_email(email: str):
    from config import SUPABASE_URL, SUPABASE_HEADERS
    import httpx
    h = SUPABASE_HEADERS.copy()
    h["Accept-Profile"] = "auth_app"
    url = f"{SUPABASE_URL}/rest/v1/utilisateurs"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url, headers=h, params={
            "select": "*",
            "email": f"eq.{email}"
        })
    r.raise_for_status()
    data = r.json()
    return data[0] if data else None

async def insert_user(payload: dict):
    url = f"{SUPABASE_URL}/rest/v1/utilisateurs"
    headers = SUPABASE_HEADERS.copy()
    headers["Content-Profile"] = "auth_app"
    headers["Prefer"] = "return=representation"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(url, headers=headers, json=payload)
    print("STATUS:", r.status_code)
    print("RESPONSE:", r.text)
    r.raise_for_status()
    return r.json()

async def update_connexion(user_id: int, ip: str):
    from config import SUPABASE_URL, SUPABASE_HEADERS
    import httpx
    h = SUPABASE_HEADERS.copy()
    h["Content-Profile"] = "auth_app"
    url = f"{SUPABASE_URL}/rest/v1/utilisateurs"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.patch(url, headers=h,
            params={"id": f"eq.{user_id}"},
            json={
                "derniere_connexion": datetime.utcnow().isoformat(),
                "ip_connexion": ip
            })
    r.raise_for_status()

# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/auth/inscription")
async def inscription(data: InscriptionForm, request: Request):
    # Vérifie si email déjà utilisé
    existant = await get_user_by_email(data.email)
    if existant:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé.")
    # Hash du mot de passe
    mdp_hash = hasher_mdp(data.mot_de_passe)
    payload = {
        "nom":            data.nom.upper(),
        "prenoms":        data.prenoms,
        "email":          data.email,
        "mot_de_passe":   mdp_hash,
        "role":           data.role,
        "statut":         "actif",
        "date_inscription": datetime.utcnow().isoformat(),
        "ip_connexion":   request.client.host
    }
    await insert_user(payload)
    return {"ok": True, "message": "Inscription réussie ! Vous pouvez maintenant vous connecter."}

@router.post("/auth/connexion")
async def connexion(data: ConnexionForm, request: Request):
    user = await get_user_by_email(data.email)
    if not user:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")
    if not verifier_mdp(data.mot_de_passe, user["mot_de_passe"]):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")
    if user["statut"] != "actif":
        raise HTTPException(status_code=403, detail="Votre compte est inactif ou banni.")
    # Mise à jour dernière connexion
    await update_connexion(user["id"], request.client.host)
    response = JSONResponse({
        "ok": True,
        "message": f"Bienvenue {user['prenoms']} {user['nom']} !",
        "user": {
            "id": user["id"],
            "nom": user["nom"],
            "prenoms": user["prenoms"],
            "email": user["email"],
            "role": user["role"],
            "statut": user["statut"],
        }
    })
    response.set_cookie(key="user_role", value=user["role"], httponly=True)
    response.set_cookie(key="user_id", value=str(user["id"]), httponly=True)
    return response


@router.get("/auth/utilisateurs")
async def get_utilisateurs():
    """Tableau de bord admin — liste tous les utilisateurs"""
    return await db.fetch_view("vue_utilisateurs", "auth_app")

class ChangerRole(BaseModel):
    role: str

@router.patch("/auth/role/{user_id}")
async def changer_role(user_id: int, data: ChangerRole):
    from config import SUPABASE_URL, SUPABASE_HEADERS
    import httpx
    h = SUPABASE_HEADERS.copy()
    h["Content-Profile"] = "auth_app"
    url = f"{SUPABASE_URL}/rest/v1/utilisateurs"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.patch(
            url,
            headers=h,
            params={"id": f"eq.{user_id}"},
            json={"role": data.role}
        )
    r.raise_for_status()
    return {"ok": True, "message": f"Rôle mis à jour : {data.role}"}

class ModifierProfil(BaseModel):
    nom:           Optional[str] = None
    prenoms:       Optional[str] = None
    email:         Optional[EmailStr] = None
    mot_de_passe:  Optional[str] = None
    ancien_mot_de_passe: Optional[str] = None

@router.patch("/auth/profil/{user_id}")
async def modifier_profil(user_id: int, data: ModifierProfil):
    from config import SUPABASE_URL, SUPABASE_HEADERS
    import httpx

    # Récupérer l'utilisateur actuel
    h = SUPABASE_HEADERS.copy()
    h["Accept-Profile"] = "auth_app"
    url = f"{SUPABASE_URL}/rest/v1/utilisateurs"

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(url, headers=h, params={
            "select": "*", "id": f"eq.{user_id}"
        })
    r.raise_for_status()
    users = r.json()
    if not users:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    user = users[0]

    payload = {}

    # Modification nom / prenoms
    if data.nom:
        payload["nom"] = data.nom.upper()
    if data.prenoms:
        payload["prenoms"] = data.prenoms

    # Modification email — vérifier qu'il n'est pas déjà pris
    if data.email and data.email != user["email"]:
        existant = await get_user_by_email(data.email)
        if existant:
            raise HTTPException(status_code=400, detail="Cet email est déjà utilisé.")
        payload["email"] = data.email

    # Modification mot de passe — vérifier l'ancien
    if data.mot_de_passe:
        if not data.ancien_mot_de_passe:
            raise HTTPException(status_code=400, detail="Ancien mot de passe requis.")
        if not verifier_mdp(data.ancien_mot_de_passe, user["mot_de_passe"]):
            raise HTTPException(status_code=401, detail="Ancien mot de passe incorrect.")
        payload["mot_de_passe"] = hasher_mdp(data.mot_de_passe)

    if not payload:
        raise HTTPException(status_code=400, detail="Aucune modification détectée.")

    # Appliquer les modifications
    h2 = SUPABASE_HEADERS.copy()
    h2["Content-Profile"] = "auth_app"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.patch(url, headers=h2,
            params={"id": f"eq.{user_id}"},
            json=payload
        )
    r.raise_for_status()

    # Retourner les nouvelles infos
    return {
        "ok": True,
        "message": "Profil mis à jour avec succès.",
        "user": {
            "id": user_id,
            "nom": payload.get("nom", user["nom"]),
            "prenoms": payload.get("prenoms", user["prenoms"]),
            "email": payload.get("email", user["email"]),
            "role": user["role"],
            "statut": user["statut"],
        }
    }