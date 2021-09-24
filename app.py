#from _typeshed import ReadableBuffer
import os
from flask.wrappers import Response
#import re

import requests
from flask import Flask, session, redirect, render_template, request, flash, url_for, json, jsonify
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

    """guardar el id en una variable, testing book id para la def book 
        hice la prueba aqui para ver si funcionaba abajo
    bookId = row.fetchone()
    print("Esto es todo lo que contiene bookId: " + str(bookId))
        esto imprime la linea de arriba: Esto es todo lo que contiene bookId: (2,)
    bookId = bookId[0]
    print("Esto es lo que contiene bookId[0]: " + str(bookId))
        esto imprime la linea de arriba: Esto es lo que contiene bookId[0]: 2
    """
    
    # Fetch all the results
    books = rows.fetchall()

    return render_template("results.html", books=books)

@app.route("/book/<isbn>", methods=["GET", "POST"])
@login_required
def book(isbn):
    if request.method == "POST":
        # Guardar actual usuario
        currentUser = session["user_id"]
        
        # Fetch la data
        rating = request.form.get("rating")
        review = request.form.get("review")
        
        # Buscar book_id por ISBN
        row = db.execute("SELECT id FROM books WHERE isbn = :isbn",
                        {"isbn": isbn})

        # Guardar id en una variable
        bookId = row.fetchone() 
        bookId = bookId[0]

        # Revisar que el usuario solo haga un submission por libro
        row2 = db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id",
                    {"user_id": currentUser,
                     "book_id": bookId})

        # Si un review ya existe
        if row2.rowcount == 1:
            
            flash('You already submitted a review for this book', 'warning')
            return redirect("/book/" + isbn)

        # Casteo de int a entero
        rating = int(rating)

        db.execute("INSERT INTO reviews (user_id, book_id, review, rating) VALUES \
                    (:user_id, :book_id, :review, :rating)",
                    {"user_id": currentUser, 
                    "book_id": bookId, 
                    "review": review, 
                    "rating": rating})

        # Cometer transaccion 
        db.commit()

        flash('Review submitted!', 'info')

        return redirect("/book/" + isbn)
    else:

        bookInfo = db.execute("SELECT id, isbn, title, author, year FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()

        response = requests.get("https://www.googleapis.com/books/v1/volumes?q=isbn:"+isbn).json()
        bookInfoApi = response["items"][0]["volumeInfo"]

        #validar imagen
        try:
            image = bookInfoApi["imageLinks"]["smallThumbnail"]
        except KeyError:
            image = "static/img/image_not_available.jpg"

        #validar descripcion
        try:
            description = bookInfoApi["description"]
        except:
            description = "Description not available"

        #validar puntaje promedio
        try:
            averageRating = bookInfoApi["averageRating"]
        except:
            averageRating = "Average rating not available"
        
        #validar cantidad de puntuaciones
        try:
            ratingsCount = bookInfoApi["ratingsCount"]
        except:
            ratingsCount = "Ratings count not available"

        id = bookInfo["id"]

        reviews = db.execute("SELECT username, review, rating from users JOIN reviews ON reviews.user_id = users.id_user where book_id = :id",
        {"id": id}).fetchall()

        return render_template("book.html", reviews=reviews, bookInfo=bookInfo, image=image, description=description, averageRating=averageRating, ratingsCount=ratingsCount)

@app.route("/api/<isbn>", methods=["GET"])
def api(isbn):

    ISBN = isbn

    book = db.execute("""SELECT * FROM "books" WHERE "isbn" = :isbn""", {"isbn": ISBN}).fetchone()

    if book:
        reviews = db.execute(""" SELECT AVG("rating"), COUNT("rating") FROM "reviews" 
                                WHERE "book_id" = :book_id """,
                                {"book_id" : book["id"]}).fetchone()

        response = {
            "title": book["title"],
            "author": book["author"],
            "year": book["year"],
            "isbn": book["isbn"],
            "review_count": str(reviews[1]),
            "average_score": str(reviews[0])
        }

        return json.dumps(response)
    else:
        return jsonify({"Error": "Invalid book ISBN"}), 404