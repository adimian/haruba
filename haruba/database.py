from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Zone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    path = db.Column(db.String(256))

    def __init__(self, name, path):
        self.name = name
        self.path = path


class ReadableFile(db.Model):
    __tablename__ = 'extensions'
    id = db.Column(db.Integer, primary_key=True)
    extension = db.Column(db.String(128))

    def __init__(self, ext):
        self.extension = ext
