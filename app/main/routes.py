from flask import (
    render_template, current_app, abort, make_response, send_from_directory,
    redirect, url_for, flash,
)
from app.main import main
from app.main.forms import ContactForm
from app import db, mail, limiter
from app.models import Termin, Vorstandsmitglied, Bericht
from flask_mail import Message
from markupsafe import Markup, escape
import urllib.parse
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload


@main.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html",
        title="Kutschfahrten & Reitsport in Reckahn",
        meta_description=(
            "Fahrverein Planetal e.V. in Reckahn (Brandenburg): "
            "Kutschfahrten, Reitsport, Ausfahrten und der jährliche "
            "Kutschertag. Seit 2012 für Pferdefreunde jeden Alters."
        ),
    )


@main.route('/berichte')
def berichte_uebersicht():
    """Uebersichtsseite: alle Jahre mit veroeffentlichten Berichten."""
    berichte = (
        Bericht.query
        .options(selectinload(Bericht.bilder))
        .filter_by(veroeffentlicht=True)
        .order_by(Bericht.jahr.desc(), Bericht.reihenfolge.asc(),
                  Bericht.titel.asc())
        .all()
    )
    # Pro Jahr gruppieren (Reihenfolge der Query bleibt erhalten).
    jahre = []
    by_year = {}
    for b in berichte:
        if b.jahr not in by_year:
            by_year[b.jahr] = {
                'jahr': b.jahr,
                'anzahl_berichte': 0,
                'anzahl_bilder': 0,
                'titelbild': None,
            }
            jahre.append(by_year[b.jahr])
        eintrag = by_year[b.jahr]
        eintrag['anzahl_berichte'] += 1
        eintrag['anzahl_bilder'] += len(b.bilder)
        if eintrag['titelbild'] is None and b.bilder:
            eintrag['titelbild'] = b.bilder[0].dateiname
    return render_template(
        'main/berichte_uebersicht.html', jahre=jahre,
        title="Erlebnisberichte",
        meta_description=(
            "Fotogalerien und Erlebnisberichte des Fahrvereins Planetal "
            "e.V.: Kutschertage, Ausfahrten und Turniere in Reckahn, "
            "Brandenburg - nach Jahren sortiert."
        ),
    )


@main.route('/berichte/<int:jahr>')
def erlebnisberichte(jahr):
    """Alle veroeffentlichten Berichte eines Jahres auf einer Seite."""
    berichte = (
        Bericht.query
        .options(selectinload(Bericht.bilder))
        .filter_by(jahr=jahr, veroeffentlicht=True)
        .order_by(Bericht.reihenfolge.asc(), Bericht.titel.asc())
        .all()
    )
    if not berichte:
        abort(404)
    return render_template(
        'main/berichte.html', jahr=jahr, berichte=berichte,
        title="Erlebnisberichte {}".format(jahr),
        meta_description=(
            "Fotos und Berichte aus {} vom Fahrverein Planetal e.V.: "
            "Kutschfahrten, Turniere und Kutschertag in Reckahn, "
            "Brandenburg.".format(jahr)
        ),
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


# Deutsche Monats-Kuerzel (locale-unabhaengig) fuer Datums-Chips.
_MONATE_KURZ = [
    "", "Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
    "Jul", "Aug", "Sep", "Okt", "Nov", "Dez",
]


@main.app_template_filter('monat_kurz')
def monat_kurz_filter(d):
    """Gibt das deutsche Monatskuerzel zu einem date/datetime zurueck."""
    try:
        return _MONATE_KURZ[d.month]
    except (AttributeError, IndexError):
        return ""




@main.route("/verein", methods=["GET"])
def verein():
    return render_template(
        "main/verein.html",
        title="Über den Verein",
        meta_description=(
            "Lernen Sie den Fahrverein Planetal e.V. kennen: "
            "Pferdefreunde, Jugendarbeit, Dressurplatz und Fahrsport-"
            "Tradition seit 2012 in Reckahn, Hoher Fläming."
        ),
    )


@main.route("/kontakt", methods=["GET", "POST"])
@limiter.limit(
    "5 per hour",
    methods=["POST"],
    error_message=(
        "Es wurden zu viele Nachrichten in kurzer Zeit gesendet. "
        "Bitte versuche es später erneut oder schreib uns direkt per E-Mail."
    ),
)
def kontakt():
    vorstand = (
        Vorstandsmitglied.query
        .filter_by(sichtbar=True)
        .order_by(Vorstandsmitglied.reihenfolge.asc())
        .all()
    )
    form = ContactForm()
    # Mailversand nur moeglich, wenn ein Mailserver konfiguriert ist.
    mail_aktiv = bool(current_app.config.get("MAIL_SERVER"))

    if form.validate_on_submit():
        if not mail_aktiv:
            flash(
                "Der Online-Versand ist derzeit nicht eingerichtet. Bitte "
                "schreib uns direkt an fvplanetal@web.de.",
                "warning",
            )
            return redirect(url_for("main.kontakt") + "#kontaktformular")

        empfaenger = current_app.config.get("CONTACT_RECIPIENT")
        absender = current_app.config.get("MAIL_DEFAULT_SENDER")
        msg = Message(
            subject=f"[Kontaktformular] {form.betreff.data}",
            recipients=[empfaenger],
            reply_to=form.email.data,
            sender=absender,
            body=(
                "Neue Nachricht über das Kontaktformular der Website:\n\n"
                f"Name:    {form.name.data}\n"
                f"E-Mail:  {form.email.data}\n"
                f"Betreff: {form.betreff.data}\n\n"
                "Nachricht:\n"
                f"{form.nachricht.data}\n"
            ),
        )
        try:
            mail.send(msg)
        except Exception:  # noqa: BLE001 - Versandfehler dem Nutzer melden
            current_app.logger.exception("Kontaktformular: Mailversand fehlgeschlagen")
            flash(
                "Die Nachricht konnte gerade nicht versendet werden. Bitte "
                "versuche es später erneut oder schreib uns an fvplanetal@web.de.",
                "danger",
            )
            return redirect(url_for("main.kontakt") + "#kontaktformular")

        flash(
            "Vielen Dank für deine Nachricht! Wir melden uns so schnell wie "
            "möglich bei dir.",
            "success",
        )
        return redirect(url_for("main.kontakt") + "#kontaktformular")

    return render_template(
        "main/kontakt.html", vorstand=vorstand, form=form,
        mail_aktiv=mail_aktiv,
        title="Vorstand & Kontakt",
        meta_description=(
            "Kontakt zum Fahrverein Planetal e.V. in Reckahn: Vorstand, "
            "Ansprechpartner und Anfragen rund um Kutschfahrten, "
            "Reitsport und Mitgliedschaft."
        ),
    )


@main.route("/impressum", methods=["GET"])
def impressum():
    return render_template(
        "main/impressum.html",
        title="Impressum",
        meta_description=(
            "Impressum und Anbieterkennzeichnung des Fahrvereins Planetal "
            "e.V., Krahner Straße, 14797 Kloster Lehnin OT Reckahn."
        ),
    )


@main.route('/veranstaltungen')
def veranstaltungen():
    heute = datetime.now().date()
    kommende = (
        Termin.query
        .filter_by(veroeffentlicht=True)
        .filter(Termin.datum >= heute)
        .order_by(Termin.datum.asc())
        .all()
    )
    vergangene = (
        Termin.query
        .filter_by(veroeffentlicht=True)
        .filter(Termin.datum < heute)
        .order_by(Termin.datum.desc())
        .all()
    )
    return render_template(
        'main/veranstaltungen.html',
        kommende=kommende, vergangene=vergangene,
        title="Veranstaltungen & Termine",
        meta_description=(
            "Aktuelle Termine, Trainingstage und der Reckahner "
            "Kutschertag des Fahrvereins Planetal e.V. Fahrsport-"
            "Veranstaltungen in Brandenburg entdecken."
        ),
    )


@main.route('/vereinsdaten')
def vereinsdaten():
    return render_template(
        'main/vereinsdaten.html',
        title="Vereinsdaten & Mitgliedschaft",
        meta_description=(
            "Geschäftsadresse, Bankverbindung, Register- und Mitglieds-"
            "daten des Fahrvereins Planetal e.V. in Reckahn (Kloster "
            "Lehnin), Brandenburg."
        ),
    )

@main.route('/datenschutz')
def datenschutz():
    return render_template(
        'main/datenschutz.html',
        title="Datenschutz",
        meta_description=(
            "Datenschutzerklärung des Fahrvereins Planetal e.V. gemäß "
            "DSGVO: verarbeitete Daten, Zwecke, Rechtsgrundlagen und "
            "Ihre Rechte."
        ),
    )

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
        '/berichte': {'priority': '0.7', 'changefreq': 'monthly'},
        '/kontakt': {'priority': '0.7', 'changefreq': 'monthly'},
        '/vereinsdaten': {'priority': '0.7', 'changefreq': 'monthly'},
        '/formcenter/': {'priority': '0.5', 'changefreq': 'weekly'},
        '/impressum': {'priority': '0.3', 'changefreq': 'yearly'},
        '/datenschutz': {'priority': '0.3', 'changefreq': 'yearly'}
    }
    
    # Stabiles lastmod fuer statische Info-Seiten: ein fester Stand statt
    # datetime.utcnow() pro Abruf (sonst signalisiert die Sitemap bei jedem
    # Crawl 'alles gerade geaendert', was Suchmaschinen abwerten).
    static_lastmod = '2026-06-20T00:00:00+00:00'

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
            sitemap_xml += f'    <lastmod>{static_lastmod}</lastmod>\n'
            sitemap_xml += f'    <changefreq>{settings["changefreq"]}</changefreq>\n'
            sitemap_xml += f'    <priority>{settings["priority"]}</priority>\n'
            sitemap_xml += '  </url>\n'

    # Dynamische Routen: veroeffentlichte Erlebnisberichte je Jahr.
    # Stabiles lastmod = Jahresende (Berichte sind historisch, aendern sich
    # nicht laufend); kein datetime.utcnow() pro Abruf.
    # (Die statische Schleife oben ueberspringt Routen mit Argumenten.)
    try:
        jahre = (
            db.session.query(Bericht.jahr)
            .filter_by(veroeffentlicht=True)
            .distinct()
            .order_by(Bericht.jahr.desc())
            .all()
        )
    except SQLAlchemyError:
        jahre = []
    for (jahr,) in jahre:
        url = urllib.parse.urljoin(base_url, f'/berichte/{jahr}')
        lastmod = f'{jahr}-12-31T00:00:00+00:00'
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>{url}</loc>\n'
        sitemap_xml += f'    <lastmod>{lastmod}</lastmod>\n'
        sitemap_xml += '    <changefreq>yearly</changefreq>\n'
        sitemap_xml += '    <priority>0.6</priority>\n'
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
