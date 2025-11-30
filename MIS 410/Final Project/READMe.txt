# CougarHub – CSUSM Club & Event Hub

CougarHub is a Flask web application that helps CSUSM students discover campus clubs and events in one place. Club officers can create clubs and events, while students can browse and RSVP to upcoming activities.

## 1. Tech Stack

- Python 3.x
- Flask (web framework)
- Flask-SQLAlchemy (ORM for database access)
- Flask-WTF (form handling + validation)
- Flask-Login (authentication)
- SQLite (local development database)
- HTML, CSS, Bootstrap 5 (responsive UI)

## 2. Project Structure

```text
cougarhub/
├─ app.py
├─ models.py
├─ forms.py
├─ config.py
├─ requirements.txt
├─ .env               # NOT committed to Git
├─ /templates
│   ├─ base.html
│   ├─ index.html
│   ├─ login.html
│   ├─ register.html
│   ├─ events.html
│   ├─ event_detail.html
│   ├─ event_form.html
│   ├─ clubs.html
│   ├─ club_form.html
│   └─ my_events.html
└─ /static
    └─ css/
        └─ styles.css
