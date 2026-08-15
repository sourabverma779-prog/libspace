import sqlite3

# Connect to database
connection = sqlite3.connect("database.db")
cursor = connection.cursor()


# ==========================================
# BOOKS TABLE
# ==========================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    pdf_filename TEXT
)
""")


# ==========================================
# ADD PDF COLUMN TO OLD DATABASE
# ==========================================

try:

    cursor.execute("""
    ALTER TABLE books
    ADD COLUMN pdf_filename TEXT
    """)

except sqlite3.OperationalError:

    # Column already exists
    pass


# ==========================================
# USERS TABLE
# ==========================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")


# ==========================================
# FAVORITES TABLE
# ==========================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,

    UNIQUE(user_id, book_id),

    FOREIGN KEY(user_id)
        REFERENCES users(id),

    FOREIGN KEY(book_id)
        REFERENCES books(id)
)
""")


# ==========================================
# SAVE CHANGES
# ==========================================

connection.commit()
connection.close()


print("Database updated successfully!")