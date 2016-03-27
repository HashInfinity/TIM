from werkzeug import generate_password_hash
import datetime

from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    """The base class model for Teachers and Students
    User role can be 'student' or 'teacher' """
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique = True)
    mobilenumber = db.Column(db.String, nullable=False)
    pwdhash = db.Column(db.String, nullable=False)
    registered_on = db.Column(db.DateTime)

    authenticated = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default = False)
    verified = db.Column(db.Boolean, default = False)
    user_role = db.Column(db.String, nullable=False)

    posts = db.relationship('Post', backref='user', lazy='dynamic')

    discussions = db.relationship('Discussion', backref='user', lazy='dynamic')

    assignments = db.relationship('Assignment', backref='user', lazy='dynamic')

    comments = db.relationship('Comment', backref='user', lazy='dynamic')

    documents = db.relationship('Document', backref='user', lazy='dynamic')

    __mapper_args__ = {
        'polymorphic_identity':'user',
        'polymorphic_on':user_role,
        'with_polymorphic':'*'
    }

    def __init__(self, name, email, password, mobilenumber, role):
        self.name = name
        self.email = email
        self.mobilenumber = mobilenumber
        self.pwdhash = generate_password_hash(password)
        self.registered_on = datetime.datetime.utcnow()
        self.user_role = role


    def is_active(self):
        return True

    def get_id(self):
        return self.id

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False

    def __repr__(self):
        return '<id: %r - email: %r - role:%r>' %(self.id, self.email, self.user_role)

class Student(User):
    """The database model for Student"""
    __tablename__="student"
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity':'student',
    }

class Teacher(User):
    """The database model for Teacher"""
    __tablename__="teacher"
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

    __mapper_args__ = {
        'polymorphic_identity':'teacher',
    }



class Category(db.Model):
    """The database model for Category"""
    __tablename__ = "category"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)	

    def __init__(self, name):
        self.name = name

    def  __repr__(self):
        return '<Category- id: %r - name: %r ->'%(self.id, self.name)

class Post(db.Model):
    """The database model for Posts"""
    __tablename__ = "post"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category',backref=db.backref('posts', lazy='dynamic'))
    documents = db.relationship('Document', backref='post', lazy='dynamic')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    def __init__(self, title, text, category_id, user_id):
        self.title = title
        self.text = text
        self.category_id = category_id
        self.user_id = user_id
        self.timestamp = datetime.datetime.utcnow()

    def  __repr__(self):
        return '<id: %r - title: %r ->'%(self.id, self.title)

class Discussion(db.Model):
    """The database model for Discussions"""
    __tablename__ = "discussion"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category',backref=db.backref('discussions', lazy='dynamic'))
    documents = db.relationship('Document', backref='discussion', lazy='dynamic')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comments = db.relationship('Comment', backref='discussion', lazy='dynamic')
    flagged = db.Column(db.Boolean, default=False)
    
    def __init__(self, title, text, category_id, user_id):
        self.title = title
        self.text = text
        self.category_id = category_id
        self.user_id = user_id
        self.timestamp = datetime.datetime.utcnow()

    def  __repr__(self):
        return '<id: %r - title: %r ->'%(self.id, self.title)

class Assignment(db.Model):
    """The database model for Assignments"""
    __tablename__ = "assignment"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category',backref=db.backref('assignments', lazy='dynamic'))
    duedate = db.Column(db.Date)
    documents = db.relationship('Document', backref='assignment', lazy='dynamic')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comments = db.relationship('Comment', backref='assignment', lazy='dynamic')

    def __init__(self, title, text, duedate, category_id, user_id):
        self.title = title
        self.text = text
        self.duedate = datetime.datetime.strptime(duedate,"%d/%m/%Y").date()
        self.category_id = category_id
        self.user_id = user_id
        self.timestamp = datetime.datetime.utcnow()

    def  __repr__(self):
        return '<id: %r - title: %r ->'%(self.id, self.title)


class Document(db.Model):
    """The database model for Documentocuments"""
    __tablename__ = "document"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String, nullable=False)
    filetype = db.Column(db.String, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    discussion_id = db.Column(db.Integer, db.ForeignKey('discussion.id'))
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'))
    parent_type = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime)

    def __init__(self, filename, filetype, parent_type, parent_id,user_id):
        self.filename = filename
        self.filetype = filetype
        self.user_id = user_id
        self.parent_type = parent_type
        self.timestamp = datetime.datetime.utcnow()
        if parent_type == 'post':
            self.post_id = parent_id
        elif parent_type == 'discussion':
            self.discussion_id = parent_id
        elif parent_type == 'assignment':
            self.assignment_id = parent_id

    def __repr__(self):
        return '<id: %r - filename: %r - filetype: %r>'%(self.id, self.filename, self.filetype)

class Comment(db.Model):
    __tablename__ = "comment"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    discussion_id = db.Column(db.Integer, db.ForeignKey('discussion.id'))
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'))
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime)
    flagged = db.Column(db.Boolean, default=False)

    def __init__(self,text,user_id, parent_type, parent_id):
        self.text = text
        self.user_id = user_id
        self.parent_type = parent_type
        if parent_type == 'post':
            self.post_id = parent_id
        elif parent_type == 'discussion':
            self.discussion_id = parent_id
        self.timestamp = datetime.datetime.utcnow()
