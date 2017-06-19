from app import app
import os

if __name__ == "__main__":
    app.jinja_env.auto_reload = True
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.run(
        debug=True,
        port=int(os.environ.get("PORT", "3000")),
        host="0.0.0.0"
    )
