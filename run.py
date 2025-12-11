from app import create_app
from flask import render_template
app = create_app()

# Définir une route pour les erreurs 404
@app.errorhandler(404)
def page_not_found(e):
    # Render a custom 404 page
    return render_template('404.html'), 404

if __name__ == "__main__":
    app.run(debug=True)