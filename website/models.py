from website import db, login_manager
from website import bcrypt
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#rankings = db.Table('rankings',
#    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
#    db.Column('player_id', db.Integer(), db.ForeignKey('player.id')),
#    db.Column('ovr_rank', db.Integer())
#    )

class Rank(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer())
    player_id = db.Column(db.Integer())
    custom_rank = db.Column(db.Integer())

class Player(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    rank = db.Column(db.Integer())
    name = db.Column(db.String(length=40), nullable=False, unique=True)
    position = db.Column(db.String(length=3), nullable=False)
    team = db.Column(db.String(length=4))
    adp = db.Column(db.DECIMAL(3,2))
    fp_rank = db.Column(db.Integer())
    ffb_calc_rank = db.Column(db.Integer())
    sport_news_rank = db.Column(db.Integer())
    overall_tier = db.Column(db.Integer())
    position_rank = db.Column(db.Integer())
    #custom_rankings = db.relationship('User', secondary=rankings, backref=db.backref('ranked_players'), lazy='dynamic')

    def __repr__(self):
        return f'Player {self.name}'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length=30), nullable=False, unique=True)
    email_address = db.Column(db.String(length=50), nullable=False, unique=True)
    password_hash = db.Column(db.String(length=60), nullable=False)
    
    #rank1_id = db.Column(db.Integer(), db.ForeignKey('player.id'))
    #rank2_id = db.Column(db.Integer(), db.ForeignKey('player.id'))
    #rank3_id = db.Column(db.Integer(), db.ForeignKey('player.id'))
    #rank4_id = db.Column(db.Integer(), db.ForeignKey('player.id'))
    #rank5_id = db.Column(db.Integer(), db.ForeignKey('player.id'))
    #rank6_id = db.Column(db.Integer(), db.ForeignKey('player.id'))
    #rank7_id = db.Column(db.Integer(), db.ForeignKey('player.id'))
    #rank8_id = db.Column(db.Integer(), db.ForeignKey('player.id'))
    #rank9_id = db.Column(db.Integer(), db.ForeignKey('player.id'))
    #rank10_id = db.Column(db.Integer(), db.ForeignKey('player.id'))

    #rank1 = db.relationship("Player", foreign_keys=[rank1_id])
    #rank2 = db.relationship("Player", foreign_keys=[rank2_id])
    #rank3 = db.relationship("Player", foreign_keys=[rank3_id])
    #rank4 = db.relationship("Player", foreign_keys=[rank4_id])
    #rank5 = db.relationship("Player", foreign_keys=[rank5_id])
    #rank6 = db.relationship("Player", foreign_keys=[rank6_id])
    #rank7 = db.relationship("Player", foreign_keys=[rank7_id])
    #rank8 = db.relationship("Player", foreign_keys=[rank8_id])
    #rank9 = db.relationship("Player", foreign_keys=[rank9_id])    
    #rank10 = db.relationship("Player", foreign_keys=[rank10_id])
    #player = db.relationship("Player", foreign_keys=[rank1_id,
    #    rank2_id, rank3_id, rank4_id, rank5_id, rank6_id,
    #    rank7_id, rank8_id, rank9_id, rank10_id])
    
    @property
    def password(self):
        return self.password

    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)

        