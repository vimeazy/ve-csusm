from datetime import datetime

from flask import (
    Flask, render_template, redirect,
    url_for, flash, request
)
from flask_login import (
    LoginManager, login_user, logout_user,
    current_user, login_required
)
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from models import db, User, Event, RSVP, Club
from forms import RegisterForm, LoginForm, EventForm, ClubForm


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    # SQLAlchemy 2.x style
    return db.session.get(User, int(user_id))


# ---------- Auth routes ----------

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower()).first()
        if existing:
            flash("Email already registered.", "danger")
            return redirect(url_for("register"))

        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            password_hash=generate_password_hash(form.password.data),
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created. You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash("Logged in successfully.", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("index"))
        flash("Invalid email or password.", "danger")

    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# ---------- Main / dashboard ----------

@app.route("/")
def index():
    # Upcoming events ordered by time
    events = (
        Event.query
        .filter(Event.start_time >= datetime.now())
        .order_by(Event.start_time.asc())
        .all()
    )
    return render_template("index.html", events=events)


@app.route("/my-events")
@login_required
def my_events():
    created_events = (
        Event.query
        .filter_by(created_by=current_user.id)
        .order_by(Event.start_time.asc())
        .all()
    )

    rsvp_events = [rsvp.event for rsvp in current_user.rsvps]

    return render_template(
        "my_events.html",
        created_events=created_events,
        rsvp_events=rsvp_events,
    )


# ---------- Event CRUD ----------

@app.route("/events")
def events():
    events = Event.query.order_by(Event.start_time.asc()).all()
    return render_template("events.html", events=events)


@app.route("/events/<int:event_id>")
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)

    user_has_rsvped = False
    if current_user.is_authenticated:
        user_has_rsvped = RSVP.query.filter_by(
            user_id=current_user.id,
            event_id=event.id
        ).first() is not None

    return render_template(
        "event_detail.html",
        event=event,
        user_has_rsvped=user_has_rsvped,
    )


@app.route("/events/new", methods=["GET", "POST"])
@login_required
def event_create():
    form = EventForm()

    # populate clubs dropdown (all clubs, ordered by name)
    clubs = Club.query.order_by(Club.name.asc()).all()
    form.club_id.choices = [(0, "— No club —")] + [(c.id, c.name) for c in clubs]

    if form.validate_on_submit():
        club_id = form.club_id.data or None
        if club_id == 0:
            club_id = None

        event = Event(
            title=form.title.data.strip(),
            description=form.description.data,
            location=form.location.data.strip(),
            start_time=form.start_time.data,
            created_by=current_user.id,
            club_id=club_id,
        )
        db.session.add(event)
        db.session.commit()
        flash("Event created.", "success")
        return redirect(url_for("events"))

    return render_template("event_form.html", form=form, form_title="Create Event")



@app.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def event_edit(event_id):
    event = Event.query.get_or_404(event_id)

    if event.created_by != current_user.id:
        flash("You are not allowed to edit this event.", "danger")
        return redirect(url_for("event_detail", event_id=event.id))

    form = EventForm(obj=event)

    # populate clubs dropdown
    clubs = Club.query.order_by(Club.name.asc()).all()
    form.club_id.choices = [(0, "— No club —")] + [(c.id, c.name) for c in clubs]
    form.club_id.data = event.club_id or 0

    if form.validate_on_submit():
        club_id = form.club_id.data or None
        if club_id == 0:
            club_id = None

        event.title = form.title.data.strip()
        event.description = form.description.data
        event.location = form.location.data.strip()
        event.start_time = form.start_time.data
        event.club_id = club_id

        db.session.commit()
        flash("Event updated.", "success")
        return redirect(url_for("event_detail", event_id=event.id))

    return render_template("event_form.html", form=form, form_title="Edit Event")


@app.route("/events/<int:event_id>/delete", methods=["POST"])
@login_required
def event_delete(event_id):
    event = Event.query.get_or_404(event_id)

    if event.created_by != current_user.id:
        flash("You are not allowed to delete this event.", "danger")
        return redirect(url_for("event_detail", event_id=event.id))

    db.session.delete(event)
    db.session.commit()
    flash("Event deleted.", "info")
    return redirect(url_for("events"))

# ---------- Club CRUD ----------

@app.route("/clubs")
def clubs():
    clubs = Club.query.order_by(Club.name.asc()).all()
    return render_template("clubs.html", clubs=clubs)


@app.route("/clubs/<int:club_id>")
def club_detail(club_id):
    club = Club.query.get_or_404(club_id)
    return render_template("club_detail.html", club=club)


@app.route("/clubs/new", methods=["GET", "POST"])
@login_required
def club_create():
    form = ClubForm()
    if form.validate_on_submit():
        club = Club(
            name=form.name.data.strip(),
            description=form.description.data,
            created_by=current_user.id,
        )
        db.session.add(club)
        db.session.commit()
        flash("Club created.", "success")
        return redirect(url_for("clubs"))

    return render_template("club_form.html", form=form, form_title="Create Club")


@app.route("/clubs/<int:club_id>/edit", methods=["GET", "POST"])
@login_required
def club_edit(club_id):
    club = Club.query.get_or_404(club_id)

    if club.created_by != current_user.id:
        flash("You are not allowed to edit this club.", "danger")
        return redirect(url_for("club_detail", club_id=club.id))

    form = ClubForm(obj=club)
    if form.validate_on_submit():
        club.name = form.name.data.strip()
        club.description = form.description.data
        db.session.commit()
        flash("Club updated.", "success")
        return redirect(url_for("club_detail", club_id=club.id))

    return render_template("club_form.html", form=form, form_title="Edit Club")


@app.route("/clubs/<int:club_id>/delete", methods=["POST"])
@login_required
def club_delete(club_id):
    club = Club.query.get_or_404(club_id)

    if club.created_by != current_user.id:
        flash("You are not allowed to delete this club.", "danger")
        return redirect(url_for("club_detail", club_id=club.id))

    db.session.delete(club)
    db.session.commit()
    flash("Club deleted.", "info")
    return redirect(url_for("clubs"))


# ---------- RSVP actions ----------

@app.route("/events/<int:event_id>/rsvp", methods=["POST"])
@login_required
def rsvp_event(event_id):
    event = Event.query.get_or_404(event_id)

    existing = RSVP.query.filter_by(
        user_id=current_user.id,
        event_id=event.id
    ).first()

    if existing:
        flash("You already RSVP'd to this event.", "info")
    else:
        rsvp = RSVP(user_id=current_user.id, event_id=event.id)
        db.session.add(rsvp)
        db.session.commit()
        flash("RSVP recorded!", "success")

    return redirect(url_for("event_detail", event_id=event.id))


@app.route("/events/<int:event_id>/cancel_rsvp", methods=["POST"])
@login_required
def cancel_rsvp(event_id):
    event = Event.query.get_or_404(event_id)

    rsvp = RSVP.query.filter_by(
        user_id=current_user.id,
        event_id=event.id
    ).first()

    if not rsvp:
        flash("You have not RSVP'd to this event.", "warning")
    else:
        db.session.delete(rsvp)
        db.session.commit()
        flash("Your RSVP has been cancelled.", "info")

    return redirect(url_for("event_detail", event_id=event.id))


# ---------- Entry point ----------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
