from pkg import app, db
import datetime


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    lizards = db.relationship("Lizard", cascade="delete")
    hobbies = db.relationship("Hobby", cascade="delete")
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80))
    picture = db.Column(db.LargeBinary)
    facebook_id = db.Column(db.String(80))
    gplus_id = db.Column(db.String(80))


class Lizard(db.Model):
    __tablename__ = 'lizard'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    picture_url = db.Column(db.String(500))
    creation_instant = db.Column(db.DateTime(timezone=True),
                                 default=datetime.datetime.utcnow)
    hobby_relationship = db.relationship("Hobby", cascade="delete")

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name':             self.name,
            'id':               self.id,
            'picture_url':      self.picture_url,
            'creation_instant': self.creation_instant
        }


class Hobby(db.Model):
    __tablename__ = 'hobby'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(250))
    lizard_id = db.Column(db.Integer, db.ForeignKey('lizard.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    picture_url = db.Column(db.String(500))
    creation_instant = db.Column(db.DateTime(timezone=True),
                                 default=datetime.datetime.utcnow)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name':             self.name,
            'description':      self.description,
            'id':               self.id,
            'picture_url':      self.picture_url,
            'creation_instant': self.creation_instant
        }








# ChangeLog table that contains instants when a lizard or hobby is added,
# updated, or deleted
class ChangeLog(db.Model):
    __tablename__ = 'changelog'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    # user = db.relationship(User)
    lizard_name = db.Column(db.String(80))
    lizard_id = db.Column(db.Integer)
    # lizard = db.relationship(Lizard)
    hobby_name = db.Column(db.String(80))
    hobby_id = db.Column(db.Integer)
    # hobby = db.relationship(Hobby)
    update_instant = db.Column(db.DateTime(timezone=True),
                               default=datetime.datetime.utcnow)
    # Possible actions are "new", "update", or "delete"
    action = db.Column(db.String(6))
    # Possible tables are "lizard" or "hobby"
    table = db.Column(db.String(9))

# Command to create all these tables
db.create_all()
