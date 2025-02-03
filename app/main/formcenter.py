# app/main/formcenter.py
from flask import Blueprint, render_template, current_app
import os

formcenter = Blueprint('formcenter', __name__, template_folder='templates')

@formcenter.route('/', methods=['GET'])
def index():
    # Ordner, in dem die Formulare abgelegt werden (z. B. PDFs)
    docs_dir = os.path.join(current_app.root_path, 'static', 'forms')
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)
    allowed_extensions = {'pdf'}  # Erlaubt aktuell nur PDFs
    files = []
    for f in os.listdir(docs_dir):
        if f.split('.')[-1].lower() in allowed_extensions:
            full_path = os.path.join(docs_dir, f)
            size = os.path.getsize(full_path) / 1024  # Größe in KB
            files.append({
                'name': f,
                'size': f"{size:.1f} KB",
                'type': "Adobe Acrobat Dokument"
            })
    # Sortierung nach Dateinamen (anpassbar)
    files = sorted(files, key=lambda x: x['name'])
    return render_template('main/formcenter.html', files=files)
