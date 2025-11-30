from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # 'student' or 'officer'
    role = db.Column(db.String(20), default="student", nullable=False)
    
    # Profile image filename (stored in static/uploads)
    profile_image_filename = db.Column(db.String(255), nullable=True)

    # Events this user created
    events_created = db.relationship("Event", backref="creator", lazy=True)

    # RSVPs this user has made
    rsvps = db.relationship(
        "RSVP",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Clubs this user owns (is an officer for)
    clubs_owned = db.relationship(
        "Club",
        back_populates="owner",
        lazy=True
    )


class Club(db.Model):
    __tablename__ = "club"

    id = db.Column(db.Integer, primary_key=True)

    # Basic identity
    name = db.Column(db.String(120), nullable=False)

    # Short card preview / tagline for club cards
    short_description = db.Column(db.String(200), nullable=True)

    # Rich-text "About / Details" (HTML from Quill)
    description = db.Column(db.Text, nullable=True)

    # Optional logo image filename (stored in static/uploads)
    logo_filename = db.Column(db.String(255), nullable=True)

    # Optional banner image filename (shown at top of club detail page)
    banner_filename = db.Column(db.String(255), nullable=True)

    # Contact fields
    website = db.Column(db.String(255), nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    contact_phone = db.Column(db.String(50), nullable=True)

    # Owner (club officer)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    owner = db.relationship("User", back_populates="clubs_owned")

    # Events hosted by this club
    # NOTE: no lazy="dynamic" → this is a normal list-like collection
    events = db.relationship(
        "Event",
        back_populates="club",
        lazy=True
    )


class Event(db.Model):
    __tablename__ = "event"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(150), nullable=False)
    # Rich text HTML from Quill
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(150), nullable=False)

    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)

    # Relationships / foreign keys
    club_id = db.Column(db.Integer, db.ForeignKey("club.id"), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Optional event image filename (stored in static/uploads)
    image_filename = db.Column(db.String(255), nullable=True)

    # Backrefs
    club = db.relationship("Club", back_populates="events")

    # RSVPs for this event
    # NOTE: no lazy="dynamic" → e.rsvps is list-like, so `|length` works in templates
    rsvps = db.relationship(
        "RSVP",
        back_populates="event",
        cascade="all, delete-orphan"
    )


class RSVP(db.Model):
    __tablename__ = "rsvp"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="rsvps")
    event = db.relationship("Event", back_populates="rsvps")

    __table_args__ = (
        db.UniqueConstraint("user_id", "event_id", name="uniq_user_event"),
    )
