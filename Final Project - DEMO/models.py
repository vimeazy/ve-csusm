from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    events_created = db.relationship("Event", backref="creator", lazy=True)
    rsvps = db.relationship(
        "RSVP",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    clubs_created = db.relationship("Club", backref="creator", lazy=True)


class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)

    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    # one club → many events
    events = db.relationship("Event", backref="club", lazy=True)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(150), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    # Which club this event belongs to
    club_id = db.Column(db.Integer, db.ForeignKey("club.id"), nullable=True)

    rsvps = db.relationship(
        "RSVP",
        back_populates="event",
        cascade="all, delete-orphan"
    )
    

class RSVP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="rsvps")
    event = db.relationship("Event", back_populates="rsvps")

    __table_args__ = (
        db.UniqueConstraint("user_id", "event_id", name="uq_user_event"),
    )
