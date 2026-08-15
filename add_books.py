import sqlite3

connection = sqlite3.connect("database.db")
cursor = connection.cursor()

books = [
    (
        "Python Programming Basics",
        "John Smith",
        "Programming",
        "A beginner-friendly introduction to Python programming."
    ),
    (
        "Introduction to Science",
        "David Brown",
        "Science",
        "Learn the basic concepts of science."
    ),
    (
        "Web Development Fundamentals",
        "Sarah Wilson",
        "Technology",
        "Learn HTML, CSS and JavaScript."
    ),
    (
        "World History",
        "Michael Johnson",
        "History",
        "Explore important events from world history."
    )
]

cursor.executemany("""
INSERT INTO books (title, author, category, description)
VALUES (?, ?, ?, ?)
""", books)

connection.commit()
connection.close()

print("Books added successfully!")