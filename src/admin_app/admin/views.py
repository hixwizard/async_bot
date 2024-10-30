from flask import Response, redirect, url_for

from . import app


# Flask views
@app.route('/')
def index() -> Response:
    """Перенаправляет пользователя на страницу '/admin'."""
    return redirect(url_for('admin.index'))
