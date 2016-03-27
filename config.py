import os
basedir = os.path.abspath(os.path.dirname(__file__))


DATABASE = 'site.db'
DEBUG = True
DATABASE_PATH = os.path.join(basedir, DATABASE)
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DATABASE_PATH
SECRET_KEY = "<insert some random string here>"
IMAGE_FOLDER = 'static/files/images'
DOC_FOLDER = 'static/files/docs'
ASSIGNMENT_FOLDER = 'static/files/assignments'

MAIL_SERVER='smtp.gmail.com' # if using gmail
MAIL_PORT=465
MAIL_USE_SSL=True
MAIL_USERNAME = '<email>'
MAIL_PASSWORD = '<password>'