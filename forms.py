from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField, BooleanField
from wtforms.fields.choices import SelectField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    name = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm your password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')


class UserForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Log In')

class PredictionForm(FlaskForm):
    race = SelectField('Race', choices=[], coerce=int, validators=[DataRequired()])
    driver_1 = SelectField('1st Place', validators=[DataRequired()])
    driver_2 = SelectField('2nd Place', validators=[DataRequired()])
    driver_3 = SelectField('3rd Place', validators=[DataRequired()])
    driver_4 = SelectField('4th Place', validators=[DataRequired()])
    driver_5 = SelectField('5th Place', validators=[DataRequired()])
    driver_6 = SelectField('6th Place', validators=[DataRequired()])
    driver_7 = SelectField('7th Place', validators=[DataRequired()])
    driver_8 = SelectField('8th Place', validators=[DataRequired()])
    driver_9 = SelectField('9th Place', validators=[DataRequired()])
    driver_10 = SelectField('10th Place', validators=[DataRequired()])
    submit = SubmitField('Submit Prediction')

class ChangeForm(FlaskForm):
    driver_1 = SelectField('1st Place', validators=[DataRequired()])
    driver_2 = SelectField('2nd Place', validators=[DataRequired()])
    driver_3 = SelectField('3rd Place', validators=[DataRequired()])
    driver_4 = SelectField('4th Place', validators=[DataRequired()])
    driver_5 = SelectField('5th Place', validators=[DataRequired()])
    driver_6 = SelectField('6th Place', validators=[DataRequired()])
    driver_7 = SelectField('7th Place', validators=[DataRequired()])
    driver_8 = SelectField('8th Place', validators=[DataRequired()])
    driver_9 = SelectField('9th Place', validators=[DataRequired()])
    driver_10 = SelectField('10th Place', validators=[DataRequired()])
    submit = SubmitField('Edit Prediction')