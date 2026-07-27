import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
app = Flask(__name__)
app.secret_key = "petadoption123"


# ==========================
# CREATE DATABASE TABLES
# ==========================

def create_table():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT,
        email TEXT,
        phone TEXT,
        address TEXT,
        password TEXT
    )
    """)

    # Pets Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        breed TEXT,
        age TEXT,
        gender TEXT,
        vaccinated TEXT,
        description TEXT,
        image TEXT,
        status TEXT DEFAULT 'Available'
)
""")

    # Adoptions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS adoptions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pet_id INTEGER,
        adopter_name TEXT,
        phone TEXT,
        address TEXT,
        payment_status TEXT,
        transport_method TEXT,
        request_status TEXT
    )
    """)

    # Insert Sample Pets Only Once
    cursor.execute("SELECT COUNT(*) FROM pets")
    count = cursor.fetchone()[0]

    if count == 0:

        pets = [

            (
                "Bruno",
                "Labrador",
                "2 Years",
                "Male",
                "Yes",
                "Friendly and energetic Labrador.",
                "hero.jpg"
            ),

            (
                "Kitty",
                "Persian Cat",
                "1 Year",
                "Female",
                "Yes",
                "Calm and affectionate Persian cat.",
                "hero.jpg"
            ),

            (
                "Snow",
                "Rabbit",
                "8 Months",
                "Male",
                "No",
                "Playful white rabbit.",
                "hero.jpg"
            )

        ]

        cursor.executemany("""
        INSERT INTO pets
        (name, breed, age, gender, vaccinated, description, image)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, pets)

    conn.commit()
    conn.close()


# ==========================
# HOME
# ==========================

@app.route('/')
def home():
    return render_template("index.html")


# ==========================
# REGISTER
# ==========================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        phone = request.form["phone"]
        address = request.form["address"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO users(fullname,email,phone,address,password)
        VALUES(?,?,?,?,?)
        """, (fullname, email, phone, address, password))

        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# ==========================
# LOGIN
# ==========================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:
            session['user'] = user[1]
            if email == "admin@gmail.com":
                return redirect(url_for('admin'))
            return redirect(url_for('pets'))
        else:
            return "Invalid Email or Password"
    
    return render_template("login.html")

    # ==========================
# PET LIST
# ==========================

@app.route('/pets')
def pets():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM pets WHERE status='Available'")

    pets = cursor.fetchall()

    conn.close()

    return render_template("pets.html", pets=pets)


# ==========================
# PET DETAILS
# ==========================

@app.route('/pet-details/<int:pet_id>')
def pet_details(pet_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM pets WHERE id=?",
        (pet_id,)
    )

    pet = cursor.fetchone()

    conn.close()

    if pet is None:
        return "Pet not found"

    return render_template("pet_details.html", pet=pet)


# ==========================
# ADOPTION
# ==========================

@app.route('/adoption/<int:pet_id>', methods=['GET', 'POST'])
def adoption(pet_id):

    if request.method == "POST":

        adopter_name = request.form["adopter_name"]
        phone = request.form["phone"]
        address = request.form["address"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO adoptions
        (
            pet_id,
            adopter_name,
            phone,
            address,
            payment_status,
            transport_method,
            request_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            pet_id,
            adopter_name,
            phone,
            address,
            "Pending",
            "",
            "Pending"
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("payment", pet_id=pet_id))

    return render_template(
        "adoption.html",
        pet_id=pet_id
    )

    # ==========================
# PAYMENT
# ==========================

@app.route('/payment/<int:pet_id>', methods=['GET', 'POST'])
def payment(pet_id):

    if request.method == "POST":

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE adoptions
        SET payment_status = ?
        WHERE pet_id = ?
        """, ("Paid", pet_id))

        conn.commit()
        conn.close()

        return redirect(url_for("transport", pet_id=pet_id))

    return render_template(
        "payment.html",
        pet_id=pet_id
    )


# ==========================
# TRANSPORT
# ==========================

@app.route('/transport/<int:pet_id>', methods=['GET', 'POST'])
def transport(pet_id):

    if request.method == 'POST':

        transport_method = request.form['transport']

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE adoptions
        SET transport_method = ?
        WHERE pet_id = ?
        """, (transport_method, pet_id))

        conn.commit()
        conn.close()

        return redirect(url_for('success'))

    return render_template("transport.html", pet_id=pet_id)


@app.route('/success')
def success():
    return render_template("success.html")
# ==========================
# ADMIN DASHBOARD
# ==========================

@app.route('/admin')
def admin():
    if 'user' not in session:
        return redirect(url_for('login'))
    if session['user'] != "Admin":
        return "Access Denied!"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        adoptions.id,
        pets.name,
        adoptions.adopter_name,
        adoptions.phone,
        adoptions.payment_status,
        adoptions.transport_method,
        adoptions.request_status

    FROM adoptions

    JOIN pets

    ON adoptions.pet_id = pets.id
    """)

    requests = cursor.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        requests=requests
    )


@app.route('/approve/<int:request_id>')
def approve(request_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Approve the adoption request
    cursor.execute("""
    UPDATE adoptions
    SET request_status = 'Approved'
    WHERE id = ?
    """, (request_id,))

    # Find the pet ID for this adoption
    cursor.execute("""
    SELECT pet_id
    FROM adoptions
    WHERE id = ?
    """, (request_id,))

    pet_id = cursor.fetchone()[0]

    # Mark the pet as adopted
    cursor.execute("""
    UPDATE pets
    SET status = 'Adopted'
    WHERE id = ?
    """, (pet_id,))

    conn.commit()
    conn.close()

    return redirect(url_for('admin'))


@app.route('/reject/<int:request_id>')
def reject(request_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE adoptions
    SET request_status = ?
    WHERE id = ?
    """, ("Rejected", request_id))

    conn.commit()
    conn.close()

    return redirect(url_for('admin'))
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/about')
def about():
    return render_template("about.html")
@app.route('/contact')
def contact():
    return render_template("contact.html")
if __name__ == "__main__":
    create_table()
    app.run(debug=True)