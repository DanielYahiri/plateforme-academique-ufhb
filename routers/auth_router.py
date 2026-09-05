from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta, timezone
import bcrypt
import resend
from jose import JWTError, jwt
import supabase_client as db
from config import (
    SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_HEADERS, SUPABASE_SERVICE_KEY,
    RESEND_API_KEY, EMAIL_EXPEDITEUR, APP_BASE_URL, PASSWORD_RESET_SECRET,
)
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

class DemandeReinitialisation(BaseModel):
    email: EmailStr

class NouveauMotDePasse(BaseModel):
    token: str
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
    if len(data.mot_de_passe) < 6:
        raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins 6 caractères.")

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
        # Un visiteur ne peut jamais choisir son rôle depuis le formulaire public.
        "role":           "visiteur",
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

@router.post("/auth/mot-de-passe-oublie")
async def demander_reinitialisation(data: DemandeReinitialisation):
    user = await get_user_by_email(data.email)

    if not user:
        print(f"[RESET] Email inconnu: {data.email}")
        return {"ok": True, "message": "Si cette adresse est associée à un compte, un lien de réinitialisation a été envoyé."}

    if not RESEND_API_KEY:
        print(f"[RESET] Clé Resend absente pour {data.email}")
        return {"ok": False, "detail": "Le service d'email n'est pas configuré pour l'instant."}

    if not EMAIL_EXPEDITEUR:
        print(f"[RESET] Expéditeur email absent pour {data.email}")
        return {"ok": False, "detail": "L'expéditeur email n'est pas configuré."}

    try:
        token = jwt.encode(
            {"sub": str(user["id"]), "email": user["email"],
             "exp": datetime.now(timezone.utc) + timedelta(minutes=30)},
            PASSWORD_RESET_SECRET,
            algorithm="HS256",
        )
        lien = f"{APP_BASE_URL}/reinitialiser-mot-de-passe?token={token}"
        resend.api_key = RESEND_API_KEY
        response = resend.Emails.send({
            "from": f"Classe Étoile <{EMAIL_EXPEDITEUR}>",
            "to": data.email,
            "subject": "Réinitialisation de votre mot de passe",
            "html": f"<p>Bonjour,</p><p>Cliquez sur le lien suivant pour choisir un nouveau mot de passe :</p><p><a href=\"{lien}\">Réinitialiser mon mot de passe</a></p><p>Ce lien expire dans 30 minutes.</p>",
        })
        print(f"[RESET] Email envoyé à {data.email} -> {response}")
    except Exception as exc:
        print(f"[RESET] ERREUR ENVOI EMAIL pour {data.email}: {exc}")
        return {"ok": False, "detail": "Impossible d'envoyer le mail pour le moment."}

    return {"ok": True, "message": "Si cette adresse est associée à un compte, un lien de réinitialisation a été envoyé."}

@router.post("/auth/reinitialiser-mot-de-passe")
async def appliquer_reinitialisation(data: NouveauMotDePasse):
    if len(data.mot_de_passe) < 6:
        raise HTTPException(status_code=400, detail="Le mot de passe doit contenir au moins 6 caractères.")
    try:
        payload = jwt.decode(data.token, PASSWORD_RESET_SECRET, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=400, detail="Le lien de réinitialisation est invalide ou expiré.")

    url = f"{SUPABASE_URL}/rest/v1/utilisateurs"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Content-Profile": "auth_app",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.patch(
            url,
            headers=headers,
            params={"id": f"eq.{user_id}"},
            json={"mot_de_passe": hasher_mdp(data.mot_de_passe)},
        )
    response.raise_for_status()
    return {"ok": True, "message": "Mot de passe réinitialisé. Vous pouvez vous connecter."}


@router.get("/auth/utilisateurs")
async def get_utilisateurs(request: Request):
    """Tableau de bord admin — liste tous les utilisateurs"""
    if request.cookies.get("user_role") != "admin":
        raise HTTPException(status_code=403, detail="Accès administrateur requis.")
    return await db.fetch_view("vue_utilisateurs", "auth_app")

class ChangerRole(BaseModel):
    role: str

@router.patch("/auth/role/{user_id}")
async def changer_role(user_id: int, data: ChangerRole, request: Request):
    if request.cookies.get("user_role") != "admin":
        raise HTTPException(status_code=403, detail="Accès administrateur requis.")
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
async def modifier_profil(user_id: int, data: ModifierProfil, request: Request):
    if request.cookies.get("user_id") != str(user_id):
        raise HTTPException(status_code=403, detail="Vous ne pouvez modifier que votre propre profil.")
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