#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

logging.basicConfig(filename="error.log",
                              filemode='a',
                              format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                              datefmt='%H:%M:%S',
                              level=logging.ERROR)
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
  __tablename__ = 'venues'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String)
  city = db.Column(db.String(120))
  state = db.Column(db.String(120))
  address = db.Column(db.String(120))
  phone = db.Column(db.String(120))
  genres = db.Column(db.String(120))
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  website_link = db.Column(db.String(120))
  seeking_talent = db.Column(db.Boolean(), nullable=False, default=False)
  seeking_description = db.Column(db.String(120))

  venue_shows = db.relationship('Show', backref='venue_shows', lazy=True)
  # TODO: implement any missing fields, as a database migration using Flask-Migrate

  def __repr__(self):
    return f'<Venue {self.id} {self.name}>'

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
  website_link = db.Column(db.String(120))
  seeking_venue = db.Column(db.Boolean(), nullable=False, default=False)
  seeking_description = db.Column(db.String(120))

  artist_shows = db.relationship('Show', backref='artist_shows', lazy=True)
  # TODO: implement any missing fields, as a database migration using Flask-Migrate

  def __repr__(self):
    return f'<Artist {self.id} {self.name}>'

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
  __tablename__ = 'shows'

  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('artists.id', ondelete='CASCADE'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('venues.id', ondelete='CASCADE'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)

  def __repr__(self):
    return f'<Show {self.id} {self.start_time}>'
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

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
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  # Get unique locations by venue city and state
  locations = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state)
  payload = []
  for location in locations:

    # Query all venue records with locations (city, state)
    records = Venue.query.filter(Venue.city == location.city).filter(Venue.state == Venue.state).all()
    data = []
    for venue in records:
      data.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(db.session.query(Show).filter(Show.start_time > datetime.now()).all())
      })

      payload.append({
        "city": location.city,
        "state": location.state,
        "venues": data
      })
  return render_template('pages/venues.html', areas=payload)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  search_term = request.form.get('search_term', '')
  search_results = db.session.query(Venue).filter(Venue.name.ilike(f"%{search_term}%")).all()
  result_count = len(search_results)
  response = {
    "count": result_count,
    "data": search_results
  }

  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  
  data = Venue.query.filter_by(id=venue_id).outerjoin(Show).order_by('start_time').outerjoin(Artist).one()
  upcoming_shows = []
  past_shows = []
  
  for show in data.venue_shows:
    if show.start_time >= datetime.now():
      upcoming_shows.append({
        "artist_image_link": show.artist_shows.image_link,
        "artist_id": show.artist_id,
        "artist_name": show.artist_shows.name,
        "start_time": format_datetime(str(show.start_time))})
    elif show.start_time < datetime.now():
      past_shows.append({
        "artist_image_link": show.artist_shows.image_link,
        "artist_id": show.artist_id,
        "artist_name": show.artist_shows.name,
        "start_time": format_datetime(str(show.start_time))})
    else:
      print('show not processed')
  data.upcoming_shows_count = len(upcoming_shows)
  data.upcoming_shows = upcoming_shows
  data.past_shows_count = len(past_shows)
  data.past_shows = past_shows
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = VenueForm()
  print( request.form['seeking_description'])
  seeking_talent = request.form['seeking_talent'] == 'y'
  if form.validate_on_submit():
    try:
      venue = Venue(
        name = request.form['name'],
        city = request.form['city'],
        state = request.form['state'],
        address = request.form['address'],
        phone = request.form['phone'],
        genres = request.form.getlist('genres'),
        facebook_link = request.form['facebook_link'],
        image_link = request.form['image_link'],
        website_link = request.form['website_link'],
        seeking_talent = seeking_talent,
        seeking_description = request.form['seeking_description']
      )
      db.session.add(venue)
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    except Exception as e:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
      flash(e)
      db.session.rollback()
    finally:
      db.session.close()
  else:
    flash('Venue ' + request.form['name'] + ' failed due to validation error(s)!')
    flash(form.errors)
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term', '')
  search_results = db.session.query(Artist).filter(Artist.name.ilike(f"%{search_term}%")).all()
  results_count = len(search_results)
  response = {
    "count": results_count,
    "data": search_results
  }
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  
  data = Artist.query.filter_by(id=artist_id).outerjoin(Show).order_by(Show.start_time).outerjoin(Venue).one()
  upcoming_shows = []
  past_shows = []
  for show in data.artist_shows:
    if show.start_time >= datetime.now():
      upcoming_shows.append({
        "venue_image_link": show.venue_shows.image_link,
        "venue_id": show.venue_id,
        "venue_name": show.venue_shows.name,
        "start_time": format_datetime(str(show.start_time))})
    elif show.start_time < datetime.now():
      past_shows.append({
        "venue_image_link": show.venue_shows.image_link,
        "venue_id": show.venue_id,
        "venue_name": show.venue_shows.name,
        "start_time": format_datetime(str(show.start_time))})
    else:
      print('Show not processed')
  data.upcoming_shows_count = len(upcoming_shows)
  data.upcoming_shows = upcoming_shows
  data.past_shows_count = len(past_shows)
  data.past_shows = past_shows
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  try:
    artist = Artist.query.filter_by(id=artist_id).one()
    form = ArtistForm(
      name = artist.name,
      city = artist.city,
      state = artist.state,
      phone = artist.phone,
      genres = artist.genres,
      facebook_link = artist.facebook_link,
      image_link = artist.image_link,
      website_link = artist.website_link,
      seeking_venue = artist.seeking_venue,
      seeking_description = artist.seeking_description
    )
  
  except:
    flash('An error occurred. Artist ' + update_artist.name + ' could not be updated.')
    return redirect(url_for("index"))
  # TODO: populate form with fields from artist with ID <artist_id>
  finally:
    db.session.close()
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    seeking_venue = request.form['seeking_venue'] == 'y'
    artist = {
      "name": request.form["name"],
      "city": request.form["city"],
      "state": request.form["state"],
      "phone": request.form["phone"],
      "genres": request.form.getlist('genres'),
      "facebook_link": request.form["facebook_link"],
      "image_link": request.form["image_link"],
      "website_link": request.form["website_link"],
      "seeking_venue": seeking_venue,
      "seeking_description": request.form['seeking_description']
    }
    Artist.query.filter_by(id=artist_id).update(artist)
    db.session.commit()
    flash("Artist " + request.form["name"] + " update successfully.")

  except:
    db.session.rollback()
    flash("An error occurred. Artist " + request.form.get("name") + " could not be updated.")
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  # TODO: populate form with values from venue with ID <venue_id>
  venue = Venue.query.filter_by(id=venue_id).one()

  form = VenueForm(
    name = venue.name,
    genres = venue.genres,
    address = venue.address,
    city = venue.city,
    state = venue.state,
    phone = venue.phone,
    facebook_link = venue.facebook_link,
    image_link = venue.image_link,
    website_link = venue.website_link,
    seeking_talent = venue.seeking_talent,
    seeking_description = venue.seeking_description
  )
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  try:
    seeking_talent = request.form['seeking_talent'] == 'y'

    venue = {
      "name": request.form["name"],
      "city": request.form["city"],
      "state": request.form["state"],
      "address": request.form["address"],
      "phone": request.form["phone"],
      "genres": request.form.getlist('genres'),
      "facebook_link": request.form["facebook_link"],
      "image_link": request.form["image_link"],
      "website_link": request.form["website_link"],
      "seeking_talent": seeking_talent,
      "seeking_description": request.form['seeking_description']
    }
    Venue.query.filter_by(id=venue_id).update(venue)
    db.session.commit()
    flash("Venue " + request.form["name"] + " update successfully.")

  except Exception as e:
    db.session.rollback()
    flash("An error occurred. Venue " + request.form.get("name") + " could not be updated.")
  finally:
    db.session.close()
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
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = ArtistForm()
  if form.validate_on_submit():
    try:
      seeking_venue = request.form['seeking_venue'] == 'y'
      artist = Artist(
        name=request.form['name'],
        city=request.form['city'],
        state=request.form['state'],
        phone=request.form['phone'],
        genres=request.form.getlist('genres'),
        image_link=request.form['image_link'],
        seeking_venue=seeking_venue,
        seeking_description=request.form['seeking_description'],
        website_link=request.form['website_link'],
        facebook_link=request.form['facebook_link']
      )
      db.session.add(artist)
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    except Exception as e:
      db.session.rollback()
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
      logging.error(e)
    finally:
      db.session.close()
  else:
    flash('Artist ' + request.form['name'] + ' failed due to validation error(s)!')
    flash(form.errors)
  return render_template('pages/home.html')

@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  try:
    name = Artist.query.filter_by(id=artist_id).one().name
    Artist.query.filter_by(id=artist_id).delete()
    db.session.commit()
    flash('Artist ' + name + ' was successfully deleted!')
  except:
    error = True
    db.session.rollback()
    flash('An error occurred. Artist ' + name + ' could not be deleted!')
  finally:
    db.session.close()
  
  return jsonify({'success': True})

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  
  data = Show.query.join(Artist, Artist.id == Show.artist_id).join(Venue, Venue.id == Show.venue_id).all()

  response = []
  for show in data:
      response.append({
          "venue_id": show.venue_id,
          "venue_name": show.venue_shows.name,
          "artist_id": show.artist_id,
          "artist_name": show.artist_shows.name,
          "artist_image_link": show.artist_shows.image_link,
          "start_time": str(show.start_time)
      })
  return render_template('pages/shows.html', shows=response)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  form = ShowForm()
  if form.validate_on_submit():
    try:
      show = Show(
          artist_id=request.form['artist_id'],
          venue_id=request.form['venue_id'],
          start_time=request.form['start_time']
      )
      db.session.add(show)
      db.session.commit()

    # on successful db insert, flash success
      flash('Show was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    except Exception as e:
      print(e)
      flash('An error occurred. Show could not be added')
      db.session.rollback()
    finally:
      db.session.close()

  else:
    flash('Show failed due to validation error(s)!')
    flash(form.errors)
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500

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
