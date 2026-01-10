from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from app import db, login


class Users(UserMixin, db.Model):
    """Benutzer-Model mit Admin-Unterstützung"""
    __tablename__ = "users"
    id: int = db.Column(db.Integer, primary_key=True)
    email: str = db.Column(db.String(120), unique=True)
    first_name: str = db.Column(db.String(15))
    last_name: str = db.Column(db.String(15))
    password_hash: str = db.Column(db.String(128))
    is_admin: bool = db.Column(db.Boolean, default=False, nullable=False)
    created_at: datetime = db.Column(db.DateTime(), default=datetime.utcnow)

    def __repr__(self):
        return f"<Users {self.id} {'(Admin)' if self.is_admin else ''}>"

    def set_password(self, password: str) -> None:
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


class Report(db.Model):
    """Bericht/Event mit Bildern"""
    __tablename__ = "reports"
    id: int = db.Column(db.Integer, primary_key=True)
    slug: str = db.Column(db.String(100), unique=True, nullable=False)
    title: str = db.Column(db.String(200), nullable=False)
    description: str = db.Column(db.Text, nullable=True)
    is_published: bool = db.Column(db.Boolean, default=False, nullable=False)
    year: int = db.Column(db.Integer, nullable=True)
    event_date: datetime = db.Column(db.Date, nullable=True)
    created_at: datetime = db.Column(db.DateTime(), default=datetime.utcnow)
    updated_at: datetime = db.Column(
        db.DateTime(),
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Beziehung zu Bildern
    images = db.relationship(
        'ReportImage',
        backref='report',
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='ReportImage.position'
    )

    def __repr__(self):
        status = "✓" if self.is_published else "○"
        return f"<Report [{status}] {self.slug}>"

    @property
    def image_count(self) -> int:
        """Anzahl der Bilder in diesem Bericht"""
        return self.images.count()

    @property
    def folder_path(self) -> str:
        """Relativer Pfad zum Bericht-Ordner"""
        return f"berichte/{self.slug}"


class ReportImage(db.Model):
    """Einzelnes Bild in einem Bericht"""
    __tablename__ = "report_images"
    id: int = db.Column(db.Integer, primary_key=True)
    report_id: int = db.Column(
        db.Integer,
        db.ForeignKey('reports.id', ondelete='CASCADE'),
        nullable=False
    )
    filename: str = db.Column(db.String(255), nullable=False)
    original_filename: str = db.Column(db.String(255), nullable=True)
    position: int = db.Column(db.Integer, default=0, nullable=False)
    created_at: datetime = db.Column(db.DateTime(), default=datetime.utcnow)

    def __repr__(self):
        return f"<ReportImage {self.filename} (pos={self.position})>"

    @property
    def web_path(self) -> str:
        """Pfad zum WebP-Bild für Anzeige"""
        return f"berichte/{self.report.slug}/web/{self.filename}"

    @property
    def original_path(self) -> str:
        """Pfad zum Originalbild für Download"""
        if self.original_filename:
            return f"berichte/{self.report.slug}/originals/{self.original_filename}"
        return self.web_path


@login.user_loader
def load_user(id):
    """
    Loads a user from the database (used by Flask-Login).

    :param id: user ID
    :return: user object
    """
    return Users.query.get(int(id))
