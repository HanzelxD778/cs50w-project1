#from _typeshed import ReadableBuffer
import os
#import re

from flask import Flask, session, redirect, render_template, request, flash, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Check for environment variable
if not os.getenv("DB_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DB_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/admin")
def admin():
    rows = db.execute("SELECT * FROM users").fetchall()

    return render_template("admin.html", rows=rows)

@app.route("/register", methods=["POST", "GET"])
def register():
    """ Register user """

    session.clear()

    if request.method == "POST":

        userExistece = db.execute("SELECT * FROM users WHERE username = :username", 
        {"username": request.form.get("username")}).fetchone()

        if userExistece:
            return render_template("error.html", message="Username already exists")
        
        elif not request.form.get("password") == request.form.get("confirmation"):
            return render_template("error.html", message="Passwords didn´t match")

        hashedPassword = generate_password_hash(request.form.get("password"))

        result = db.execute("INSERT INTO users (username, pass) VALUES (:username, :password) RETURNING id_user, username", 
                {"username": request.form.get("username"), "password": hashedPassword}).fetchone()

        db.commit()

        session["user_id"] = result[0]
        session["username"] = result[1]

        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    """ Log user in """

    session.clear()

    if request.method == "POST": 
        username = request.form.get("username")

        result = db.execute("SELECT * FROM users where username = :username", {"username": username}).fetchone()
        
        #ensure username exists and password is correct
        if result == None or not check_password_hash(result[2], request.form.get("password")):
            return render_template("error.html", message="Invalid username or password")

        #remember wich user has logged in
        session["user_id"] = result[0]
        session["username"] = result[1]

        #redirect user to home page
        return redirect(url_for("index"))

    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/search")
@login_required
def search():
    
    query = "%" + request.args.get("book") + "%"
    """query1 = request.args.get("book")
    query2 = request.form.get("book")

    print("Con args el valor es: " + str(query1))
    print("Con form el valor es: " + str(query2))"""
    
    rows = db.execute("""SELECT isbn, title, author, year FROM books WHERE
                        isbn ILIKE :query OR 
                        title ILIKE :query OR 
                        author ILIKE :query LIMIT 15""",
                        {"query": query})
    
    """print("La consulta a la bd almacenada en la variable rows tiene como valor: " + str(rows))
    print("La consulta a la bd almacenada en la variable rows tiene como valor: " + str(rows.rowcount))
    print("La consulta a la bd almacenada en la variable rows usando fetchall tiene como valor: " + str(rows.fetchall()))"""

    # Books not founded
    if rows.rowcount == 0:
        return render_template("error.html", message="we can't find books with that description.")

    #teasting boodId
    row = db.execute("SELECT id FROM books WHERE isbn = :isbn", {"isbn": "0380795272"})

    #guardar el id en una variable, testing book id
    bookId = row.fetchone()
    print("Esto es TODO lo que contiene bookId: " + str(bookId))
    bookId = bookId[0]
    print("Esto es lo que contiene bookId[0]: " + str(bookId))
    
    # Fetch all the results
    books = rows.fetchall()

    return render_template("results.html", books=books)

"""@app.route("/search/<isbn>", methods=["GET", "POST"])
@login_required
def book(isbn):
    if request.method == "POST":
        #guardar sesion del usuario
        current_user = session["id_user"]

        #almacenar la data ingresada en el formulario
        rating = request.form.get("rating")
        comment = request.form.get("comment")

        #identificar el id del libro por su isbn
        row = db.execute("SELECT id FROM books WHERE isbn = :isbn", {"isbn": isbn})

        #guardar el id en una variable
        bookId = row.fetchone()
        bookId = bookId[0]"""