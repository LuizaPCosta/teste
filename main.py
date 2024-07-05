from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from sqlalchemy import ForeignKey
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
import smtplib
import os

#testing how this commitment thing works
# how???
# for god's sake, how the fuck does it work??


email_sender = "luiza.dpcosta@gmail.com"
app_password = os.environ.get("APP_PASSWORD")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
ckeditor = CKEditor(app)
Bootstrap5(app)

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

app.config["TEMPLATES_AUTO_RELOAD"] = True

# CREATE DATABASE
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI")
db = SQLAlchemy(model_class=Base)
db.init_app(app)

login_manager = LoginManager() 
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

def admin_only(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.id != 1:
            return abort(403)
        return function(*args, **kwargs)
    return decorated_function

# User table for all your registered users. This is the parent table
class User(db.Model, UserMixin):
    __tablename__ = "blog_users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    posts: Mapped["BlogPost"] = relationship(back_populates="author") # works like a list that contains the posts from a specific author
    user_comments: Mapped["Comment"] = relationship(back_populates="comment_author")

# CONFIGURE TABLES
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("blog_users.id"))
    author: Mapped["User"] = relationship(back_populates="posts") # connects the posts to the user who wrote them.
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    comments: Mapped["Comment"] = relationship(back_populates="parent_post")

class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    comment_author_id: Mapped[int] = mapped_column(Integer, ForeignKey("blog_users.id"))
    comment_author: Mapped["User"] = relationship(back_populates="user_comments")
    parent_post: Mapped["BlogPost"] = relationship(back_populates="comments")
    post_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))

with app.app_context():
    db.create_all()

@app.route('/register', methods=['POST', 'GET'])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit(): # if post
        if len(db.session.execute(db.select(User).where(User.email == register_form.email.data)).scalars().all()) > 0: # if it is already registered
            flash("You already have an account on this email address")
            return redirect(url_for('login'))
        else:
            new_user = User(
                email = register_form.email.data,
                name = register_form.name.data,
                password  = generate_password_hash(register_form.password.data, method='pbkdf2:sha256', salt_length=8),
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user) 
            return redirect(url_for('get_all_posts'))
    else:   
        return render_template("register.html", form = register_form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.email == login_form.email.data)).scalars().all()
        if len(user) == 0:
            flash("Wrong email address. Maybe you don't have an account yet?")
            return render_template("login.html", form= login_form)  
        else:
            for user in user:
                pwhash = user.password
                if check_password_hash(pwhash, login_form.password.data):
                    login_user(user)
                    return redirect(url_for('get_all_posts'))
                else:
                    flash("Invalid password")
                    return render_template("login.html", form = login_form)
    else:
        return render_template("login.html", form = login_form)


@app.route('/logout')
def logout():
    logout_user()
    flash('You have successfully logged yourself out.')
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts)


@app.route("/post/<int:post_id>",methods=["POST", "GET"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

        new_comment = Comment(
            text=comment_form.comment.data,
            comment_author_id = current_user.id,
            post_id = requested_post.id
        )
        db.session.add(new_comment)
        db.session.commit()

    post_comments = db.session.execute(db.select(Comment).where(Comment.post_id == post_id)).scalars().all()
    return render_template("post.html", post=requested_post, current_user=current_user, form=comment_form, comments=post_comments)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            author=current_user,
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, current_user=current_user)


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
    return render_template("make-post.html", form=edit_form, is_edit=True, current_user=current_user)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods = ["POST", "GET"])
def contact():
    if request.method == "GET":
        return render_template("contact.html", method="get")
    else:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        with smtplib.SMTP("smtp.gmail.com") as connection:
            connection.starttls() 
            connection.login(user= email_sender, password= app_password)
            connection.sendmail(
                from_addr=email_sender, 
                to_addrs="luizacosta.paula@gmail.com", 
                msg=f"Subject:Contact from site\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage: {message}".encode('utf-8')
            ) 
        return render_template("contact.html", method="post")


if __name__ == "__main__":
    app.run(debug=True, port=5002)