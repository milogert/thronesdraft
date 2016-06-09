from app import db

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), index=True)
    uuid = db.Column(db.String(256), index=True, unique=True)
    players = db.Column(db.Integer)
    staged = db.Column(db.String(1))

    def __repr__(self):
        return '<Room {} {} ready:{}>'.format(self.name, self.uuid, self.staged)


class RoomPlayer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_uuid = db.Column(db.String(256))
    player_name = db.Column(db.String(256))

    __table_args__ = (
        db.UniqueConstraint('room_uuid', 'player_name', name='no_double_players'),
    )


class RoomPack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_uuid = db.Column(db.String(256))
    pack_code = db.Column(db.String(64))


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pack_code = db.Column(db.String(64))
    pack_name = db.Column(db.String(64))
    position = db.Column(db.String(64))
    code = db.Column(db.String(64), unique=True)
    name = db.Column(db.String(64))
    octgn_id = db.Column(db.String(64), unique=True)
    url = db.Column(db.String(64), unique=True)
    imagesrc = db.Column(db.String(64), unique=True)

    def __repr__(self):
        return '<Card {} {}>'.format(self.name, self.code)


class Pack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    code = db.Column(db.String(64), unique=True)
    position = db.Column(db.Integer)
    cycle_position = db.Column(db.Integer)
    available = db.Column(db.String(10))
    known = db.Column(db.Integer)
    total = db.Column(db.Integer)
    url = db.Column(db.String(256))

    def __repr__(self):
        return '<Pack %r>' % (self.name)

    @property
    def serialize(self):
        '''Returns data in a serializable format.'''
        return {
            'name': self.name,
            'code': self.code,
            'position': self.position,
            'cycle_position': self.cycle_position,
            'available': self.available,
            'known': self.known,
            'total': self.total,
            'url': self.url
        }

