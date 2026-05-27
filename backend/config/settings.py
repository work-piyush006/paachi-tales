import os


class Settings:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPER_ADMIN_EMAIL = "paachitales.store@gmail.com"
    APP_TITLE = "Paachi Tales"


settings = Settings()
