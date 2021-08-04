from website import db, login_manager
from website import bcrypt
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length=30), nullable=False, unique=True)
    email_address = db.Column(db.String(length=50), nullable=False, unique=True)
    password_hash = db.Column(db.String(length=60), nullable=False)
    # add team and ranks, which point to other tables
    
    @property
    def password(self):
        return self.password

    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)

class Player(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    rank = db.Column(db.Integer(), nullable=False)
    name = db.Column(db.String(length=40), nullable=False, unique=True)
    position = db.Column(db.String(length=3), nullable=False)
    team = db.Column(db.String(length=4))
    fp_rank = db.Column(db.Integer())
    ffb_calc_rank = db.Column(db.Integer())
    sport_news_rank = db.Column(db.Integer())

    def __repr__(self):
        return f'Player {self.name}'


        