from flask import Flask, render_template
from backend.config.settings import settings
from backend.routes.web import web
from backend.middleware.auth import attach_user_context


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.register_blueprint(web)
    app.before_request(attach_user_context)

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("pages/404.html"), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
