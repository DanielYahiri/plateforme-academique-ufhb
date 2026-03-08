#  CONFIGURATION


import os

SUPABASE_URL     = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
SUPABASE_HEADERS = {
    "apikey":        SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type":  "application/json",
}
GMAIL_USER         = os.environ.get("GMAIL_USER")
GMAIL_PASSWORD     = os.environ.get("GMAIL_PASSWORD")
EMAIL_DESTINATAIRE = os.environ.get("EMAIL_DESTINATAIRE")
APP_NAME           = "Classe-Etoile -plateforme -academique-ufhb"
APP_SLOGAN         = "Ressources pédagogiques de l'UFHB"
UNIVERSITE         = "Université Félix Houphouët-Boigny"