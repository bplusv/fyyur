# Fyyur
Fyyur is a musical venue and artist booking site that facilitates the discovery and bookings of shows between local performing artists and venues.

- Back-end built with Python + Flask framework.
- Models and relationships with SQLAlchemy ORM, Postgresql.
- DB migrations with Alembic + Flask-Migrate.
- Front-end templates with Jinja.

This site lets you list new artists and venues, discover them, and list shows with artists as a venue owner.

### Development Setup

To start and run the local development server,

1. Initialize and activate a virtualenv:
  ```
  $ cd YOUR_PROJECT_DIRECTORY_PATH/
  $ python3 -m venv env
  $ source env/bin/activate
  ```

2. Install the dependencies:
  ```
  $ pip3 install -r requirements.txt
  ```
  
3. Run DB Migrations:
  ```
  $ flask db upgrade
  ```

4. Run the development server:
  ```
  $ FLASK_APP=app FLASK_ENV=development python3 app.py
  ```

5. Navigate to Home page [http://localhost:5000](http://localhost:5000)
