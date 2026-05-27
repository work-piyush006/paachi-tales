from datetime import timedelta
from flask import Flask, render_template
from backend.config.settings import settings
from backend.routes.web import web
from backend.routes.admin import admin
from backend.middleware.auth import attach_user_context


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=14)
    app.register_blueprint(web)
    app.register_blueprint(admin)
    app.before_request(attach_user_context)

    error_map = {
        400: "Error 400 — Bad request.", 401: "Error 401 — Login required.", 403: "Error 403 — Access denied.",
        404: "Error 404 — Product not found.", 409: "Error 409 — Conflict.", 413: "Error 413 — Media file too large.",
        422: "Error 422 — Invalid data.", 500: "Error 500 — Internal server issue.", 503: "Error 503 — Service unavailable."
    }
    for code, msg in error_map.items():
        app.register_error_handler(code, lambda e, c=code, m=msg: (render_template("pages/error.html", code=c, message=m), c))
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
