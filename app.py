import sqlite3
import datetime
import re
import os
import base64
import uuid

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "petadoption123"

# ==========================
# IMAGE UPLOAD SETTINGS
# ==========================

UPLOAD_FOLDER = "static/images"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["MAX_FORM_MEMORY_SIZE"] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp"
}


def save_cropped_image(cropped_data):
    """
    Decodes base64 cropped image data from Cropper.js and saves to UPLOAD_FOLDER.
    Returns the generated filename or None if invalid.
    """
    if not cropped_data or not isinstance(cropped_data, str) or not cropped_data.startswith("data:image"):
        return None
    try:
        header, encoded = cropped_data.split(",", 1)
        ext = "jpg"
        if "image/png" in header:
            ext = "png"
        elif "image/webp" in header:
            ext = "webp"
        elif "image/gif" in header:
            ext = "gif"

        filename = f"pet_{uuid.uuid4().hex[:12]}.{ext}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        with open(filepath, "wb") as fh:
            fh.write(base64.b64decode(encoded))
        return filename
    except Exception as e:
        print(f"Error saving cropped image: {e}")
        return None


def get_approximate_time(method):
    if not method:
        return "Approximately 2–4 hours"
    m = method.strip().lower()
    if "pickup" in m or "pick up" in m:
        return "Approximately 30–60 minutes"
    return "Approximately 2–4 hours"


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# ==========================
# CREATE DATABASE TABLES
# ==========================

def create_table():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # ==========================
    # USERS TABLE
    # ==========================
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

    # Add role column if it doesn't already exist
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [column[1] for column in cursor.fetchall()]

    if "role" not in user_columns:
        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN role TEXT DEFAULT 'Adopter'
        """)

    # Add account status for shelter approval workflow
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [column[1] for column in cursor.fetchall()]

    if "account_status" not in user_columns:
        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN account_status TEXT DEFAULT 'Active'
        """)

    # ==========================
    # PETS TABLE
    # ==========================
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

    cursor.execute("PRAGMA table_info(pets)")
    pet_columns = [column[1] for column in cursor.fetchall()]

    if "shelter_id" not in pet_columns:
        cursor.execute("""
            ALTER TABLE pets
            ADD COLUMN shelter_id INTEGER
        """)

    # ==========================
    # ADOPTIONS TABLE
    # ==========================
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

    cursor.execute("PRAGMA table_info(adoptions)")
    adoption_columns = [column[1] for column in cursor.fetchall()]

    if "payment_method" not in adoption_columns:
        cursor.execute("""
            ALTER TABLE adoptions
            ADD COLUMN payment_method TEXT DEFAULT 'Online'
        """)

    if "payment_amount" not in adoption_columns:
        cursor.execute("""
            ALTER TABLE adoptions
            ADD COLUMN payment_amount REAL DEFAULT 0
        """)

    if "refund_status" not in adoption_columns:
        cursor.execute("""
            ALTER TABLE adoptions
            ADD COLUMN refund_status TEXT DEFAULT 'Not Applicable'
        """)

    if "transport_date" not in adoption_columns:
        cursor.execute("""
            ALTER TABLE adoptions
            ADD COLUMN transport_date TEXT
        """)

    if "transport_time" not in adoption_columns:
        cursor.execute("""
            ALTER TABLE adoptions
            ADD COLUMN transport_time TEXT
        """)

    if "transport_status" not in adoption_columns:
        cursor.execute("""
            ALTER TABLE adoptions
            ADD COLUMN transport_status TEXT DEFAULT 'Not Scheduled'
        """)

    if "adopter_id" not in adoption_columns:
        cursor.execute("""
            ALTER TABLE adoptions
            ADD COLUMN adopter_id INTEGER
        """)

    # ==========================
    # MESSAGES TABLE
    # ==========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        email TEXT,
        subject TEXT,
        message TEXT,
        status TEXT DEFAULT 'Unread',
        reply TEXT,
        created_at TEXT,
        shelter_id INTEGER,
        pet_id INTEGER
    )
    """)

    # ==========================
    # INSERT SAMPLE PETS IF EMPTY
    # ==========================
    # Ensure default Admin exists
    cursor.execute("SELECT id FROM users WHERE email = 'admin@petadoption.com' OR role = 'Admin'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO users(fullname, email, phone, address, password, role, account_status)
            VALUES ('Administrator', 'admin@petadoption.com', '9999999999', 'Headquarters', 'admin123', 'Admin', 'Approved')
        """)

    # Ensure default Transport Provider exists
    cursor.execute("SELECT id FROM users WHERE email = 'transport@petadoption.com' OR role = 'Transport'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO users(fullname, email, phone, address, password, role, account_status)
            VALUES ('Pet Transport Express', 'transport@petadoption.com', '9876543219', 'Transport Hub Central', 'transport123', 'Transport', 'Approved')
        """)

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
                "hero.jpg",
                "Available"
            ),
            (
                "Kitty",
                "Persian Cat",
                "1 Year",
                "Female",
                "Yes",
                "Calm and affectionate Persian cat.",
                "hero.jpg",
                "Available"
            ),
            (
                "Snow",
                "Rabbit",
                "8 Months",
                "Male",
                "No",
                "Playful white rabbit.",
                "hero.jpg",
                "Available"
            )
        ]

        cursor.executemany("""
        INSERT INTO pets
        (
            name,
            breed,
            age,
            gender,
            vaccinated,
            description,
            image,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
# ADOPTER REGISTRATION
# ==========================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        role = request.form.get("role", "").strip()
        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # 1. Role validation
        if role not in ["Adopter", "Shelter"]:
            return render_template(
                "register.html",
                error="Please select whether you are registering as an Adopter or Shelter / Breeder.",
                form_data=request.form
            )

        # 2. Name validation
        if not fullname or len(fullname) < 2:
            return render_template(
                "register.html",
                error="Please enter a valid name.",
                form_data=request.form
            )

        if re.search(r'\d', fullname):
            return render_template(
                "register.html",
                error="Name cannot contain numbers. Please enter a valid name.",
                form_data=request.form
            )

        # 3. Email validation
        if not email or " " in email or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            return render_template(
                "register.html",
                error="Please enter a valid email address.",
                form_data=request.form
            )

        # Duplicate email check
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (email,))
        if cursor.fetchone():
            conn.close()
            return render_template(
                "register.html",
                error="An account with this email already exists.",
                form_data=request.form
            )

        # 4. Phone validation
        if not re.match(r'^[0-9]{10}$', phone):
            conn.close()
            return render_template(
                "register.html",
                error="Please enter a valid 10-digit phone number.",
                form_data=request.form
            )

        # 5. Address validation
        if not address:
            conn.close()
            return render_template(
                "register.html",
                error="Address cannot be empty.",
                form_data=request.form
            )

        # 6. Password validation
        if len(password) < 6:
            conn.close()
            return render_template(
                "register.html",
                error="Password must contain at least 6 characters.",
                form_data=request.form
            )

        # 7. Confirm password match
        if password != confirm_password:
            conn.close()
            return render_template(
                "register.html",
                error="Passwords do not match.",
                form_data=request.form
            )

        # Role & Status assignment
        if role == "Shelter":
            account_status = "Pending"
            success_msg = "Shelter registration submitted successfully! Your account is pending administrator approval before you can log in."
        else:
            account_status = "Active"
            success_msg = "Registration successful! You can now log in."

        cursor.execute("""
            INSERT INTO users(fullname, email, phone, address, password, role, account_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            fullname,
            email,
            phone,
            address,
            password,
            role,
            account_status
        ))

        conn.commit()
        conn.close()

        return render_template("login.html", success=success_msg)

    # Pre-select role if passed in query params (e.g. ?role=Shelter)
    preset_role = request.args.get('role', '')
    form_data = {'role': preset_role} if preset_role in ['Adopter', 'Shelter'] else None
    return render_template("register.html", form_data=form_data)


# ==========================
# SHELTER REGISTRATION
# ==========================

@app.route('/shelter-register', methods=['GET', 'POST'])
def shelter_register():
    return redirect(url_for('register', role='Shelter'))


# ==========================
# LOGIN
# ==========================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email:
            return render_template("login.html", error="Email cannot be empty")

        if not password:
            return render_template("login.html", error="Password cannot be empty")

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, fullname, email, phone, address, password, role, account_status
            FROM users
            WHERE email=? AND password=?
            """,
            (email, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            user_id = user[0]
            fullname = user[1]
            user_role = user[6]
            account_status = user[7]

            # 1. Admin login (by Admin role or designated admin emails)
            if user_role == "Admin" or email in ["admin@gmail.com", "admin@petadoption.com"]:
                session['user'] = fullname
                session['user_id'] = user_id
                session['role'] = "Admin"
                return redirect(url_for('admin'))

            # 2. Shelter login (must be approved by Admin)
            if user_role == "Shelter":
                if account_status == "Approved":
                    session['user'] = fullname
                    session['user_id'] = user_id
                    session['role'] = "Shelter"
                    return redirect(url_for('shelter_dashboard'))
                elif account_status == "Rejected":
                    return render_template(
                        "login.html",
                        error="Your shelter registration has been rejected by the administrator."
                    )
                elif account_status == "Deactivated":
                    return render_template(
                        "login.html",
                        error="Your shelter account has been deactivated by the administrator."
                    )
                else:
                    return render_template(
                        "login.html",
                        error="Your shelter registration is pending administrator approval."
                    )

            # 3. Transport Provider login
            if user_role in ["Transport", "Transport Provider"]:
                session['user'] = fullname
                session['user_id'] = user_id
                session['role'] = "Transport"
                return redirect(url_for('transport_dashboard'))

            # 4. Adopter login
            session['user'] = fullname
            session['user_id'] = user_id
            session['role'] = "Adopter"
            return redirect(url_for('pets'))

        else:
            return render_template("login.html", error="Invalid Email or Password")

    return render_template("login.html")


# ==========================
# LOGOUT
# ==========================

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# =========================================================
# ADMIN DASHBOARD & SHELTER MANAGEMENT (ADMIN ROLE ONLY)
# =========================================================

@app.route('/admin')
def admin():
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Admin":
        return "Access Denied!"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Query all registered shelters with their pet counts
    cursor.execute("""
        SELECT
            u.id,
            u.fullname,
            u.email,
            u.phone,
            u.address,
            u.account_status,
            (SELECT COUNT(*) FROM pets WHERE pets.shelter_id = u.id) AS pet_count
        FROM users u
        WHERE u.role = 'Shelter'
        ORDER BY u.id DESC
    """)
    shelters = cursor.fetchall()
    conn.close()

    total_shelters = len(shelters)
    pending_shelters = len([s for s in shelters if s[5] == "Pending"])
    approved_shelters = len([s for s in shelters if s[5] == "Approved"])
    rejected_shelters = len([s for s in shelters if s[5] in ["Rejected", "Deactivated"]])

    return render_template(
        "admin.html",
        shelters=shelters,
        total_shelters=total_shelters,
        pending_shelters=pending_shelters,
        approved_shelters=approved_shelters,
        rejected_shelters=rejected_shelters
    )


@app.route('/admin/shelter/<int:shelter_id>/<action>', methods=['GET', 'POST'])
def manage_shelter(shelter_id, action):
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Admin":
        return "Access Denied!"

    valid_actions = ["approve", "reject", "deactivate", "delete"]
    if action not in valid_actions:
        return "Invalid shelter action."

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if action == "approve":
        cursor.execute("""
            UPDATE users
            SET account_status = 'Approved'
            WHERE id = ? AND role = 'Shelter'
        """, (shelter_id,))
    elif action == "reject":
        cursor.execute("""
            UPDATE users
            SET account_status = 'Rejected'
            WHERE id = ? AND role = 'Shelter'
        """, (shelter_id,))
    elif action == "deactivate":
        cursor.execute("""
            UPDATE users
            SET account_status = 'Deactivated'
            WHERE id = ? AND role = 'Shelter'
        """, (shelter_id,))
    elif action == "delete":
        cursor.execute("""
            DELETE FROM users
            WHERE id = ? AND role = 'Shelter'
        """, (shelter_id,))

    conn.commit()
    conn.close()

    return redirect(url_for('admin'))


@app.route('/admin/shelter/<int:shelter_id>/edit', methods=['POST'])
def admin_edit_shelter(shelter_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Admin":
        return "Access Denied!"

    fullname = request.form.get("fullname", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    account_status = request.form.get("account_status", "Approved").strip()

    if not fullname or not email:
        return "Shelter name and email cannot be empty"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET fullname = ?, email = ?, phone = ?, address = ?, account_status = ?
        WHERE id = ? AND role = 'Shelter'
    """, (fullname, email, phone, address, account_status, shelter_id))

    conn.commit()
    conn.close()

    return redirect(url_for('admin'))


# Legacy pet endpoints redirected to appropriate shelter views
@app.route('/add-pet', methods=['GET', 'POST'])
def add_pet():
    if session.get('role') == "Shelter":
        return redirect(url_for('shelter_add_pet'))
    if session.get('role') == "Admin":
        return redirect(url_for('admin'))
    return redirect(url_for('login'))


@app.route('/edit-pet/<int:pet_id>', methods=['GET', 'POST'])
def edit_pet(pet_id):
    if session.get('role') == "Shelter":
        return redirect(url_for('shelter_edit_pet', pet_id=pet_id))
    if session.get('role') == "Admin":
        return redirect(url_for('admin'))
    return redirect(url_for('login'))


# =========================================================
# SHELTER DASHBOARD & PET MANAGEMENT (SHELTER ROLE ONLY)
# =========================================================

@app.route('/shelter-dashboard')
def shelter_dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Shelter":
        return "Access Denied!"

    shelter_id = session['user_id']

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Total pets belonging to this shelter
    cursor.execute("""
        SELECT COUNT(*)
        FROM pets
        WHERE shelter_id = ?
    """, (shelter_id,))
    total_pets = cursor.fetchone()[0]

    # Available pets
    cursor.execute("""
        SELECT COUNT(*)
        FROM pets
        WHERE shelter_id = ?
        AND status = 'Available'
    """, (shelter_id,))
    available_pets = cursor.fetchone()[0]

    # Adopted pets
    cursor.execute("""
        SELECT COUNT(*)
        FROM pets
        WHERE shelter_id = ?
        AND status = 'Adopted'
    """, (shelter_id,))
    adopted_pets = cursor.fetchone()[0]

    # Adoption requests for this shelter's pets
    cursor.execute("""
        SELECT COUNT(*)
        FROM adoptions
        JOIN pets ON adoptions.pet_id = pets.id
        WHERE pets.shelter_id = ?
    """, (shelter_id,))
    total_requests = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "shelter_dashboard.html",
        total_pets=total_pets,
        available_pets=available_pets,
        adopted_pets=adopted_pets,
        total_requests=total_requests
    )


@app.route('/shelter-pets')
def shelter_pets():
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Shelter":
        return "Access Denied!"

    shelter_id = session['user_id']

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM pets
        WHERE shelter_id = ?
        ORDER BY id DESC
    """, (shelter_id,))
    pets = cursor.fetchall()

    conn.close()

    return render_template("shelter_pets.html", pets=pets)


@app.route('/shelter-add-pet', methods=['GET', 'POST'])
def shelter_add_pet():
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Shelter":
        return "Access Denied!"

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        breed = request.form.get('breed', '').strip()
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()
        vaccinated = request.form.get('vaccinated', '').strip()
        description = request.form.get('description', '').strip()

        image_file = request.files.get('image')
        image_name = "hero.jpg"

        cropped_image = request.form.get('cropped_image', '').strip()
        saved_crop = save_cropped_image(cropped_image)

        if saved_crop:
            image_name = saved_crop
        elif image_file and image_file.filename:
            if not allowed_file(image_file.filename):
                return "Invalid image format. Use JPG, JPEG, PNG, GIF or WEBP."

            image_name = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO pets
            (
                name,
                breed,
                age,
                gender,
                vaccinated,
                description,
                image,
                status,
                shelter_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            breed,
            age,
            gender,
            vaccinated,
            description,
            image_name,
            "Available",
            session['user_id']
        ))

        conn.commit()
        conn.close()

        return redirect(url_for('shelter_pets'))

    return render_template("shelter_add_pet.html")


@app.route('/shelter-edit-pet/<int:pet_id>', methods=['GET', 'POST'])
def shelter_edit_pet(pet_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Shelter":
        return "Access Denied!"

    shelter_id = session['user_id']

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM pets
        WHERE id = ?
        AND shelter_id = ?
    """, (pet_id, shelter_id))
    pet = cursor.fetchone()

    if not pet:
        conn.close()
        return "Pet not found or you do not have permission to edit this pet."

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        breed = request.form.get('breed', '').strip()
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()
        vaccinated = request.form.get('vaccinated', '').strip()
        description = request.form.get('description', '').strip()
        status = request.form.get('status', 'Available').strip()

        image_name = pet[7]
        image_file = request.files.get('image')
        cropped_image = request.form.get('cropped_image', '').strip()
        saved_crop = save_cropped_image(cropped_image)

        if saved_crop:
            image_name = saved_crop
        elif image_file and image_file.filename:
            if not allowed_file(image_file.filename):
                conn.close()
                return "Invalid image format."

            image_name = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))

        cursor.execute("""
            UPDATE pets
            SET
                name = ?,
                breed = ?,
                age = ?,
                gender = ?,
                vaccinated = ?,
                description = ?,
                image = ?,
                status = ?
            WHERE id = ?
            AND shelter_id = ?
        """, (
            name,
            breed,
            age,
            gender,
            vaccinated,
            description,
            image_name,
            status,
            pet_id,
            shelter_id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for('shelter_pets'))

    conn.close()
    return render_template("shelter_edit_pet.html", pet=pet)


@app.route('/shelter-delete-pet/<int:pet_id>', methods=['GET', 'POST'])
def shelter_delete_pet(pet_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Shelter":
        return "Access Denied!"

    shelter_id = session['user_id']

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM pets
        WHERE id = ? AND shelter_id = ?
    """, (pet_id, shelter_id))

    conn.commit()
    conn.close()

    return redirect(url_for('shelter_pets'))


# =========================================================
# SHELTER ADOPTION REQUEST MANAGEMENT
# =========================================================

@app.route('/shelter-requests')
def shelter_requests():
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Shelter":
        return "Access Denied!"

    shelter_id = session['user_id']

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            adoptions.id,
            pets.name,
            pets.breed,
            adoptions.adopter_name,
            adoptions.phone,
            adoptions.address,
            adoptions.payment_method,
            adoptions.payment_status,
            adoptions.request_status,
            adoptions.transport_method,
            adoptions.transport_date,
            adoptions.transport_time,
            adoptions.transport_status,
            adoptions.refund_status
        FROM adoptions
        JOIN pets ON adoptions.pet_id = pets.id
        WHERE pets.shelter_id = ?
        ORDER BY adoptions.id DESC
    """, (shelter_id,))

    requests = cursor.fetchall()

    # Query shelter info for pickup details
    cursor.execute("SELECT fullname, phone, address FROM users WHERE id = ?", (shelter_id,))
    shelter_info = cursor.fetchone()
    conn.close()

    today_str = datetime.date.today().isoformat()

    return render_template(
        "shelter_requests.html",
        requests=requests,
        shelter_info=shelter_info,
        today=today_str
    )


@app.route('/approve/<int:request_id>', methods=['GET', 'POST'])
def approve(request_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Shelter":
        return "Access Denied!"

    shelter_id = session['user_id']

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Ensure this request belongs to a pet managed by this shelter
    cursor.execute("""
        SELECT adoptions.pet_id, adoptions.transport_method
        FROM adoptions
        JOIN pets ON adoptions.pet_id = pets.id
        WHERE adoptions.id = ? AND pets.shelter_id = ?
    """, (request_id, shelter_id))

    result = cursor.fetchone()

    if not result:
        conn.close()
        return "Adoption request not found or you do not have permission to manage it."

    pet_id, transport_method = result
    approx_time = get_approximate_time(transport_method)

    # Get delivery date chosen by the shelter
    delivery_date = request.form.get("delivery_date", "").strip() or request.args.get("delivery_date", "").strip()
    if not delivery_date:
        delivery_date = datetime.date.today().isoformat()

    cursor.execute("""
        UPDATE adoptions
        SET request_status = 'Approved',
            transport_status = 'Scheduled',
            transport_time = ?,
            transport_date = ?
        WHERE id = ?
    """, (approx_time, delivery_date, request_id))

    cursor.execute("""
        UPDATE pets
        SET status = 'Adopted'
        WHERE id = ? AND shelter_id = ?
    """, (pet_id, shelter_id))

    conn.commit()
    conn.close()

    return redirect(url_for('shelter_requests'))


@app.route('/shelter-set-delivery-date/<int:request_id>', methods=['POST'])
def shelter_set_delivery_date(request_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Shelter":
        return "Access Denied!"

    shelter_id = session['user_id']
    delivery_date = request.form.get("delivery_date", "").strip()

    if not delivery_date:
        return "Please select a valid delivery date."

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Verify request belongs to shelter
    cursor.execute("""
        SELECT adoptions.id
        FROM adoptions
        JOIN pets ON adoptions.pet_id = pets.id
        WHERE adoptions.id = ? AND pets.shelter_id = ?
    """, (request_id, shelter_id))

    if not cursor.fetchone():
        conn.close()
        return "Adoption request not found or unauthorized."

    cursor.execute("""
        UPDATE adoptions
        SET transport_date = ?
        WHERE id = ?
    """, (delivery_date, request_id))

    conn.commit()
    conn.close()

    return redirect(url_for('shelter_requests'))


@app.route('/reject/<int:request_id>', methods=['GET', 'POST'])
def reject(request_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Shelter":
        return "Access Denied!"

    shelter_id = session['user_id']

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT adoptions.pet_id, adoptions.payment_status
        FROM adoptions
        JOIN pets ON adoptions.pet_id = pets.id
        WHERE adoptions.id = ? AND pets.shelter_id = ?
    """, (request_id, shelter_id))

    result = cursor.fetchone()

    if not result:
        conn.close()
        return "Adoption request not found or you do not have permission to manage it."

    pet_id, payment_status = result

    cursor.execute("""
        UPDATE adoptions
        SET request_status = 'Rejected',
            refund_status = ?
        WHERE id = ?
    """, (
        'Refund Pending' if payment_status == 'Paid' else 'Not Applicable',
        request_id
    ))

    cursor.execute("""
        UPDATE pets
        SET status = 'Available'
        WHERE id = ? AND shelter_id = ?
    """, (pet_id, shelter_id))

    conn.commit()
    conn.close()

    return redirect(url_for('shelter_requests'))


# =========================================================
# SHELTER TRANSPORT SCHEDULING (SHELTER ROLE ONLY)
# =========================================================

@app.route('/shelter-schedule-transport/<int:request_id>', methods=['GET', 'POST'])
def shelter_schedule_transport(request_id):
    return redirect(url_for('shelter_requests'))


def _old_shelter_schedule_transport_disabled(request_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Shelter":
        return "Access Denied! Only shelters can schedule transport."

    shelter_id = session['user_id']

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Ensure this request belongs to a pet managed by this shelter
    cursor.execute("""
        SELECT
            adoptions.id,
            pets.name,
            pets.breed,
            adoptions.adopter_name,
            adoptions.phone,
            adoptions.address,
            adoptions.request_status,
            adoptions.transport_method,
            adoptions.transport_date,
            adoptions.transport_time,
            adoptions.transport_status
        FROM adoptions
        JOIN pets ON adoptions.pet_id = pets.id
        WHERE adoptions.id = ? AND pets.shelter_id = ?
    """, (request_id, shelter_id))

    adoption = cursor.fetchone()

    if not adoption:
        conn.close()
        return "Adoption request not found or you do not have permission to schedule transport."

    if adoption[6] != "Approved":
        conn.close()
        return "Transport can only be scheduled after approving the adoption request."

    # Fetch shelter address for pickup reference
    cursor.execute("SELECT fullname, phone, address FROM users WHERE id = ?", (shelter_id,))
    shelter_info = cursor.fetchone()

    if request.method == "POST":
        transport_method = request.form.get("transport_method", "Home Delivery").strip()
        transport_date = request.form.get("transport_date", "").strip()
        transport_time = request.form.get("transport_time", "").strip()

        if not transport_date:
            conn.close()
            return "Please select a transport date."

        if not transport_time:
            conn.close()
            return "Please select a transport time."

        cursor.execute("""
            UPDATE adoptions
            SET
                transport_method = ?,
                transport_date = ?,
                transport_time = ?,
                transport_status = 'Scheduled'
            WHERE id = ?
        """, (
            transport_method,
            transport_date,
            transport_time,
            request_id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for('shelter_requests'))

    conn.close()
    today_str = datetime.date.today().isoformat()
    return render_template(
        "shelter_schedule_transport.html",
        adoption=adoption,
        shelter_info=shelter_info,
        today=today_str
    )


# =========================================================
# ADOPTER / USER WORKFLOWS
# =========================================================

@app.route('/pets')
def pets():
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') == "Shelter":
        return redirect(url_for('shelter_dashboard'))

    if session.get('role') == "Admin":
        return redirect(url_for('admin'))

    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip().lower()

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    query = """
        SELECT *
        FROM pets
        WHERE LOWER(TRIM(status)) = 'available'
    """
    params = []

    if search:
        query += """
            AND (
                LOWER(name) LIKE ?
                OR LOWER(breed) LIKE ?
            )
        """
        search_value = "%" + search.lower() + "%"
        params.append(search_value)
        params.append(search_value)

    if category == "dog":
        query += """
            AND (
                LOWER(breed) LIKE '%labrador%'
                OR LOWER(breed) LIKE '%dog%'
                OR LOWER(breed) LIKE '%retriever%'
                OR LOWER(breed) LIKE '%beagle%'
                OR LOWER(breed) LIKE '%german shepherd%'
                OR LOWER(breed) LIKE '%poodle%'
                OR LOWER(breed) LIKE '%husky%'
            )
        """
    elif category == "cat":
        query += """
            AND (
                LOWER(breed) LIKE '%cat%'
                OR LOWER(breed) LIKE '%persian%'
                OR LOWER(breed) LIKE '%siamese%'
                OR LOWER(breed) LIKE '%maine coon%'
            )
        """
    elif category == "rabbit":
        query += """
            AND (
                LOWER(breed) LIKE '%rabbit%'
            )
        """

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    pets_list = cursor.fetchall()
    conn.close()

    return render_template(
        "pets.html",
        pets=pets_list,
        search=search,
        category=category
    )


@app.route('/pet_details/<int:pet_id>')
def pet_details(pet_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') == "Shelter":
        return redirect(url_for('shelter_dashboard'))

    if session.get('role') == "Admin":
        return redirect(url_for('admin'))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM pets
        WHERE id = ?
    """, (pet_id,))
    pet = cursor.fetchone()
    conn.close()

    if not pet:
        return "Pet not found."

    return render_template("pet_details.html", pet=pet)


@app.route('/adoption/<int:pet_id>', methods=['GET', 'POST'])
def adoption(pet_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') == "Shelter":
        return redirect(url_for('shelter_dashboard'))

    if session.get('role') == "Admin":
        return redirect(url_for('admin'))

    if request.method == "POST":
        adopter_name = request.form.get("adopter_name", "").strip() or session.get('user', '')
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        transport_method = request.form.get("transport_method", "Home Delivery").strip()
        if transport_method not in ["Home Delivery", "Shelter Pickup"]:
            transport_method = "Home Delivery"
        approx_time = get_approximate_time(transport_method)

        cursor.execute("""
        INSERT INTO adoptions
        (
            pet_id,
            adopter_name,
            phone,
            address,
            payment_status,
            transport_method,
            request_status,
            transport_time,
            transport_status,
            adopter_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pet_id,
            adopter_name,
            phone,
            address,
            "Pending",
            transport_method,
            "Pending",
            approx_time,
            "Scheduled",
            session.get('user_id')
        ))

        conn.commit()
        conn.close()

        # Redirect to My Requests so adopter can view pending status
        return redirect(url_for("my_requests"))

    return render_template("adoption.html", pet_id=pet_id)


@app.route('/my-requests')
def my_requests():
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Adopter":
        if session.get('role') == "Shelter":
            return redirect(url_for('shelter_dashboard'))
        if session.get('role') == "Admin":
            return redirect(url_for('admin'))
        return redirect(url_for('pets'))

    adopter_name = session['user']

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            adoptions.id,
            pets.id,
            pets.name,
            pets.breed,
            adoptions.request_status,
            adoptions.transport_method,
            adoptions.adopter_name,
            adoptions.payment_method,
            adoptions.payment_status,
            adoptions.refund_status,
            adoptions.transport_date,
            adoptions.transport_time,
            adoptions.transport_status
        FROM adoptions
        JOIN pets ON adoptions.pet_id = pets.id
        WHERE adoptions.adopter_name = ?
        ORDER BY adoptions.id DESC
    """, (adopter_name,))

    requests = cursor.fetchall()
    conn.close()

    return render_template("my_requests.html", requests=requests)


@app.route('/payment/<int:pet_id>', methods=['GET', 'POST'])
def payment(pet_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Adopter":
        return "Access Denied!"

    adopter_name = session['user']

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, request_status
        FROM adoptions
        WHERE pet_id = ?
        AND adopter_name = ?
        ORDER BY id DESC
        LIMIT 1
    """, (pet_id, adopter_name))

    adoption_record = cursor.fetchone()

    if not adoption_record:
        conn.close()
        return "Adoption request not found!"

    request_id = adoption_record[0]
    request_status = adoption_record[1]

    # Payment is strictly allowed only after shelter approval
    if request_status != "Approved":
        conn.close()
        return "Payment is available only after the shelter approves your request."

    if request.method == "POST":
        payment_method = request.form.get("payment_method")

        if payment_method not in ["Online", "COD"]:
            conn.close()
            return "Please select a valid payment method."

        payment_status = "Paid" if payment_method == "Online" else "COD"
        refund_status = "Not Applicable"

        cursor.execute("""
            UPDATE adoptions
            SET
                payment_method = ?,
                payment_status = ?,
                refund_status = ?
            WHERE id = ?
        """, (
            payment_method,
            payment_status,
            refund_status,
            request_id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("my_requests"))

    conn.close()

    return render_template(
        "payment.html",
        pet_id=pet_id,
        request_id=request_id
    )


@app.route('/transport/<int:pet_id>', methods=['GET', 'POST'])
def transport(pet_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Adopter":
        if session.get('role') == "Shelter":
            return redirect(url_for('shelter_requests'))
        if session.get('role') in ["Transport", "Transport Provider"]:
            return redirect(url_for('transport_dashboard'))
        return redirect(url_for('home'))

    adopter_name = session['user']

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            adoptions.id,
            pets.name,
            pets.breed,
            adoptions.transport_method,
            adoptions.transport_time,
            adoptions.transport_status,
            adoptions.request_status
        FROM adoptions
        JOIN pets ON adoptions.pet_id = pets.id
        WHERE adoptions.pet_id = ? AND adoptions.adopter_name = ?
        ORDER BY adoptions.id DESC
        LIMIT 1
    """, (pet_id, adopter_name))

    adoption_record = cursor.fetchone()

    if not adoption_record:
        conn.close()
        return redirect(url_for('my_requests'))

    request_id = adoption_record[0]

    if request.method == "POST":
        transport_method = request.form.get("transport_method", "Home Delivery").strip()
        if transport_method not in ["Home Delivery", "Shelter Pickup"]:
            transport_method = "Home Delivery"

        approx_time = get_approximate_time(transport_method)

        cursor.execute("""
            UPDATE adoptions
            SET
                transport_method = ?,
                transport_time = ?
            WHERE id = ?
        """, (
            transport_method,
            approx_time,
            request_id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("my_requests"))

    conn.close()

    return render_template(
        "transport.html",
        pet_id=pet_id,
        adoption=adoption_record
    )


@app.route('/success')
def success():
    return render_template("success.html")


# =========================================================
# TRANSPORT PROVIDER DASHBOARD & DELIVERY MANAGEMENT
# =========================================================

@app.route('/transport-dashboard')
def transport_dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') not in ["Transport", "Transport Provider"]:
        return "Access Denied! Transport Provider role required."

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Query all adoptions scheduled for transport
    cursor.execute("""
        SELECT
            adoptions.id,
            pets.name,
            pets.breed,
            pets.image,
            adoptions.adopter_name,
            adoptions.phone,
            adoptions.address,
            shelters.fullname AS shelter_name,
            shelters.phone AS shelter_phone,
            shelters.address AS shelter_address,
            adoptions.transport_method,
            adoptions.transport_date,
            adoptions.transport_time,
            adoptions.transport_status,
            adoptions.request_status
        FROM adoptions
        JOIN pets ON adoptions.pet_id = pets.id
        LEFT JOIN users shelters ON pets.shelter_id = shelters.id
        WHERE adoptions.request_status = 'Approved' AND adoptions.transport_status IN ('Scheduled', 'Pickup', 'In Transit', 'Delivered')
        ORDER BY adoptions.id DESC
    """)

    deliveries = cursor.fetchall()
    conn.close()

    total_deliveries = len(deliveries)
    scheduled_count = len([d for d in deliveries if d[13] == "Scheduled"])
    pickup_count = len([d for d in deliveries if d[13] == "Pickup"])
    transit_count = len([d for d in deliveries if d[13] == "In Transit"])
    delivered_count = len([d for d in deliveries if d[13] == "Delivered"])

    return render_template(
        "transport_dashboard.html",
        deliveries=deliveries,
        total_deliveries=total_deliveries,
        scheduled_count=scheduled_count,
        pickup_count=pickup_count,
        transit_count=transit_count,
        delivered_count=delivered_count
    )


@app.route('/transport-update-status/<int:adoption_id>', methods=['POST'])
def transport_update_status(adoption_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') not in ["Transport", "Transport Provider"]:
        return "Access Denied! Transport Provider role required."

    new_status = request.form.get("transport_status", "").strip()

    valid_statuses = ["Scheduled", "Pickup", "In Transit", "Delivered"]
    if new_status not in valid_statuses:
        return "Invalid status transition"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE adoptions
        SET transport_status = ?
        WHERE id = ?
    """, (new_status, adoption_id))

    conn.commit()
    conn.close()

    return redirect(url_for('transport_dashboard'))


# ==========================
# INFORMATIONAL & MESSAGES
# ==========================

@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        # 1. Name validation
        if not name or len(name) < 2:
            return render_template("contact.html", error="Please enter a valid name.", form_data=request.form)

        if re.search(r'\d', name):
            return render_template("contact.html", error="Name cannot contain numbers. Please enter a valid name.", form_data=request.form)

        # 2. Email validation
        if not email or " " in email or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            return render_template("contact.html", error="Please enter a valid email address.", form_data=request.form)

        # 3. Subject validation
        if not subject or len(subject) < 3:
            return render_template("contact.html", error="Please enter a subject (at least 3 characters).", form_data=request.form)

        # 4. Message validation
        if not message or len(message) < 10:
            return render_template("contact.html", error="Please enter a message (at least 10 characters).", form_data=request.form)

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO messages
            (
                user_id,
                name,
                email,
                subject,
                message,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            session.get('user_id'),
            name,
            email,
            subject,
            message,
            "Unread"
        ))

        conn.commit()
        conn.close()

        return render_template(
            "contact.html",
            success="Your message has been sent successfully!"
        )

    return render_template("contact.html")


@app.route('/my-messages')
def my_messages():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_id = session.get('user_id')

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            email,
            subject,
            message,
            status,
            reply,
            created_at
        FROM messages
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))
    user_messages = cursor.fetchall()
    conn.close()

    return render_template("my_messages.html", messages=user_messages)


@app.route('/messages')
def messages():
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'Admin':
        return "Access Denied!"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM messages
        ORDER BY id DESC
    """)
    all_messages = cursor.fetchall()
    conn.close()

    return render_template("messages.html", messages=all_messages)


@app.route('/reply-message/<int:message_id>', methods=['POST'])
def reply_message(message_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'Admin':
        return "Access Denied!"

    reply = request.form.get('reply', '').strip()

    if not reply:
        return "Reply cannot be empty"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE messages
        SET reply = ?,
            status = 'Read'
        WHERE id = ?
    """, (reply, message_id))

    conn.commit()
    conn.close()

    return redirect(url_for('messages'))


@app.route('/check-adoptions')
def check_adoptions():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(adoptions)")
    columns = cursor.fetchall()
    conn.close()

    return "<br>".join(str(column) for column in columns)


# ==========================
# MAIN ENTRY POINT
# ==========================

if __name__ == "__main__":
    create_table()
    app.run(debug=True)
