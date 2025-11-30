from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, TextAreaField,
    DateTimeField, SubmitField, SelectField
)
from wtforms.validators import DataRequired, Email, EqualTo, Length


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=80)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=6)]
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Create Account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


class EventForm(FlaskForm):
    title = StringField("Event Title", validators=[DataRequired()])
    description = TextAreaField("Event Description")
    location = StringField("Location", validators=[DataRequired()])
    start_time = DateTimeField(
        "Start Time (MM-DD-YYYY HH:MM)",
        format="%m-%d-%Y %H:%M %p",
        validators=[DataRequired()],
        description="Example: 12-01-2025 15:00"
    )

    # Club dropdown (choices will be set in app.py)
    club_id = SelectField("Club", coerce=int, choices=[])

    submit = SubmitField("Save Event")



class ClubForm(FlaskForm):
    name = StringField("Club Name", validators=[DataRequired(), Length(max=120)])
    description = TextAreaField("Club Description")
    submit = SubmitField("Save Club")
