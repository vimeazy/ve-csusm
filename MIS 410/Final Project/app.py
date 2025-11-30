import os
from datetime import datetime

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import (
    LoginManager, login_user, logout_user,
    current_user, login_required
)
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from config import Config
from models import db, User, Club, Event, RSVP
from forms import RegisterForm, LoginForm, ClubForm, EventForm, ProfileForm

# ----------------- APP SETUP -----------------

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# File uploads (event images, club logos)
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = "login"  # redirect here if not logged in


@login_manager.user_loader
def load_user(user_id: str):
    # Modern SQLAlchemy 2.0 style
    return db.session.get(User, int(user_id))


# ----------------- AUTH ROUTES -----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data.lower()).first():
            flash("Email already registered.", "danger")
            return redirect(url_for("register"))

        user = User(
            name=form.name.data,
            email=form.email.data.lower(),
            password_hash=generate_password_hash(form.password.data),
            role=form.role.data,
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created. You can log in now.", "success")
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
            return redirect(url_for("index"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("index"))


# ----------------- MAIN / FEED -----------------

from datetime import datetime, timedelta
# ^ make sure timedelta is imported

@app.route("/")
def index():
    now = datetime.now()

    # All upcoming events (used for main grid)
    upcoming_events = (
        Event.query
        .filter(Event.start_time >= now)
        .order_by(Event.start_time.asc())
        .all()
    )

    # Calculate Sunday and Saturday of current week
    days_since_sunday = (now.weekday() + 1) % 7  # Sunday is 0, so we need to adjust
    sunday_this_week = now - timedelta(days=days_since_sunday)
    saturday_this_week = sunday_this_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    # Events happening this week (Sunday to Saturday)
    this_week_events = (
        Event.query
        .filter(Event.start_time >= sunday_this_week, Event.start_time <= saturday_this_week)
        .order_by(Event.start_time.asc())
        .all()
    )

    # Simple stats
    club_count = Club.query.count()
    upcoming_count = len(upcoming_events)
    rsvp_count = RSVP.query.count()

    # Featured clubs: clubs with the most events (limit 3)
    from sqlalchemy import func
    featured_clubs = (
        Club.query
        .outerjoin(Event)
        .group_by(Club.id)
        .order_by(func.count(Event.id).desc())
        .limit(3)
        .all()
    )

    # Featured events: upcoming events with most RSVPs (for carousel)
    featured_events = (
        Event.query
        .filter(Event.start_time >= now)
        .outerjoin(RSVP)
        .group_by(Event.id)
        .order_by(func.count(RSVP.id).desc())
        .limit(6)
        .all()
    )

    return render_template(
        "index.html",
        events=upcoming_events,
        this_week_events=this_week_events,
        club_count=club_count,
        event_count=upcoming_count,
        rsvp_count=rsvp_count,
        featured_clubs=featured_clubs,
        featured_events=featured_events,
        week_start_date=sunday_this_week,
    )


@app.route("/my-events")
@login_required
def my_events():
    # Events user created
    created = (
        Event.query
        .filter_by(created_by=current_user.id)
        .order_by(Event.start_time.asc())
        .all()
    )

    # Events user RSVP'd to, newest RSVP first
    rsvps_sorted = sorted(
        current_user.rsvps,
        key=lambda r: r.created_at or datetime.min,
        reverse=True,
    )
    rsvp_events = [rsvp.event for rsvp in rsvps_sorted]
    
    # Deduplicate: remove events from rsvp_events if they're already in created
    created_ids = {e.id for e in created}
    rsvp_events = [e for e in rsvp_events if e.id not in created_ids]

    return render_template("my_events.html", created=created, rsvp_events=rsvp_events, now=datetime.now())


# ----------------- USER PROFILE -----------------

@app.route("/profile")
@login_required
def profile():
    # Clubs this user owns (officer)
    officer_clubs = sorted(current_user.clubs_owned, key=lambda c: c.name.lower())

    # Events created by this user
    created_events = (
        Event.query
        .filter_by(created_by=current_user.id)
        .order_by(Event.start_time.asc())
        .all()
    )

    # Events this user has RSVP’d to (most recent RSVP first)
    rsvps_sorted = sorted(
        current_user.rsvps,
        key=lambda r: r.created_at or datetime.min,
        reverse=True,
    )
    rsvp_events = [rsvp.event for rsvp in rsvps_sorted]

    # Separate upcoming and past events
    now = datetime.now()
    
    upcoming_created = [e for e in created_events if e.start_time > now]
    past_created = [e for e in created_events if e.start_time <= now]
    
    upcoming_rsvp = [e for e in rsvp_events if e.start_time > now]
    past_rsvp = [e for e in rsvp_events if e.start_time <= now]

    # Calculate stats
    stats = {
        'clubs': len(officer_clubs),
        'events_created': len(created_events),
        'events_attending': len(rsvp_events),
    }

    return render_template(
        "profile.html",
        officer_clubs=officer_clubs,
        created_events=created_events,
        upcoming_created=upcoming_created,
        past_created=past_created,
        rsvp_events=rsvp_events,
        upcoming_rsvp=upcoming_rsvp,
        past_rsvp=past_rsvp,
        stats=stats,
    )


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.bio = form.bio.data
        current_user.website = form.website.data
        current_user.twitter = form.twitter.data
        current_user.instagram = form.instagram.data
        current_user.linkedin = form.linkedin.data
        
        # Handle profile image upload
        if form.profile_image.data:
            # Create profiles subfolder if it doesn't exist
            profiles_folder = os.path.join(app.config["UPLOAD_FOLDER"], "profiles")
            os.makedirs(profiles_folder, exist_ok=True)
            
            # Delete old image if exists
            if current_user.profile_image_filename:
                old_path = os.path.join(profiles_folder, current_user.profile_image_filename)
                if os.path.exists(old_path):
                    os.remove(old_path)
            
            # Save new image
            file = form.profile_image.data
            filename = secure_filename(file.filename)
            # Add timestamp to make filename unique
            filename = f"profile_{current_user.id}_{datetime.now().timestamp()}_{filename}"
            file.save(os.path.join(profiles_folder, filename))
            current_user.profile_image_filename = filename
        
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("profile"))

    return render_template("profile_edit.html", form=form)


# ----------------- CLUB CRUD (officers only) -----------------

def officer_required() -> bool:
    return current_user.is_authenticated and current_user.role == "officer"


@app.route("/clubs")
def clubs():
    q = request.args.get("q", "").strip()       # search query from ?q=
    my_only = request.args.get("my") == "1"     # ?my=1 → only my clubs

    query = Club.query

    # Filter to "my clubs" if requested and logged in
    if my_only and current_user.is_authenticated:
        query = query.filter_by(owner_id=current_user.id)

    if q:
        # case-insensitive search on club name or description
        search_pattern = f"%{q}%"
        query = query.filter(
            db.or_(
                Club.name.ilike(search_pattern),
                Club.description.ilike(search_pattern)
            )
        )

    clubs_list = query.order_by(Club.name.asc()).all()

    my_clubs = []
    if current_user.is_authenticated:
        my_clubs = (
            Club.query
            .filter_by(owner_id=current_user.id)
            .order_by(Club.name.asc())
            .all()
        )

    return render_template(
        "clubs.html",
        clubs=clubs_list,
        my_clubs=my_clubs,
        search_query=q,
        my_only=my_only,
    )


@app.route("/clubs/<int:club_id>")
def club_detail(club_id):
    club = Club.query.get_or_404(club_id)
    return render_template("club_detail.html", club=club)


@app.route("/clubs/new", methods=["GET", "POST"])
@login_required
def club_create():
    if not officer_required():
        flash("Only officers can create clubs.", "danger")
        return redirect(url_for("clubs"))

    form = ClubForm()
    if form.validate_on_submit():
        logo_filename = None
        if form.image.data:
            file = form.image.data
            filename = secure_filename(file.filename)
            if filename:
                logo_filename = filename
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        banner_filename = None
        if form.banner.data:
            file = form.banner.data
            filename = secure_filename(file.filename)
            if filename:
                banner_filename = filename
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        club = Club(
            name=form.name.data,
            short_description=form.short_description.data or None,
            description=form.description.data,
            website=form.website.data or None,
            contact_email=form.contact_email.data or None,
            contact_phone=form.contact_phone.data or None,
            logo_filename=logo_filename,
            banner_filename=banner_filename,
            owner_id=current_user.id,
        )
        db.session.add(club)
        db.session.commit()
        flash("Club created.", "success")
        return redirect(url_for("club_detail", club_id=club.id))

    return render_template("club_form.html", form=form, form_title="Create Club")


@app.route("/clubs/<int:club_id>/edit", methods=["GET", "POST"])
@login_required
def club_edit(club_id):
    club = Club.query.get_or_404(club_id)

    # Only officers + the owner can edit
    if not officer_required() or club.owner_id != current_user.id:
        flash("You are not allowed to edit this club.", "danger")
        return redirect(url_for("clubs"))

    form = ClubForm(obj=club)

    if form.validate_on_submit():
        club.name = form.name.data
        club.short_description = form.short_description.data or None
        club.description = form.description.data
        club.website = form.website.data or None
        club.contact_email = form.contact_email.data or None
        club.contact_phone = form.contact_phone.data or None

        # Handle new logo upload (optional)
        if form.image.data:
            file = form.image.data
            filename = secure_filename(file.filename)
            if filename:
                club.logo_filename = filename
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        # Handle new banner upload (optional)
        if form.banner.data:
            file = form.banner.data
            filename = secure_filename(file.filename)
            if filename:
                club.banner_filename = filename
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        db.session.commit()
        flash("Club updated successfully.", "success")
        return redirect(url_for("club_detail", club_id=club.id))

    return render_template("club_form.html", form=form, form_title="Edit Club", club=club)


@app.route("/clubs/<int:club_id>/delete", methods=["POST"])
@login_required
def club_delete(club_id):
    club = Club.query.get_or_404(club_id)

    # Only officers + the owner can delete
    if not officer_required() or club.owner_id != current_user.id:
        flash("You are not allowed to delete this club.", "danger")
        return redirect(url_for("club_detail", club_id=club.id))

    # Delete events for this club first (their RSVPs will cascade)
    for event in list(club.events):
        db.session.delete(event)

    db.session.delete(club)
    db.session.commit()
    flash("Club and its events were deleted.", "info")
    return redirect(url_for("clubs"))


# ----------------- EVENT CRUD -----------------

@app.route("/events")
def events():
    q = request.args.get("q", "").strip()       # search query from ?q=
    sort_by = request.args.get("sort", "date")  # sort by "date" or "rsvp"
    view = request.args.get("view", "card")     # view as "card" or "list"
    
    query = Event.query

    if q:
        # case-insensitive search on event title or description
        search_pattern = f"%{q}%"
        query = query.filter(
            db.or_(
                Event.title.ilike(search_pattern),
                Event.description.ilike(search_pattern)
            )
        )

    # Sort by RSVP count (descending) or by date (ascending)
    if sort_by == "rsvp":
        # Sort by RSVP count in Python since it's a relationship
        events_list = query.all()
        events_list = sorted(events_list, key=lambda e: len(e.rsvps), reverse=True)
    else:
        events_list = query.order_by(Event.start_time.asc()).all()
    
    return render_template("events.html", events=events_list, search_query=q, sort_by=sort_by, view=view)


@app.route("/events/<int:event_id>")
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template("event_detail.html", event=event)


@app.route("/events/new", methods=["GET", "POST"])
@login_required
def event_create():
    if not officer_required():
        flash("Only officers can create events.", "danger")
        return redirect(url_for("events"))

    form = EventForm()
    # Populate club choices with only the clubs this officer owns
    form.club_id.choices = [(c.id, c.name) for c in current_user.clubs_owned]

    if form.validate_on_submit():
        # handle uploaded image (optional)
        image_filename = None
        if form.image.data:
            file = form.image.data
            filename = secure_filename(file.filename)
            if filename:
                image_filename = filename
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        event = Event(
            title=form.title.data,
            description=form.description.data,
            location=form.location.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            club_id=form.club_id.data,
            created_by=current_user.id,
            image_filename=image_filename,
        )
        db.session.add(event)
        db.session.commit()
        flash("Event created.", "success")
        return redirect(url_for("events"))

    return render_template("event_form.html", form=form)


@app.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def event_edit(event_id):
    event = Event.query.get_or_404(event_id)

    # Only officers who created the event can edit it
    if not officer_required() or event.created_by != current_user.id:
        flash("You are not allowed to edit this event.", "danger")
        return redirect(url_for("event_detail", event_id=event.id))

    form = EventForm(obj=event)
    # Populate club choices with only the clubs this officer owns
    form.club_id.choices = [(c.id, c.name) for c in current_user.clubs_owned]

    # Ensure the current club is selected
    if form.club_id.data is None:
        form.club_id.data = event.club_id

    if form.validate_on_submit():
        event.title = form.title.data
        event.description = form.description.data
        event.location = form.location.data
        event.start_time = form.start_time.data
        event.end_time = form.end_time.data
        event.club_id = form.club_id.data

        # handle new image upload (optional)
        if form.image.data:
            file = form.image.data
            filename = secure_filename(file.filename)
            if filename:
                event.image_filename = filename
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        db.session.commit()
        flash("Event updated successfully.", "success")
        return redirect(url_for("event_detail", event_id=event.id))

    return render_template("event_form.html", form=form, form_title="Edit Event")


@app.route("/events/<int:event_id>/delete", methods=["POST"])
@login_required
def event_delete(event_id):
    event = Event.query.get_or_404(event_id)

    # Only officers who created the event can delete it
    if not officer_required() or event.created_by != current_user.id:
        flash("You are not allowed to delete this event.", "danger")
        return redirect(url_for("event_detail", event_id=event.id))

    db.session.delete(event)
    db.session.commit()
    flash("Event deleted.", "info")
    return redirect(url_for("events"))


@app.route("/events/<int:event_id>/rsvp", methods=["POST"])
@login_required
def rsvp_event(event_id):
    event = Event.query.get_or_404(event_id)
    existing = RSVP.query.filter_by(user_id=current_user.id, event_id=event.id).first()
    if existing:
        flash("You already RSVP’d to this event.", "info")
    else:
        rsvp = RSVP(user_id=current_user.id, event_id=event.id)
        db.session.add(rsvp)
        db.session.commit()
        flash("RSVP recorded!", "success")
    return redirect(url_for("event_detail", event_id=event.id))


# ----------------- ENTRY POINT -----------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
