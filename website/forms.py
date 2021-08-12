from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError, NumberRange
from website.models import User, Player, Rank
from flask_login import current_user
from website import db

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

class AddTierForm(FlaskForm):
	def validate_new_tier_cutoff(self, new_tier_cutoff_to_check):
		players = db.session.query(Player, Rank.custom_rank, Rank.custom_tier).join(Rank, Player.id == Rank.player_id).filter(Rank.user_id == current_user.id).order_by(Rank.custom_rank).all()
		max_tier = players[-1].custom_tier
		max_tier_cutoff = db.session.query(Rank.custom_rank).filter(Rank.custom_tier == max_tier, Rank.user_id == current_user.id).order_by(Rank.custom_rank).first().custom_rank
		if new_tier_cutoff_to_check.data > len(players):
			raise ValidationError('Must enter the rank of a ranked player!')
		elif new_tier_cutoff_to_check.data <= max_tier_cutoff:
			raise ValidationError('New tier must be lower than existing tiers!')

	new_tier = IntegerField(label='New Tier', validators=[DataRequired()])
	new_tier_cutoff = IntegerField(label='New Tier Cutoff', validators=[DataRequired()])
	submit = SubmitField(label='Add Tier')






