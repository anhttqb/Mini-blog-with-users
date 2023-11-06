from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

# URL and api key for generating random avatar
AVATAR_GENERATOR_URL = 'https://api.multiavatar.com/'
MULTIAVATAR_API_KEY = 'NDbS9WgI7qv8hL'

db = SQLAlchemy()

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    # Create a ForeignKey, "users.id" refers to the table name of User
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # create a reference to the User object, this author is an instance of User class
    author = relationship("User", back_populates="posts")
    # create a reference to the one or more comment objects
    comments = relationship("Comment", back_populates="parent_post")


    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

#Create a User table for all your registered users.
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100), nullable=False)

    # This will hold a list of one or many blog post objects which belong to an user
    posts = relationship("BlogPost", back_populates="author")
    # This will hold a list of one or many comments objects which belong to an user
    comments = relationship("Comment", back_populates="author")

    # generate random avatar for user in comment section
    def generate_avatar(self):
        return f'{AVATAR_GENERATOR_URL}{self.name}.svg'

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer(), primary_key=True)
    author_id = db.Column(db.Integer(), db.ForeignKey("users.id"))
    author = relationship("User", back_populates="comments")
    # Create a connection with blog post object
    post_id = db.Column(db.Integer(), db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    text = db.Column(db.String())
