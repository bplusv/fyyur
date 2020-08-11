#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
from datetime import datetime

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

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

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  current_time = datetime.now().astimezone()
  areas = db.session.query(Venue.city, State.name, State.id).join(State)\
    .group_by(Venue.city, State.name, State.id).order_by(Venue.city.asc()).all()
  view_model = [{
    'city': city,
    'state': state,
    'venues': [{
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_shows': sum(show.start_time > current_time for show in venue.shows)
    } for venue in Venue.query.filter_by(city=city, state_id=state_id).all()]
  } for city, state, state_id in areas]
  return render_template('pages/venues.html', areas=view_model)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  current_time = datetime.now().astimezone()
  search_term = request.form.get('search_term', '')
  venues = Venue.query.join(State).filter(db.or_(
    Venue.name.ilike(f'%{search_term}%'),
    db.func.concat(Venue.city, ', ', State.name).ilike(f'%{search_term}%'))
  ).all()
  view_model = {
    'count': len(venues),
    'data': [{
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_shows': sum(show.start_time > current_time for show in venue.shows)
    } for venue in venues]
  }
  return render_template('pages/search_venues.html', results=view_model, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  current_time = datetime.now().astimezone()
  venue = Venue.query.get(venue_id)
  past_shows = db.session.query(Show)\
    .filter(Show.venue_id == venue_id, Show.start_time <= current_time).all()
  upcoming_shows = db.session.query(Show)\
    .filter(Show.venue_id == venue_id, Show.start_time > current_time).all()
  view_model = {
    'id': venue.id,
    'name': venue.name,
    'genres': [genre.name for genre in venue.genres],
    'address': venue.address,
    'city': venue.city,
    'state': venue.state.name,
    'phone': venue.phone,
    'website': venue.website,
    'facebook_link': venue.facebook_link,
    'seeking_talent': venue.seeking_talent,
    'seeking_description': venue.seeking_description,
    'image_link': venue.image_link,
    'past_shows': [{
      'artist_id': show.artist_id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': str(show.start_time),
    } for show in past_shows],
    'past_shows_count': len(past_shows),
    'upcoming_shows': [{
      'artist_id': show.artist_id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': str(show.start_time),
    } for show in upcoming_shows],
    'upcoming_shows_count': len(upcoming_shows)
  }
  return render_template('pages/show_venue.html', venue=view_model)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  form.state.query = State.query.order_by(State.name.asc())
  form.genres.query = Genre.query.order_by(Genre.name.asc())
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    form = request.form
    venue = Venue()
    venue.name = form['name']
    venue.city = form['city']
    venue.state_id = form['state']
    venue.address = form['address']
    venue.phone = form['phone']
    venue.genres = [Genre.query.get(id) for id in form.getlist('genres')]
    venue.image_link = form['image_link']
    venue.website = form['website']
    venue.facebook_link = form['facebook_link']
    venue.seeking_talent = form.get('seeking_talent') == 'y'
    venue.seeking_description = form['seeking_description']
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Venue ' + form['name'] + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + venue.name + ' was successfully deleted!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. The venue could not be deleted.')
    return '{ "success": "false" }'
  finally:
    db.session.close()
  return '{ "success": "true" }'

#  Artists
#  ----------------------------------------------------------------

@app.route('/artists')
def artists():
  current_time = datetime.now().astimezone()
  artists = Artist.query.order_by(Artist.name.asc()).all()
  view_model = [{
    'id': artist.id,
    'name': artist.name,
    "num_upcoming_shows": sum(show.start_time > current_time for show in artist.shows)
  } for artist in artists]
  return render_template('pages/artists.html', artists=view_model)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  current_time = datetime.now().astimezone()
  search_term = request.form.get('search_term', '')
  artists = Artist.query.join(State).filter(db.or_(
    Artist.name.ilike(f'%{search_term}%'),
    db.func.concat(Artist.city, ', ', State.name).ilike(f'%{search_term}%'))
  ).all()
  view_model = {
    "count": len(artists),
    "data": [{
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": sum(show.start_time > current_time for show in artist.shows)
    } for artist in artists]
  }
  return render_template('pages/search_artists.html', results=view_model, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  current_time = datetime.now().astimezone()
  artist = Artist.query.get(artist_id)
  past_shows = db.session.query(Show)\
    .filter(Show.artist_id == artist_id, Show.start_time <= current_time).all()
  upcoming_shows = db.session.query(Show)\
    .filter(Show.artist_id == artist_id, Show.start_time > current_time).all()
  view_model = {
    "id": artist.id,
    "name": artist.name,
    "genres": [genre.name for genre in artist.genres],
    "city": artist.city,
    "state": artist.state.name,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    'available_from': artist.available_from and artist.available_from.strftime('%I:%M %p') or '',
    'available_to': artist.available_to and artist.available_to.strftime('%I:%M %p') or '',
    "image_link": artist.image_link,
    "past_shows": [{
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": str(show.start_time)
      } for show in past_shows],
    "past_shows_count": len(past_shows),
    "upcoming_shows": [{
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": str(show.start_time)
      } for show in upcoming_shows],
    "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_artist.html', artist=view_model)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  form.state.query = State.query.all()
  form.genres.query = Genre.query.all()
  artist = Artist.query.get(artist_id)
  form.state.data = artist.state
  form.genres.data = artist.genres
  view_model = {
    'id': artist.id,
    'name': artist.name,
    'genres': [genre.name for genre in artist.genres],
    'city': artist.city,
    'state': artist.state.name,
    'phone': artist.phone,
    'image_link': artist.image_link,
    'website': artist.website,
    'facebook_link': artist.facebook_link,
    'seeking_venue': artist.seeking_venue,
    'seeking_description': artist.seeking_description or '',
    'available_from': artist.available_from and artist.available_from.strftime('%H:%M') or '',
    'available_to': artist.available_to and artist.available_to.strftime('%H:%M') or ''
  }
  return render_template('forms/edit_artist.html', form=form, artist=view_model)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    data = request.form
    artist = Artist.query.get(artist_id)
    artist.name = data['name']
    artist.city = data['city']
    artist.state = State.query.get(data['state'])
    artist.phone = data['phone']
    artist.genres = [Genre.query.get(id) for id in data.getlist('genres')]
    artist.image_link = data['image_link']
    artist.website = data['website']
    artist.facebook_link = data['facebook_link']
    artist.seeking_venue = data.get('seeking_venue') == 'y'
    artist.seeking_description = data['seeking_description']
    artist.available_from = data['available_from'] and datetime.strptime(data['available_from'], '%H:%M') or None
    artist.available_to = data['available_to'] and datetime.strptime(data['available_to'], '%H:%M') or None
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + artist.name + ' was successfully edited!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. The artist could not be edited.')
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/artists/<int:artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  try:
    artist = Artist.query.get(artist_id)
    db.session.delete(artist)
    db.session.commit()
    flash('Artist ' + artist.name + ' was successfully deleted!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. The artist could not be deleted.')
    return '{ "success": "false" }'
  finally:
    db.session.close()
  return '{ "success": "true" }'

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  form.state.query = State.query.order_by(State.name.asc())
  form.genres.query = Genre.query.order_by(Genre.name.asc())
  venue = Venue.query.get(venue_id)
  form.state.data = venue.state
  form.genres.data = venue.genres
  view_model = {
    'id': venue.id,
    'name': venue.name,
    'genres': [genre.name for genre in venue.genres],
    'address': venue.address,
    'city': venue.city,
    'state': venue.state.name,
    'phone': venue.phone,
    'image_link': venue.image_link,
    'website': venue.website,
    'facebook_link': venue.facebook_link,
    'seeking_talent': venue.seeking_talent,
    'seeking_description': venue.seeking_description or ''
  }
  return render_template('forms/edit_venue.html', form=form, venue=view_model)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    data = request.form
    venue = Venue.query.get(venue_id)
    venue.name = data['name']
    venue.city = data['city']
    venue.state = State.query.get(data['state'])
    venue.address = data['address']
    venue.phone = data['phone']
    venue.genres = [Genre.query.get(id) for id in data.getlist('genres')]
    venue.image_link = data['image_link']
    venue.website = data['website']
    venue.facebook_link = data['facebook_link']
    venue.seeking_talent = data.get('seeking_talent') == 'y'
    venue.seeking_description = data['seeking_description']
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + venue.name + ' was successfully edited!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. The venue could not be edited.')
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  form.state.query = State.query.order_by(State.name.asc())
  form.genres.query = Genre.query.order_by(Genre.name.asc())
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  try:
    data = request.form
    artist = Artist()
    artist.name = data['name']
    artist.city = data['city']
    artist.state = State.query.get(data['state'])
    artist.phone = data['phone']
    artist.genres = [Genre.query.get(id) for id in data.getlist('genres')]
    artist.image_link = data['image_link']
    artist.website = data['website']
    artist.facebook_link = data['facebook_link']
    artist.seeking_venue = data.get('seeking_venue') == 'y'
    artist.seeking_description = data['seeking_description']
    artist.available_from = data['available_from'] and datetime.strptime(data['available_from'], '%H:%M') or None
    artist.available_to = data['available_to'] and datetime.strptime(data['available_to'], '%H:%M') or None
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + data['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Artist ' + data['name'] + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.all()
  view_model = [{
    'venue_id': show.venue.id,
    'venue_name': show.venue.name,
    'artist_id': show.artist_id,
    'artist_name': show.artist.name,
    'artist_image_link': show.artist.image_link,
    'start_time': str(show.start_time)
  } for show in shows]
  return render_template('pages/shows.html', shows=view_model)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    data = request.form
    show = Show()
    show.venue_id = data['venue_id']
    show.artist_id = data['artist_id']
    show.start_time = datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S')
    artist = Artist.query.get(show.artist_id)
    if artist.available_from.time() <= show.start_time.time() <= artist.available_to.time():
      db.session.add(show)
      db.session.commit()
      flash('Show was successfully listed!')
      return render_template('pages/home.html')
    else:
      flash('Show could not be listed. Artist is not available for this schedule!')
      return redirect(url_for('create_shows'))
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Show could not be listed.')
    return render_template('pages/home.html')
  finally:
    db.session.close()

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
