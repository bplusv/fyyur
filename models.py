from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

venue_genres_table = db.Table('venue_genres',
    db.Column('venue_id', db.Integer, db.ForeignKey('venues.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genres.id'), primary_key=True)
)

artist_genres_table = db.Table('artist_genres',
    db.Column('artist_id', db.Integer, db.ForeignKey('artists.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genres.id'), primary_key=True)
)

class Genre(db.Model):
    __tablename__ = 'genres'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

class State(db.Model):
    __tablename__ = 'states'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    venues = db.relationship('Venue', back_populates='state', lazy=True)
    artists = db.relationship('Artist', back_populates='state', lazy=True)

class Venue(db.Model):
    __tablename__ = 'venues'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String)
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    state = db.relationship('State', back_populates='venues', lazy=True)
    genres = db.relationship('Genre', secondary=venue_genres_table, lazy=True)
    shows = db.relationship('Show', back_populates='venue', lazy=True, cascade='all, delete-orphan')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

class Artist(db.Model):
    __tablename__ = 'artists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String)
    available_from = db.Column(db.DateTime(timezone=True))
    available_to = db.Column(db.DateTime(timezone=True))
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False)
    state = db.relationship('State', back_populates='artists', lazy=True)
    genres = db.relationship('Genre', secondary=artist_genres_table, lazy=True)
    shows = db.relationship('Show', back_populates='artist', lazy=True, cascade='all, delete-orphan')
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

class Show(db.Model):
    __tablename__ = 'shows'
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), primary_key=True)
    start_time = db.Column(db.DateTime(timezone=True), primary_key=True)
    venue = db.relationship('Venue', back_populates='shows', lazy=True)
    artist = db.relationship('Artist', back_populates='shows', lazy=True)