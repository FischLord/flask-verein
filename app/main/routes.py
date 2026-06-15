from flask import render_template, current_app, abort, make_response, send_from_directory
from app.main import main
from app import db
from app.models import Termin, Vorstandsmitglied, Bericht
from markupsafe import Markup, escape
import urllib.parse
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError


@main.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@main.app_context_processor
def inject_reports():
    """Jahre veroeffentlichter Berichte (absteigend) fuers Nav-Dropdown."""
    try:
        rows = (
            db.session.query(Bericht.jahr)
            .filter_by(veroeffentlicht=True)
            .distinct()
            .order_by(Bericht.jahr.desc())
            .all()
        )
    except SQLAlchemyError:
        # Context-Processor laeuft auf jeder Seite -> defensiv leer bleiben.
        return dict(reports=[])
    return dict(reports=[row[0] for row in rows])


@main.route('/berichte/<int:jahr>')
def erlebnisberichte(jahr):
    """Alle veroeffentlichten Berichte eines Jahres auf einer Seite."""
    berichte = (
        Bericht.query
        .filter_by(jahr=jahr, veroeffentlicht=True)
        .order_by(Bericht.reihenfolge.asc(), Bericht.titel.asc())
        .all()
    )
    if not berichte:
        abort(404)
    return render_template(
        'main/berichte.html', jahr=jahr, berichte=berichte
    )

# Janneck: Benötigt damit Zeilenumbrüche aus Text datei angezeigt werden
@main.app_template_filter('nl2br')
def nl2br_filter(s):
    if not s:
        return ""
    # Erst HTML escapen (neutralisiert rohes HTML/<script>), dann auf dem
    # escapten Klartext Zeilenumbrueche in echte <br> umwandeln.
    escaped = str(escape(s))
    return Markup(escaped.replace('\n', '<br>\n'))




@main.route("/verein", methods=["GET"])
def verein():
    return render_template("main/verein.html")


@main.route("/kontakt", methods=["GET"])
def kontakt():
    vorstand = (
        Vorstandsmitglied.query
        .filter_by(sichtbar=True)
        .order_by(Vorstandsmitglied.reihenfolge.asc())
        .all()
    )
    return render_template("main/kontakt.html", vorstand=vorstand)


@main.route("/impressum", methods=["GET"])
def impressum():
    return render_template("main/impressum.html")


@main.route('/veranstaltungen')
def veranstaltungen():
    termine = (
        Termin.query
        .filter_by(veroeffentlicht=True)
        .order_by(Termin.datum.asc())
        .all()
    )
    return render_template('main/veranstaltungen.html', termine=termine)

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