from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, DateTimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, URL
from flask_wtf.file import FileField, FileAllowed

# ---------- AUTH FORMS ----------

class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")]
    )
    role = SelectField(
        "Role",
        choices=[("student", "Student"), ("officer", "Club Officer")],
        validators=[DataRequired()]
    )
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


# ---------- PROFILE FORM ----------

class ProfileForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=80)])
    profile_image = FileField("Profile Picture (optional)", validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "gif"], "Images only!")])
    submit = SubmitField("Save Changes")


# ---------- CLUB FORM ----------

class ClubForm(FlaskForm):
    name = StringField("Club Name", validators=[DataRequired(), Length(max=120)])
    short_description = StringField("Card Preview (1–2 sentences)", validators=[Optional(), Length(max=200)])
    description = TextAreaField("Club Details", validators=[Optional()])
    image = FileField("Club Logo (optional)", validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "gif"], "Images only!")])
    banner = FileField("Club Banner (optional)", validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "gif"], "Images only!")])
    website = StringField("Website", validators=[Optional(), URL(message="Please enter a valid URL (include http:// or https://)")])
    contact_email = StringField("Contact Email", validators=[Optional(), Email(), Length(max=120)])
    contact_phone = StringField("Contact Phone", validators=[Optional(), Length(max=50)])
    submit = SubmitField("Save Club")


# ---------- EVENT FORM ----------

class EventForm(FlaskForm):
    title = StringField("Event Title", validators=[DataRequired(), Length(max=150)])
    description = TextAreaField("Event Description", validators=[Optional()])
    location = StringField("Location", validators=[DataRequired(), Length(max=150)])
    start_time = DateTimeField("Start Time", format="%m-%d-%Y %I:%M %p", validators=[DataRequired()])
    end_time = DateTimeField("End Time", format="%m-%d-%Y %I:%M %p", validators=[Optional()])
    club_id = SelectField("Hosting Club", coerce=int, validators=[DataRequired()])
    image = FileField("Event Image (optional)", validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "gif"], "Images only!")])
    submit = SubmitField("Save Event")
