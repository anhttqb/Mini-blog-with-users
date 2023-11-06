from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import login_user, LoginManager, current_user, logout_user
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
import yagmail
from decouple import config
# Import needed tables in database
from tables import db, BlogPost, User, Comment
# Import needed forms from the forms.py
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm


MY_EMAIL = 'malborohell@gmail.com'
EMAIL_APP_PW = config('EMAIL_APP_PW')

app = Flask(__name__)
app.config['SECRET_KEY'] = config('SECRET_APP_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)


#Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# create admin only decorator
def admin_only(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        try:
            if current_user.id != 1:
                abort(403)
            else:
                return function(*args, **kwargs)
        # handle when no user is logged in but still try to get the route of admin's authority
        except AttributeError:
            abort(403)

    return decorated_function


# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = config('DB_URI')
db.init_app(app)
with app.app_context():
    db.create_all()


# Use Werkzeug to hash the user's password when creating a new user.
@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        try:
            email = register_form.email.data
            password = generate_password_hash(register_form.password.data, salt_length=8)
            name = register_form.name.data
            new_user = User(
                email=email, password=password, name=name
            )
            db.session.add(new_user)
            db.session.commit()
            # Authenticate new user after adding details to database
            login_user(new_user)
            return redirect(url_for("get_all_posts"))
        except IntegrityError:
            flash("You've already signed up with that email, please login instead.")
            return redirect(url_for("login"))
    return render_template("register.html", form=register_form, logged_in=current_user.is_authenticated)


# Retrieve a user from the database based on their email.
@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        email = login_form.email.data
        password = login_form.password.data
        # find user by email
        user = User.query.filter(User.email == email).first()
        if not user:
            flash("The user's email does not exist, please try again!")
            return render_template("login.html", form=login_form)
        elif not check_password_hash(pwhash=user.password, password=password):
            flash("Password is incorrect, please try again!")
            return render_template("login.html", form=login_form)
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))
    return render_template("login.html", form=login_form, logged_in=current_user.is_authenticated)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html",
                           all_posts=posts,
                           logged_in=current_user.is_authenticated,
                           user=current_user)


# Allow logged-in users to comment on posts
@app.route("/post/<int:post_id>", methods=['GET', "POST"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment!")
            return redirect(url_for('login'))
        else:
            new_comment = Comment(
                author_id=current_user.id,
                post_id=post_id,
                text=comment_form.comment.data
            )
            db.session.add(new_comment)
            db.session.commit()

    return render_template("post.html",
                           post=requested_post,
                           user=current_user,
                           comment_form=comment_form,
                           logged_in=current_user.is_authenticated)


# Use a decorator so only an admin user can create a new post
@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


# Use a decorator so only an admin user can edit a post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True)


# Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html", logged_in=current_user.is_authenticated)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        message = request.form['message']
        # Send email to the blog owner
        # send_message(name, email, phone, message)
        return render_template("contact.html", msg_sent=True)
    return render_template("contact.html", logged_in=current_user.is_authenticated, msg_sent=False)

# Function to automatically send email with provided information
def send_message(name, email, phone, message):
    yag = yagmail.SMTP(user=MY_EMAIL, password=EMAIL_APP_PW)
    subject = f"New Message from {name}"
    body = f"Hi, I'm {name} - Phone: {phone} - Email: {email}\nMy message for you: {message}"
    yag.send(to=MY_EMAIL, subject=subject, contents=body)


if __name__ == "__main__":
    app.run(debug=True, port=5002)
