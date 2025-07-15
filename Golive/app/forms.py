from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, DateField, TextAreaField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

class MasterDataForm(FlaskForm):
    file = FileField('Upload Master Data', validators=[DataRequired()])
    submit = SubmitField('Upload')

class ServerStatusForm(FlaskForm):
    date_ready = DateField('Server Ready Date', validators=[DataRequired()])
    submit = SubmitField('Set Date')

class GoLiveDateForm(FlaskForm):
    date = DateField('Go Live Date', validators=[DataRequired()])
    submit = SubmitField('Add Date')

class NoteForm(FlaskForm):
    text = TextAreaField('Note', validators=[DataRequired()])
    submit = SubmitField('Add Note')
