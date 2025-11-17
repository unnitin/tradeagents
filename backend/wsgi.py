"""Gunicorn entrypoint for the backend Flask app."""
from __future__ import annotations

from backend import create_app

app = create_app()

if __name__ == "__main__":
    # Useful for local debugging; use Gunicorn in production.
    app.run(host="0.0.0.0", port=8000, debug=False)
