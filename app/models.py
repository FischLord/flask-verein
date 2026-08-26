from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime, timezone, date
from app import db, login


def _now_utc() -> datetime:
    """Callable-Default für created_at/updated_at (vgl. FV-11)."""
    return datetime.now(timezone.utc)


class Users(UserMixin, db.Model):
    __tablename__ = "users"
    id: int = db.Column(db.Integer, primary_key=True)
    email: str = db.Column(db.String(120), unique=True)
    first_name: str = db.Column(db.String(15))
    last_name: str = db.Column(db.String(15))
    password_hash: str = db.Column(db.String(256))
    created_at: datetime = db.Column(
        db.DateTime(), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<Users {self.id}>"

    def set_password(self, password: str) -> bool:
        """
        Sets the password hash for the user.

        :param password: password to hash
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
        Checks if the given password matches the user's password hash.

        :param password: password to check
        :return: True if the password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)


@login.user_loader
def load_user(id):
    """
    Loads a user from the database (used by Flask-Login).

    :param id: user ID
    :return: user object
    """
    return Users.query.get(int(id))


class Termin(db.Model):
    """Veranstaltung/Termin (öffentliche Seite veranstaltungen.html)."""

    __tablename__ = "termine"
    id: int = db.Column(db.Integer, primary_key=True)
    titel: str = db.Column(db.String(120), nullable=False)
    datum: date = db.Column(db.Date, nullable=False)
    uhrzeit: str = db.Column(db.String(20))
    ort: str = db.Column(db.String(200))
    beschreibung: str = db.Column(db.Text)
    veroeffentlicht: bool = db.Column(
        db.Boolean, default=True, nullable=False
    )
    created_at: datetime = db.Column(db.DateTime(), default=_now_utc)
    updated_at: datetime = db.Column(
        db.DateTime(), default=_now_utc, onupdate=_now_utc
    )

    @property
    def abgelaufen(self) -> bool:
        """True, wenn der Termin in der Vergangenheit liegt."""
        return self.datum < date.today()

    def __repr__(self):
        return f"<Termin {self.id} {self.titel}>"


class Vorstandsmitglied(db.Model):
    """Vorstandsmitglied (öffentliche Seite kontakt.html)."""

    __tablename__ = "vorstand"
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(120), nullable=False)
    funktion: str = db.Column(db.String(120), nullable=False)
    reihenfolge: int = db.Column(db.Integer, default=0, nullable=False)
    spruch: str = db.Column(db.Text)
    telefon: str = db.Column(db.String(50))
    email: str = db.Column(db.String(120))
    foto: str = db.Column(db.String(255))
    sichtbar: bool = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Vorstandsmitglied {self.id} {self.name}>"


class Bericht(db.Model):
    """Erlebnisbericht mit zugehörigen Bildern (1:n)."""

    __tablename__ = "berichte"
    id: int = db.Column(db.Integer, primary_key=True)
    jahr: int = db.Column(db.Integer, nullable=False)
    titel: str = db.Column(db.String(200), nullable=False)
    text: str = db.Column(db.Text)
    reihenfolge: int = db.Column(db.Integer, default=0, nullable=False)
    veroeffentlicht: bool = db.Column(
        db.Boolean, default=True, nullable=False
    )
    bilder = db.relationship(
        "BerichtBild",
        back_populates="bericht",
        cascade="all, delete-orphan",
        order_by="BerichtBild.reihenfolge",
    )

    def __repr__(self):
        return f"<Bericht {self.id} {self.titel}>"


class BerichtBild(db.Model):
    """Einzelnes Bild eines Erlebnisberichts."""

    __tablename__ = "bericht_bilder"
    id: int = db.Column(db.Integer, primary_key=True)
    bericht_id: int = db.Column(
        db.Integer, db.ForeignKey("berichte.id"), nullable=False
    )
    dateiname: str = db.Column(db.String(255), nullable=False)
    reihenfolge: int = db.Column(db.Integer, default=0, nullable=False)
    alt_text: str = db.Column(db.String(255))
    bericht = db.relationship("Bericht", back_populates="bilder")

    def __repr__(self):
        return f"<BerichtBild {self.id}>"
