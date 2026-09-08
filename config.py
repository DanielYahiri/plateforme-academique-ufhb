#  CONFIGURATION
from dotenv import load_dotenv
load_dotenv()

import os

SUPABASE_URL             = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY        = os.environ.get("SUPABASE_ANON_KEY")
SUPABASE_PUBLISHABLE_KEY = os.environ.get("SUPABASE_PUBLISHABLE_KEY", SUPABASE_ANON_KEY)
SUPABASE_SERVICE_KEY     = os.environ.get("SUPABASE_SERVICE_KEY")
SUPABASE_JWKS_URL        = os.environ.get("SUPABASE_JWKS_URL")

SUPABASE_HEADERS = {
    "apikey":        SUPABASE_PUBLISHABLE_KEY,
    "Authorization": f"Bearer {SUPABASE_PUBLISHABLE_KEY}",
    "Content-Type":  "application/json",
}

SUPABASE_SERVICE_HEADERS = {
    "apikey":        SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type":  "application/json",
}

GMAIL_USER         = os.environ.get("GMAIL_USER")
GMAIL_PASSWORD     = os.environ.get("GMAIL_PASSWORD")
EMAIL_DESTINATAIRE = os.environ.get("EMAIL_DESTINATAIRE")
APP_NAME           = "Classe-Etoile -plateforme -academique-ufhb"
APP_SLOGAN         = "Ressources pédagogiques de l'UFHB"
UNIVERSITE         = "Université Félix Houphouët-Boigny"
RESEND_API_KEY     = os.environ.get("RESEND_API_KEY")
EMAIL_EXPEDITEUR   = os.environ.get("EMAIL_EXPEDITEUR", "bohdaniel946@danielyahiri.online")
GEMINI_API_KEY      = os.environ.get("GEMINI_API_KEY")
PASSWORD_RESET_SECRET = os.environ.get("PASSWORD_RESET_SECRET", "change-moi-avec-une-cle-secrete-assez-longue")
APP_BASE_URL        = os.environ.get("APP_BASE_URL", "https://danielyahiri.online")
import time
# Par defaut, se base sur l'heure de demarrage du process : change a chaque
# redemarrage (donc a chaque deploiement Render), sans jamais avoir a y penser.
# ASSET_VERSION peut toujours etre force via une variable d'environnement si besoin.
ASSET_VERSION       = os.environ.get("ASSET_VERSION", str(int(time.time())))