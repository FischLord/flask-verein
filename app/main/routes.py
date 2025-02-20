from flask import render_template, current_app, __version__, abort, url_for, make_response, send_from_directory, current_app
from app.main import main
import os
from markupsafe import Markup
from platform import python_version
from pip import __version__ as pip_version
from flask_login import __version__ as flask_login_version
from flask_sqlalchemy import __version__ as flask_sqlalchemy_version
from sqlalchemy import __version__ as sqlalchemy_version
from jinja2 import __version__ as jinja2_version
from dotenv import version as dotenv_version
from flask_wtf import __version__ as flask_wtf_version
from wtforms import __version__ as wtforms_version
import urllib.parse
from datetime import datetime


@main.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html",
        flask_version=__version__,
        python_version=python_version(),
        pip_version=pip_version,
        jinja2_version=jinja2_version,
        flask_login_version=flask_login_version,
        flask_sqlalchemy_version=flask_sqlalchemy_version,
        sqlalchemy_version=sqlalchemy_version,
        flask_wtf_version=flask_wtf_version,
        wtforms_version=wtforms_version,
        dotenv_version=dotenv_version.__version__,
        debug_enabled=os.environ.get("FLASK_DEBUG"),
    )

@main.app_context_processor
def inject_reports():
    berichte_path = os.path.join(current_app.static_folder, 'berichte')
    # Falls `app/static/berichte` nicht existiert, beenden wir früh
    if not os.path.isdir(berichte_path):
        return dict(reports=[])

    # Alle Ordner in `berichte/` einlesen
    folder_names = []
    for name in os.listdir(berichte_path):
        folder_path = os.path.join(berichte_path, name)
        # Nur wenn es ein Ordner ist, wird er aufgenommen
        if os.path.isdir(folder_path):
            folder_names.append(name)

    # Sortierung (optional, z.B. alphabetisch, oder Jahr absteigend)
    folder_names.sort(reverse=True)

    return dict(reports=folder_names)
@main.route('/berichte/<folder>')
def erlebnisberichte(folder):
    # Pfad zum gewünschten Ordner im static/berichte/-Verzeichnis
    base_path = os.path.join(current_app.static_folder, 'berichte')
    target_path = os.path.join(base_path, folder)

    # Prüfen, ob der Ordner existiert
    if not os.path.isdir(target_path):
        abort(404)

    # Prüfen, ob der Ordner Unterordner enthält
    subdirs = [name for name in os.listdir(target_path)
               if os.path.isdir(os.path.join(target_path, name))]

    if subdirs:
        # Es gibt Unterordner – wir behandeln dies als Mehrfachberichte (z. B. Jahr mit mehreren Events)
        events = []
        for subdir in sorted(subdirs):
            event_path = os.path.join(target_path, subdir)
            # Bilder einsammeln
            images = []
            for file_name in os.listdir(event_path):
                if file_name.lower().endswith(('.webp')):
                    images.append(file_name)
            images.sort()

            # Textdatei laden (optional)
            text_file_path = os.path.join(event_path, 'text.txt')
            text_content = ""
            if os.path.isfile(text_file_path):
                with open(text_file_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()

            events.append({
                'name': subdir,
                'images': images,
                'text': text_content,
            })

        # multi=True signalisiert im Template, dass mehrere Events vorhanden sind
        return render_template('main/berichte.html', folder_name=folder, events=events, multi=True)
    else:
        # Kein Unterordner – alter Einzelbericht-Modus
        images = []
        for file_name in os.listdir(target_path):
            if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                images.append(file_name)
        images.sort()

        # Textdatei laden (optional)
        text_file_path = os.path.join(target_path, 'text.txt')
        text_content = ""
        if os.path.isfile(text_file_path):
            with open(text_file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()

        # multi=False signalisiert im Template den Einzelbericht-Modus
        return render_template('main/berichte.html', folder_name=folder, images=images, text=text_content, multi=False)

# Janneck: Benötigt damit Zeilenumbrüche aus Text datei angezeigt werden
@main.app_template_filter('nl2br')
def nl2br_filter(s):
    if not s:
        return ""
    return Markup(s.replace('\n', '<br>'))




@main.route("/verein", methods=["GET"])
def verein():
    return render_template("main/verein.html")


@main.route("/kontakt", methods=["GET"])
def kontakt():
    return render_template("main/kontakt.html")


@main.route("/impressum", methods=["GET"])
def impressum():
    return render_template("main/impressum.html")

@main.route('/veranstaltungen')
def veranstaltungen():
    return render_template('main/veranstaltungen.html')

@main.route('/vereinsdaten')
def vereinsdaten():
    return render_template('main/vereinsdaten.html')

@main.route('/datenschutz')
def datenschutz():
    return render_template('main/datenschutz.html')

@main.route('/robots.txt')
def robots():
    return send_from_directory(current_app.static_folder, 'robots.txt')

def generate_sitemap(app):
    """
    Generiert eine Google-konforme XML Sitemap für alle öffentlichen Routen
    """
    base_url = "https://fahrverein-planetal.de"
    
    # XML Header mit allen erforderlichen Schemas
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
    sitemap_xml += '        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
    sitemap_xml += '        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9\n'
    sitemap_xml += '        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">\n'
    
    # Liste der Routen die ausgeschlossen werden sollen
    excluded_routes = {
        'static', 'admin', 'login', 'logout', 'register',
        'robots.txt', 'sitemap.xml'
    }
    
    # Dictionary für Seitenprioritäten und Änderungshäufigkeiten
    page_settings = {
        '/': {'priority': '1.0', 'changefreq': 'daily'},
        '/verein': {'priority': '0.8', 'changefreq': 'weekly'},
        '/veranstaltungen': {'priority': '0.8', 'changefreq': 'daily'},
        '/kontakt': {'priority': '0.7', 'changefreq': 'monthly'},
        '/vereinsdaten': {'priority': '0.7', 'changefreq': 'monthly'},
        '/formcenter/': {'priority': '0.5', 'changefreq': 'weekly'},
        '/impressum': {'priority': '0.3', 'changefreq': 'yearly'},
        '/datenschutz': {'priority': '0.3', 'changefreq': 'yearly'}
    }
    
    # Aktuelles Datum und Zeit im ISO 8601 Format
    current_datetime = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S+00:00')
    
    for rule in app.url_map.iter_rules():
        if "GET" in rule.methods and not rule.arguments:
            endpoint = rule.endpoint.split('.')[-1]
            path = rule.rule
            
            # Überspringe ausgeschlossene Routen
            if any(excl in endpoint for excl in excluded_routes) or \
               any(excl in path for excl in excluded_routes):
                continue
                
            url = urllib.parse.urljoin(base_url, path)
            settings = page_settings.get(path, {'priority': '0.5', 'changefreq': 'monthly'})
            
            sitemap_xml += '  <url>\n'
            sitemap_xml += f'    <loc>{url}</loc>\n'
            sitemap_xml += f'    <lastmod>{current_datetime}</lastmod>\n'
            sitemap_xml += f'    <changefreq>{settings["changefreq"]}</changefreq>\n'
            sitemap_xml += f'    <priority>{settings["priority"]}</priority>\n'
            sitemap_xml += '  </url>\n'
    
    sitemap_xml += '</urlset>'
    return sitemap_xml

@main.route('/sitemap.xml')
def sitemap():
    """Generate and serve sitemap.xml"""
    sitemap_xml = generate_sitemap(current_app)
    response = make_response(sitemap_xml)
    response.headers['Content-Type'] = 'application/xml'
    response.headers['X-Robots-Tag'] = 'noindex'
    return response