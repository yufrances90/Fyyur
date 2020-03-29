#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import datetime

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

# the relationship between Venue & Genre
venue_genres = db.Table('venue_genres',
    db.Column('venue_id', db.Integer, db.ForeignKey('venues.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genres.id'), primary_key=True)
)

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, default = False)
    seeking_description = db.Column(db.String)
    created_time = db.Column(db.DateTime)

    shows = db.relationship('Show', backref='venue', lazy=True)
    genres = db.relationship( \
      'Genre', \
      secondary = venue_genres, \
      backref=db.backref('genres', lazy=True), \
      collection_class=set \
        )
      

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, default = False)
    seeking_description = db.Column(db.String)
    created_time = db.Column(db.DateTime)

    shows = db.relationship('Show', backref='artist', lazy=True)
    genres = db.relationship('Artist_Genre', backref='artist', lazy=True)

    
class Show(db.Model):
  __tablename__ = 'shows'

  id = db.Column(db.Integer, primary_key = True)
  venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable = False)
  artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable = False)
  start_time = db.Column(db.DateTime)

class Genre(db.Model):
  __tablename__ = 'genres'
  
  id = db.Column(db.Integer, primary_key = True)
  name = db.Column(db.String(300), nullable = False)

class Artist_Genre(db.Model):
  __tablename__ = 'artist_genres'

  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable = False)
  genre_id = db.Column(db.Integer, db.ForeignKey('genres.id'), nullable = False)

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

  venues = Venue.query.order_by(Venue.created_time).limit(10).all()

  artists = Artist.query.order_by(Artist.created_time).limit(10).all()

  return render_template('pages/home.html', venues=venues, artists=artists)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

  res = db.session.query( \
    Venue.city, \
    Venue.state \
    ) \
        .distinct() \
        .all()

  data = []

  for entry in res:
    tmpObj = {
      'city': entry.city,
      'state': entry.state,
      'venues': db.session \
        .query( \
          Venue.name, \
          Venue.id, \
          db.func.count(Show.artist_id) \
            .filter(Show.start_time > datetime.datetime.now()).label('num_upcoming_shows') \
        ) \
        .outerjoin('shows') \
        .filter(Venue.city == entry.city) \
        .filter(Venue.state == entry.state) \
        .group_by(Venue.name, Venue.id) \
        .all()
    }
    data.append(tmpObj)

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():

  data = []

  search_term = request.form.get('search_term', '')

  if (search_term == ''):
    data = db.session \
        .query( \
          Venue.name, \
          Venue.id, \
          db.func.count(Show.artist_id) \
            .filter(Show.start_time > datetime.datetime.now()).label('num_upcoming_shows') \
        ) \
        .outerjoin('shows') \
        .group_by(Venue.name, Venue.id) \
        .all()
  else:
    data = db.session \
      .query( \
        Venue.name, \
        Venue.id, \
        db.func.count(Show.artist_id) \
          .filter(Show.start_time > datetime.datetime.now()).label('num_upcoming_shows') \
      ) \
      .outerjoin('shows') \
      .filter(Venue.name.contains(search_term)) \
      .group_by(Venue.name, Venue.id) \
      .all()

  response={
    "count": len(data),
    "data": data
  }

  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  data = db.session.query(Venue).join(Genre, Venue.genres).filter(Venue.id == venue_id).first()

  data.venue_genres = []

  for genre in data.genres:
    data.venue_genres.append(genre.name)

  data.past_shows = \
    db.session.query( \
      Show.artist_id, \
      db.func.to_char(Show.start_time, 'yyyy-mm-dd hh:mm').label('start_time'), \
      Artist.name.label('artist_name'), \
      Artist.image_link.label('artist_image_link') \
     ) \
    .join(Artist) \
    .filter(Show.start_time < datetime.datetime.now()) \
    .filter(Show.venue_id == venue_id).distinct().all()

  data.past_shows_count = len(data.past_shows)

  data.upcoming_shows = \
    db.session.query( \
      Show.artist_id, \
      db.func.to_char(Show.start_time, 'yyyy-mm-dd hh:mm').label('start_time'), \
      Artist.name.label('artist_name'), \
      Artist.image_link.label('artist_image_link') \
     ) \
    .join(Artist) \
    .filter(Show.start_time > datetime.datetime.now()) \
    .filter(Show.venue_id == venue_id).distinct().all()

  data.upcoming_shows_count = len(data.upcoming_shows)

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  try:
    
    # basic venue info
    venue = Venue (
      name = request.form['name'],
      city = request.form['city'],
      state = request.form['state'],
      address = request.form['address'],
      phone = request.form['phone'],
      facebook_link = request.form['facebook_link'],
      image_link = request.form['image_link'],
      seeking_talent = request.form.get('seeking_talent', False, type=bool),
      seeking_description = request.form['seeking_description'],
      website = request.form['website'],
      created_time = datetime.datetime.now()
    )

    db.session.add(venue)

    genre_names = request.form.getlist('genres')

    for gname in genre_names:
        genre = Genre.query.filter_by(name = gname).first()

        if genre is None:
          genre = Genre(name = gname)

        venue.genres.add(genre)

    db.session.commit()

    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')

  except Exception as e:

    print(e)

    flash('An error occurred. Venue ' + request.form.name + ' could not be listed.')

  return index()

@app.route('/venues/<int:venue_id>/delete', methods=['GET'])
def delete_venue(venue_id):

  try:

    # NO delete if there exist shows happening at this venue
    shows = db.session.query(Show).filter_by(venue_id = venue_id).all()

    if len(shows) > 0:

      flash('There is a show associated with this venue. Venue ' + str(venue_id) + ' could not be deleted.')
      
      return index()
  
    # delete venue genre association without deleteing genres
    data = db.session.query(Venue).join(Genre, Venue.genres).filter(Venue.id == venue_id).first()

    data.genres.clear()

    # delete basic venue info
    db.session.query(Venue).filter(Venue.id == venue_id).delete()

    db.session.commit()

    # on successful db insert, flash success
    flash('Venue with ID: ' + str(venue_id) + ' was successfully deleted!')

  except Exception as e:

    print(e)

    flash('An error occurred. Venue ' + str(venue_id) + ' could not be deleted.')
  
  return index()

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

  data = Artist.query.all()

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  
  search_term = request.form.get('search_term', '')

  res = Artist.query.all() if search_term == '' else Artist.query.filter(Artist.name.contains(search_term)).all()

  response={
    "count": len(res),
    "data": res
  }

  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  data = Artist.query.get(artist_id)

  genres = db.session.query(Genre).join(Artist_Genre).filter(Artist_Genre.artist_id == artist_id).all()

  data.artist_genres = []

  for genre in genres:
    data.artist_genres.append(genre.name)

  data.upcoming_shows = db.session.query( \
    Show.venue_id,
    db.func.to_char(Show.start_time, 'yyyy-mm-dd hh:mm').label('start_time'), \
    Venue.image_link.label('venue_image_link'), \
    Venue.name.label('venue_name') \
      ) \
      .filter(Show.artist_id == artist_id).join(Venue) \
      .filter(Show.start_time > datetime.datetime.now()).all()

  data.upcoming_shows_count = len(data.upcoming_shows)

  data.past_shows = db.session.query( \
    Show.venue_id,
    db.func.to_char(Show.start_time, 'yyyy-mm-dd hh:mm').label('start_time'), \
    Venue.image_link.label('venue_image_link'), \
    Venue.name.label('venue_name') \
      ) \
      .filter(Show.artist_id == artist_id).join(Venue) \
      .filter(Show.start_time < datetime.datetime.now()).all()

  data.past_shows_count = len(data.past_shows)

  return render_template('pages/show_artist.html', artist=data)

@app.route('/artists/<int:artist_id>/delete', methods=['GET'])
def delete_artist(artist_id):

  try:
    
    # NO delete if there exist shows happening at this venue
    shows = db.session.query(Show).filter_by(artist_id = artist_id).all()

    if len(shows) > 0:

      flash('There is a show associated with this artist. Artist ' + str(artist_id) + ' could not be deleted.')
      
      return index()

    # delete artist genre association without deleteing genres
    db.session.query(Artist_Genre).filter(Artist_Genre.artist_id == artist_id).delete()

    # delete basic artist info
    db.session.query(Artist).filter(Artist.id == artist_id).delete()

    db.session.commit()

    # on successful db insert, flash success
    flash('Artist with ID: ' + str(artist_id) + ' was successfully deleted!')

  except Exception as e:
    
    print(e)

    flash('An error occurred. Venue ' + str(artist_id) + ' could not be deleted.')

  return index()

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  form = ArtistForm()

  data = Artist.query.get(artist_id)

  genres = db.session.query(Genre).join(Artist_Genre).filter(Artist_Genre.artist_id == artist_id).all()

  data.artist_genres = []

  for genre in genres:
    data.artist_genres.append(genre.name)

  form.state.default = data.state
  form.genres.default = data.artist_genres
  form.seeking_venue.default = data.seeking_venue
  form.seeking_description.default = data.seeking_description

  form.process()

  return render_template('forms/edit_artist.html', form=form, artist=data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

  # update basic artist info
  db.session.query(Artist).filter(Artist.id == artist_id).update({
    'name': request.form['name'],
    'city': request.form['city'],
    'state': request.form['state'],
    'phone': request.form['phone'],
    'facebook_link': request.form['facebook_link'], 
    'image_link': request.form['image_link'], 
    'website': request.form['website'],
    'seeking_description': request.form['seeking_description'],
    'seeking_venue': request.form.get('seeking_venue', False, type=bool)
  })

  db.session.query(Artist_Genre).filter(Artist_Genre.artist_id == artist_id).delete()

  # update genres 
  genre_names = request.form.getlist('genres')

  for gname in genre_names:
    
    target_genre = Genre.query.filter_by(name = gname).first()

    if target_genre is None:
      genre = Genre(name = gname)
      db.session.add(genre)
      target_genre = Genre.query.filter_by(name = gname).first()

    genre_id = target_genre.id

    artist_genre = Artist_Genre(artist_id = artist_id, genre_id = genre_id)

    db.session.add(artist_genre)


  db.session.commit()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

  form = VenueForm()

  data = db.session.query(Venue).join(Genre, Venue.genres).filter(Venue.id == venue_id).first()

  data.venue_genres = []

  for genre in data.genres:
    data.venue_genres.append(genre.name)

  form.state.default = data.state
  form.genres.default = data.venue_genres
  form.seeking_talent.default = data.seeking_talent
  form.seeking_description.default = data.seeking_description

  form.process()

  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  # update basic venue info
  db.session.query(Venue).filter(Venue.id == venue_id).update({
    'name': request.form['name'],
    'city': request.form['city'],
    'state': request.form['state'],
    'address': request.form['address'],
    'phone': request.form['phone'],
    'facebook_link': request.form['facebook_link'], 
    'image_link': request.form['image_link'], 
    'website': request.form['website'],
    'seeking_description': request.form['seeking_description'],
    'seeking_talent': request.form.get('seeking_talent', False, type=bool)
  })

  # update genres associated with the selected venue
  saved_venue = db.session.query(Venue).join(Genre, Venue.genres).filter(Venue.id == venue_id).first()

  saved_venue.genres.clear()

  genre_names = request.form.getlist('genres')

  for gname in genre_names:
        genre = Genre.query.filter_by(name = gname).first()

        if genre is None:
          genre = Genre(name = gname)

        saved_venue.genres.add(genre)

  db.session.commit()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form

  try:
    
    artist = Artist(
      name = request.form['name'],
      city = request.form['city'],
      state = request.form['state'],
      phone =  request.form['phone'],
      facebook_link = request.form['facebook_link'],
      image_link = request.form['image_link'],
      seeking_venue = request.form.get('seeking_venue', False, type=bool),
      seeking_description = request.form['seeking_description'],
      website = request.form['website'],
      created_time = datetime.datetime.now()
    )
    
    db.session.add(artist)

    genre_names = request.form.getlist('genres')

    for gname in genre_names:
      
      target_genre = Genre.query.filter_by(name = gname).first()

      if target_genre is None:
        genre = Genre(name = gname)
        db.session.add(genre)
        target_genre = Genre.query.filter_by(name = gname).first()

      genre_id = target_genre.id
      artist_id = artist.id

      artist_genre = Artist_Genre(artist_id = artist_id, genre_id = genre_id)

      db.session.add(artist_genre)

      db.session.commit()

    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')

  except:
    
    flash('An error occurred. Artist ' + request.form.name + ' could not be listed.')
  
  return index()


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

  data = db.session.query( \
    Show.venue_id, \
    Venue.name.label('venue_name'), \
    Show.artist_id,
    Artist.name.label('artist_name'),
    Artist.image_link.label('artist_image_link'), \
    db.func.to_char(Show.start_time, 'yyyy-mm-dd hh:mm').label('start_time') \
  ) \
  .join(Venue, Venue.id == Show.venue_id) \
  .join(Artist, Artist.id == Show.artist_id) \
  .all()

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():

  try:
    
    show = Show(
      artist_id = request.form['artist_id'],
      venue_id = request.form['venue_id'],
      start_time = datetime.datetime.strptime(request.form['start_time'], '%Y-%m-%d %H:%M:%S')
    )

    db.session.add(show)

    db.session.commit()

    # on successful db insert, flash success
    flash('Show was successfully listed!')

  except:

    flash('An error occurred. Show could not be listed.')

  return index()

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
