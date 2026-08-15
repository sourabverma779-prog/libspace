from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_from_directory
)

import sqlite3
import os

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename


# ==================================================
# LIBSPACE APP
# ==================================================

app = Flask(__name__)

app.secret_key = "libspace-secret-key-2026"


# ==================================================
# CONFIGURATION
# ==================================================

UPLOAD_FOLDER = "books"

ALLOWED_EXTENSIONS = {
    "pdf",
    "jpg",
    "jpeg",
    "png",
    "webp"
}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==================================================
# ADMIN LOGIN DETAILS
# ==================================================

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# ==================================================
# DATABASE
# ==================================================

def get_connection():

    connection = sqlite3.connect("database.db")

    connection.row_factory = sqlite3.Row

    return connection


# ==================================================
# GET BOOKS
# ==================================================

def get_books():

    connection = get_connection()

    books = connection.execute(
        """
        SELECT *
        FROM books
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return books


# ==================================================
# GET ONE BOOK
# ==================================================

def get_book(book_id):

    connection = get_connection()

    book = connection.execute(
        """
        SELECT *
        FROM books
        WHERE id = ?
        """,
        (book_id,)
    ).fetchone()

    connection.close()

    return book


# ==================================================
# PDF CHECK
# ==================================================

def allowed_file(filename):

    return (
        "." in filename
        and
        filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# ==================================================
# HOME
# ==================================================

@app.route("/")
def home():

    books = get_books()

    return render_template(
        "index.html",
        books=books
    )


# ==================================================
# SEARCH
# ==================================================

@app.route("/search")
def search():

    query = request.args.get(
        "q",
        ""
    ).strip()

    category = request.args.get(
        "category",
        ""
    ).strip()

    connection = get_connection()


    if query and category:

        books = connection.execute(
            """
            SELECT *
            FROM books
            WHERE
            (
                title LIKE ?
                OR author LIKE ?
                OR category LIKE ?
                OR description LIKE ?
            )
            AND category = ?
            ORDER BY id DESC
            """,
            (
                f"%{query}%",
                f"%{query}%",
                f"%{query}%",
                f"%{query}%",
                category
            )
        ).fetchall()


    elif query:

        books = connection.execute(
            """
            SELECT *
            FROM books
            WHERE
                title LIKE ?
                OR author LIKE ?
                OR category LIKE ?
                OR description LIKE ?
            ORDER BY id DESC
            """,
            (
                f"%{query}%",
                f"%{query}%",
                f"%{query}%",
                f"%{query}%"
            )
        ).fetchall()


    elif category:

        books = connection.execute(
            """
            SELECT *
            FROM books
            WHERE category = ?
            ORDER BY id DESC
            """,
            (category,)
        ).fetchall()


    else:

        books = connection.execute(
            """
            SELECT *
            FROM books
            ORDER BY id DESC
            """
        ).fetchall()


    categories = connection.execute(
        """
        SELECT DISTINCT category
        FROM books
        ORDER BY category
        """
    ).fetchall()


    connection.close()


    return render_template(
        "search.html",
        books=books,
        categories=categories,
        query=query,
        selected_category=category
    )


# ==================================================
# BOOK DETAILS
# ==================================================

@app.route("/book/<int:book_id>")
def book_details(book_id):

    book = get_book(book_id)

    if book is None:

        return "Book not found", 404


    return render_template(
        "book.html",
        book=book
    )


# ==================================================
# READ BOOK
# ==================================================

@app.route("/read/<int:book_id>")
def read_book(book_id):

    book = get_book(book_id)

    if book is None:

        return "Book not found", 404


    return render_template(
        "reader.html",
        book=book
    )


# ==================================================
# OPEN PDF
# ==================================================

@app.route("/pdf/<path:filename>")
def open_pdf(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


# ==================================================
# USER REGISTER
# ==================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        username = request.form[
            "username"
        ].strip()

        email = request.form[
            "email"
        ].strip()

        password = request.form[
            "password"
        ]


        if not username or not email or not password:

            return render_template(
                "register.html",
                error="Please fill all fields."
            )


        hashed_password = generate_password_hash(
            password
        )


        connection = get_connection()


        try:

            connection.execute(
                """
                INSERT INTO users
                (
                    username,
                    email,
                    password
                )
                VALUES (?, ?, ?)
                """,
                (
                    username,
                    email,
                    hashed_password
                )
            )

            connection.commit()


        except sqlite3.IntegrityError:

            connection.close()

            return render_template(
                "register.html",
                error="Username or email already exists."
            )


        connection.close()


        return redirect(
            url_for("login")
        )


    return render_template(
        "register.html"
    )


# ==================================================
# USER LOGIN
# ==================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        login_value = request.form[
            "username"
        ].strip()

        password = request.form[
            "password"
        ]


        connection = get_connection()


        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            OR email = ?
            """,
            (
                login_value,
                login_value
            )
        ).fetchone()


        connection.close()


        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]

            session["username"] = user["username"]

            session["email"] = user["email"]


            return redirect(
                url_for("dashboard")
            )


        return render_template(
            "login.html",
            error="Invalid username/email or password."
        )


    return render_template(
        "login.html"
    )


# ==================================================
# USER DASHBOARD
# ==================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    connection = get_connection()


    favorites = connection.execute(
        """
        SELECT books.*
        FROM favorites

        JOIN books
        ON favorites.book_id = books.id

        WHERE favorites.user_id = ?

        ORDER BY books.id DESC
        """,
        (
            session["user_id"],
        )
    ).fetchall()


    connection.close()


    return render_template(
        "dashboard.html",
        username=session["username"],
        favorites=favorites
    )


# ==================================================
# ADD FAVORITE
# ==================================================

@app.route(
    "/add_favorite/<int:book_id>",
    methods=["POST"]
)
def add_favorite(book_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    connection = get_connection()


    connection.execute(
        """
        INSERT OR IGNORE INTO favorites
        (
            user_id,
            book_id
        )
        VALUES (?, ?)
        """,
        (
            session["user_id"],
            book_id
        )
    )


    connection.commit()

    connection.close()


    return redirect(
        request.referrer
        or
        url_for("home")
    )


# ==================================================
# REMOVE FAVORITE
# ==================================================

@app.route(
    "/remove_favorite/<int:book_id>",
    methods=["POST"]
)
def remove_favorite(book_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    connection = get_connection()


    connection.execute(
        """
        DELETE FROM favorites

        WHERE user_id = ?
        AND book_id = ?
        """,
        (
            session["user_id"],
            book_id
        )
    )


    connection.commit()

    connection.close()


    return redirect(
        request.referrer
        or
        url_for("dashboard")
    )


# ==================================================
# USER LOGOUT
# ==================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# ==================================================
# ADMIN LOGIN
# ==================================================

@app.route(
    "/admin_login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        username = request.form[
            "username"
        ].strip()

        password = request.form[
            "password"
        ]


        if (
            username == ADMIN_USERNAME
            and
            password == ADMIN_PASSWORD
        ):

            session["admin_logged_in"] = True

            return redirect(
                url_for("admin")
            )


        return render_template(
            "admin_login.html",
            error="Invalid admin username or password."
        )


    return render_template(
        "admin_login.html"
    )


# ==================================================
# ADMIN LOGOUT
# ==================================================

@app.route("/admin_logout")
def admin_logout():

    session.pop(
        "admin_logged_in",
        None
    )

    return redirect(
        url_for("home")
    )


# ==================================================
# ADMIN PANEL
# ==================================================

@app.route("/admin")
def admin():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )


    books = get_books()


    return render_template(
        "admin.html",
        books=books
    )


# ==================================================
# ADD BOOK
# ==================================================

@app.route(
    "/add_book",
    methods=["POST"]
)
def add_book():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )


    title = request.form[
        "title"
    ].strip()

    author = request.form[
        "author"
    ].strip()

    category = request.form[
        "category"
    ].strip()

    description = request.form[
        "description"
    ].strip()


    pdf = request.files.get(
        "pdf"
    )


    pdf_filename = None


    if pdf and pdf.filename:

        if not allowed_file(
            pdf.filename
        ):

            return (
                "Only PDF files are allowed.",
                400
            )


        pdf_filename = secure_filename(
            pdf.filename
        )


        base, extension = os.path.splitext(
            pdf_filename
        )

        counter = 1


        while os.path.exists(
            os.path.join(
                app.config["UPLOAD_FOLDER"],
                pdf_filename
            )
        ):

            pdf_filename = (
                f"{base}_{counter}{extension}"
            )

            counter += 1


        pdf.save(
            os.path.join(
                app.config["UPLOAD_FOLDER"],
                pdf_filename
            )
        )


    connection = get_connection()


    connection.execute(
        """
        INSERT INTO books
        (
            title,
            author,
            category,
            description,
            pdf_filename
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            title,
            author,
            category,
            description,
            pdf_filename
        )
    )


    connection.commit()

    connection.close()


    return redirect(
        url_for("admin")
    )

# ==================================================
# EDIT BOOK
# ==================================================

@app.route(
    "/edit_book/<int:book_id>",
    methods=["GET", "POST"]
)
def edit_book(book_id):

    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    book = get_book(book_id)

    if book is None:
        return "Book not found", 404

    if request.method == "POST":

        title = request.form["title"].strip()
        author = request.form["author"].strip()
        category = request.form["category"].strip()
        description = request.form["description"].strip()

        connection = get_connection()

        connection.execute(
            """
            UPDATE books
            SET title = ?,
                author = ?,
                category = ?,
                description = ?
            WHERE id = ?
            """,
            (
                title,
                author,
                category,
                description,
                book_id
            )
        )

        connection.commit()
        connection.close()

        return redirect(url_for("admin"))

    return render_template(
        "edit_book.html",
        book=book
    )
# ==================================================
# DELETE BOOK
# ==================================================

@app.route(
    "/delete_book/<int:book_id>",
    methods=["POST"]
)
def delete_book(book_id):

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for("admin_login")
        )


    connection = get_connection()


    book = connection.execute(
        """
        SELECT pdf_filename
        FROM books
        WHERE id = ?
        """,
        (book_id,)
    ).fetchone()


    if book and book["pdf_filename"]:

        pdf_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            book["pdf_filename"]
        )


        if os.path.exists(
            pdf_path
        ):

            os.remove(
                pdf_path
            )


    connection.execute(
        """
        DELETE FROM favorites
        WHERE book_id = ?
        """,
        (book_id,)
    )


    connection.execute(
        """
        DELETE FROM books
        WHERE id = ?
        """,
        (book_id,)
    )


    connection.commit()

    connection.close()


    return redirect(
        url_for("admin")
    )


# ==================================================
# START LIBSPACE
# ==================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )