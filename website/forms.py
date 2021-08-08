from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError, NumberRange
from website.models import User, Player

class RegisterForm(FlaskForm):
	# flask will search for functions with name starting with validate_<some field>
	def validate_username(self, username_to_check):
		user = User.query.filter_by(username=username_to_check.data).first()
		if user:
			raise ValidationError('Username already exists! Please try a different username.')

	def validate_email_address(self, email_address_to_check):
		email_address = User.query.filter_by(email_address=email_address_to_check.data).first()
		if email_address:
			raise ValidationError('Email address already exists! Please try a different email address.')

	username = StringField(label='User Name:', validators=[Length(min=2, max=30), DataRequired()])
	email_address = StringField(label='Email Address:', validators=[Email(), DataRequired()])
	password1 = PasswordField(label='Password:', validators=[Length(min=6), DataRequired()])
	password2 = PasswordField(label='Confirm Password:', validators=[EqualTo('password1'), DataRequired()])
	submit = SubmitField(label='Create Account')

class LoginForm(FlaskForm):
	username = StringField(label='User Name:', validators=[DataRequired()])
	password = PasswordField(label='Password:', validators=[DataRequired()])
	submit = SubmitField(label='Sign In')

# Must commment out this form when rebuilding database
class SwapRankForm(FlaskForm):
	num_players = len(Player.query.all())
	new_rank= IntegerField(label='Old Player Rank', validators=[DataRequired(), NumberRange(1, num_players - 1)])
	submit = SubmitField(label='Submit Rank Change')


