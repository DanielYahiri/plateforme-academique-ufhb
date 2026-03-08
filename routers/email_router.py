from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from config import GMAIL_USER, GMAIL_PASSWORD, EMAIL_DESTINATAIRE, APP_NAME

router = APIRouter(tags=["email"])

class SoumissionSujet(BaseModel):
    expediteur_nom:   str
    expediteur_email: EmailStr
    niveau:           str
    matiere:          str
    type_document:    str
    annee:            Optional[str] = None
    description:      str
    lien_fichier:     Optional[str] = None

class FeedbackForm(BaseModel):
    nom:     str
    email:   EmailStr
    sujet:   str
    message: str
    note:    Optional[int] = None

import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=2)

def _send_email_sync(to: str, subject: str, html_body: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_USER
    msg["To"]      = to
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, to, msg.as_string())

async def send_email(to: str, subject: str, html_body: str):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, _send_email_sync, to, subject, html_body)
def wrap(title: str, content: str) -> str:
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body style="font-family:Segoe UI,Arial,sans-serif;background:#f4f6f7;padding:30px;">
<div style="max-width:620px;margin:auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.08);">
  <div style="background:linear-gradient(135deg,#1A5276,#2E86C1);padding:28px 32px;">
    <h1 style="color:white;margin:0;font-size:20px;">🎓 {APP_NAME}</h1>
    <p style="color:rgba(255,255,255,.75);margin:4px 0 0;font-size:13px;">{title}</p>
  </div>
  <div style="padding:28px 32px;color:#1C2833;font-size:14px;line-height:1.7;">{content}</div>
  <div style="background:#f4f6f7;padding:16px 32px;font-size:11px;color:#999;text-align:center;">
    {APP_NAME} · {datetime.now().strftime('%d/%m/%Y %H:%M')}
  </div>
</div></body></html>"""

@router.post("/email/sujet")
async def envoyer_sujet(data: SoumissionSujet):
    try:
        types = {"devoir":"Devoir","examen":"Examen","td":"Travail Dirigé","support":"Support de Cours"}
        lien  = f'<a href="{data.lien_fichier}">{data.lien_fichier}</a>' if data.lien_fichier else "<em>Aucun</em>"
        rows  = [("Expéditeur", data.expediteur_nom), ("Email", data.expediteur_email),
                 ("Type", types.get(data.type_document, data.type_document)),
                 ("Niveau", data.niveau), ("Matière", data.matiere),
                 ("Année", data.annee or "—"), ("Lien", lien)]
        table = "".join(f'<tr style="border-bottom:1px solid #eee;"><td style="padding:9px 12px;font-weight:bold;color:#1A5276;width:35%;">{k}</td><td style="padding:9px 12px;">{v}</td></tr>' for k,v in rows)
        content = f'<p>Nouvelle soumission reçue.</p><table style="width:100%;border-collapse:collapse;">{table}</table><div style="background:#EBF5FB;border-left:4px solid #2E86C1;padding:14px;margin-top:12px;"><strong>Description :</strong><br>{data.description}</div>'
        send_email(EMAIL_DESTINATAIRE, f"[Soumission] {types.get(data.type_document)} — {data.matiere} ({data.niveau})", wrap("Nouvelle soumission", content))
        send_email(data.expediteur_email, f"[{APP_NAME}] Confirmation de soumission",
            wrap("Accusé de réception", f"<p>Bonjour <strong>{data.expediteur_nom}</strong>,</p><p>Votre soumission a bien été reçue. Merci !</p>"))
        return {"ok": True, "message": "Soumission envoyée avec succès !"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/email/feedback")
async def envoyer_feedback(data: FeedbackForm):
    try:
        stars = "⭐" * (data.note or 0) or "Non renseigné"
        rows  = [("Nom", data.nom), ("Email", data.email), ("Sujet", data.sujet), ("Note", stars)]
        table = "".join(f'<tr style="border-bottom:1px solid #eee;"><td style="padding:9px 12px;font-weight:bold;color:#1A5276;width:30%;">{k}</td><td style="padding:9px 12px;">{v}</td></tr>' for k,v in rows)
        content = f'<table style="width:100%;border-collapse:collapse;">{table}</table><div style="background:#EBF5FB;border-left:4px solid #2E86C1;padding:14px;margin-top:12px;"><strong>Message :</strong><br>{data.message}</div>'
        send_email(EMAIL_DESTINATAIRE, f"[Feedback] {data.sujet} — {data.nom}", wrap("Nouveau feedback", content))
        send_email(data.email, f"[{APP_NAME}] Merci pour votre feedback",
            wrap("Feedback reçu", f"<p>Bonjour <strong>{data.nom}</strong>,</p><p>Merci pour votre retour !</p>"))
        return {"ok": True, "message": "Feedback envoyé avec succès !"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))