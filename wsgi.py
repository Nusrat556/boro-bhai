"""WSGI entry point for hosting BORO BHAI in a lightweight production setup."""

from api.app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
