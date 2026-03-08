from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import httpx
from config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_HEADERS

router = APIRouter(tags=["upload"])

BUCKETS = {
    "devoir":        "sujet_devoir",
    "examen":        "sujet_examen",
    "td":            "sujet_de_TD",
    "support_cours": "support_cours",
}

SCHEMAS = {
    "devoir":        "controles",
    "examen":        "controles",
    "td":            "pedagogie",
    "support_cours": "pedagogie",
}

TABLES = {
    "devoir":        "devoir",
    "examen":        "examen",
    "td":            "td",
    "support_cours": "support_cours",
}

CLE_PRIMAIRE = {
    "devoir":        "code_dev",
    "examen":        "id_examen",
    "td":            "id_TD",
    "support_cours": "code_support",
}

COLONNE_LIEN = {
    "devoir":        "sujet_dev",
    "examen":        "sujet_exam",
    "td":            "sujet_td",
    "support_cours": "support_cours",
}

def storage_headers():
    return {
        "apikey":        SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    }

def db_headers(schema: str):
    h = SUPABASE_HEADERS.copy()
    h["Content-Profile"] = schema
    h["Prefer"] = "return=representation"
    return h

async def upload_to_bucket(bucket: str, folder: str, filename: str, content: bytes, content_type: str) -> str:
    path = f"{folder}/{filename}"
    url  = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            url,
            headers={**storage_headers(), "Content-Type": content_type},
            content=content
        )
    if r.status_code not in [200, 201]:
        raise HTTPException(status_code=500, detail=f"Upload échoué : {r.text}")
    return f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}"

async def delete_from_bucket(bucket: str, path: str):
    url = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{path}"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.delete(url, headers=storage_headers())
    return r.status_code

async def insert_row(schema: str, table: str, payload: dict):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(url, headers=db_headers(schema), json=payload)
    if r.status_code not in [200, 201]:
        raise HTTPException(status_code=500, detail=f"Insertion échouée : {r.text}")
    return r.json()

async def update_row(schema: str, table: str, cle: str, valeur: str, payload: dict):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    h   = db_headers(schema)
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.patch(
            url, headers=h,
            params={cle: f"eq.{valeur}"},
            json=payload
        )
    if r.status_code not in [200, 204]:
        raise HTTPException(status_code=500, detail=f"Mise à jour échouée : {r.text}")
    return {"ok": True}

async def delete_row(schema: str, table: str, cle: str, valeur: str):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    h   = SUPABASE_HEADERS.copy()
    h["Content-Profile"] = schema
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.delete(
            url, headers=h,
            params={cle: f"eq.{valeur}"}
        )
    if r.status_code not in [200, 204]:
        raise HTTPException(status_code=500, detail=f"Suppression échouée : {r.text}")
    return {"ok": True}

# ── AJOUTER ───────────────────────────────────────────────────────────────────
@router.post("/upload/ajouter")
async def ajouter_document(
    type_doc:    str           = Form(...),
    folder:      str           = Form(...),
    code_mat:    str           = Form(...),
    code_niveau: Optional[str] = Form(None),
    code_annee:  Optional[int] = Form(None),
    num_dev:     Optional[int] = Form(None),
    session:     Optional[int] = Form(None),
    sem_td:      Optional[int] = Form(None),
    fichier:     UploadFile    = File(...),
):
    if type_doc not in BUCKETS:
        raise HTTPException(status_code=400, detail="Type de document invalide.")

    content      = await fichier.read()
    content_type = fichier.content_type or "application/pdf"
    filename     = fichier.filename

    bucket     = BUCKETS[type_doc]
    public_url = await upload_to_bucket(bucket, folder, filename, content, content_type)

    schema = SCHEMAS[type_doc]
    table  = TABLES[type_doc]

    if type_doc == "devoir":
        if not code_niveau or not code_annee or num_dev is None:
            raise HTTPException(status_code=400, detail="code_niveau, code_annee et num_dev sont obligatoires.")
        payload = {
            "code_mat":    code_mat,
            "code_niveau": code_niveau,
            "code_annee":  code_annee,
            "num_dev":     num_dev,
            "sujet_dev":   public_url,
        }
    elif type_doc == "examen":
        if not code_niveau or not code_annee or session is None:
            raise HTTPException(status_code=400, detail="code_niveau, code_annee et session sont obligatoires.")
        payload = {
            "code_mat":    code_mat,
            "code_niveau": code_niveau,
            "code_annee":  code_annee,
            "session":     session,
            "sujet_exam":  public_url,
        }
    elif type_doc == "td":
        if not code_niveau or not code_annee or sem_td is None:
            raise HTTPException(status_code=400, detail="code_niveau, code_annee et sem_td sont obligatoires.")
        payload = {
            "code_mat":    code_mat,
            "code_niveau": code_niveau,
            "code_annee":  code_annee,
            "sem_td":      sem_td,
            "sujet_td":    public_url,
        }
    elif type_doc == "support_cours":
        payload = {
            "code_mat":      code_mat,
            "support_cours": public_url,
        }

    await insert_row(schema, table, payload)
    return {"ok": True, "message": "Document ajouté avec succès !", "url": public_url}

# ── MODIFIER ──────────────────────────────────────────────────────────────────
@router.patch("/upload/modifier")
async def modifier_document(
    type_doc: str        = Form(...),
    code_id:  str        = Form(...),
    folder:   str        = Form(...),
    fichier:  UploadFile = File(...),
):
    if type_doc not in BUCKETS:
        raise HTTPException(status_code=400, detail="Type de document invalide.")

    content      = await fichier.read()
    content_type = fichier.content_type or "application/pdf"
    filename     = fichier.filename

    bucket     = BUCKETS[type_doc]
    public_url = await upload_to_bucket(bucket, folder, filename, content, content_type)

    schema = SCHEMAS[type_doc]
    table  = TABLES[type_doc]
    cle    = CLE_PRIMAIRE[type_doc]
    lien   = COLONNE_LIEN[type_doc]

    await update_row(schema, table, cle, code_id, {lien: public_url})
    return {"ok": True, "message": "Document mis à jour !", "url": public_url}

# ── SUPPRIMER ─────────────────────────────────────────────────────────────────
@router.delete("/upload/supprimer")
async def supprimer_document(
    type_doc: str = Form(...),
    code_id:  str = Form(...),
    path:     str = Form(...),
):
    if type_doc not in BUCKETS:
        raise HTTPException(status_code=400, detail="Type de document invalide.")

    bucket = BUCKETS[type_doc]
    schema = SCHEMAS[type_doc]
    table  = TABLES[type_doc]
    cle    = CLE_PRIMAIRE[type_doc]

    await delete_from_bucket(bucket, path)
    await delete_row(schema, table, cle, code_id)
    return {"ok": True, "message": "Document supprimé avec succès !"}