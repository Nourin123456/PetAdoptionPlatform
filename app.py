import sqlite3
import datetime
import re
import os
import base64
import uuid

from flask import Flask, render_template, request, redirect, url_for, session, flash
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


# ==========================
# INPUT VALIDATION HELPERS
# ==========================

def validate_fullname(name, allow_digits=True):
    if not name or not isinstance(name, str):
        return False, "Full Name cannot be empty."
    name = name.strip()
    if len(name) < 2:
        return False, "Full Name must contain at least 2 characters."
    if len(name) > 60:
        return False, "Full Name cannot exceed 60 characters."
    # Reject purely numeric or symbol-only names; require at least one alphabetic character
    if not any(c.isalpha() for c in name):
        return False, "Name must contain letters and cannot be purely numeric or symbols."
    pattern = r"^[A-Za-z0-9\s.'&,\(\)-]+$" if allow_digits else r"^[A-Za-z\s.'-]+$"
    if not re.match(pattern, name):
        return False, "Full Name can only contain letters, spaces, dots, hyphens, and apostrophes."
    return True, name


def validate_email(email):
    if not email or not isinstance(email, str):
        return False, "Email cannot be empty."
    email = email.strip()
    if len(email) < 5 or len(email) > 100:
        return False, "Email must be between 5 and 100 characters."
    if " " in email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return False, "Please enter a valid email address."
    return True, email.lower()


def validate_phone(phone):
    if not phone or not isinstance(phone, str):
        return False, "Phone number cannot be empty."
    phone = phone.strip()
    if phone.startswith("+91"):
        phone = phone[3:].strip()
    elif phone.startswith("0") and len(phone) == 11:
        phone = phone[1:].strip()
    if not re.match(r"^[0-9]{10}$", phone):
        return False, "Phone number must be exactly 10 digits."
    return True, phone


def validate_address(address):
    if not address or not isinstance(address, str):
        return False, "Address cannot be empty."
    address = address.strip()
    if len(address) < 5:
        return False, "Address must be at least 5 characters long."
    if len(address) > 255:
        return False, "Address cannot exceed 255 characters."
    return True, address


def validate_subject(subject):
    if not subject or not isinstance(subject, str):
        return False, "Subject cannot be empty."
    subject = subject.strip()
    if len(subject) < 3:
        return False, "Subject must contain at least 3 characters."
    if len(subject) > 120:
        return False, "Subject cannot exceed 120 characters."
    return True, subject


def validate_message(message):
    if not message or not isinstance(message, str):
        return False, "Message cannot be empty."
    message = message.strip()
    if len(message) < 10:
        return False, "Message must contain at least 10 characters."
    if len(message) > 2000:
        return False, "Message cannot exceed 2000 characters."
    return True, message


def parse_pet_age(age_str):
    """
    Parses an age string (e.g. '2 Years', '6 Months', '1 Year', '1', '3 years')
    into (number: int or None, unit: str or None).
    Unit is normalized to 'Months' or 'Years' for dropdown pre-selection.
    """
    if not age_str or not isinstance(age_str, str):
        return None, None
    age_str = age_str.strip()
    m = re.match(r"^(\d+)(?:\s*([a-zA-Z]+))?$", age_str)
    if not m:
        return None, None
    try:
        num = int(m.group(1))
    except (ValueError, TypeError):
        return None, None
    if num < 1 or num > 30:
        return None, None
    unit_raw = m.group(2)
    if not unit_raw:
        return None, None
    unit_lower = unit_raw.lower()
    if "month" in unit_lower:
        return num, "Months"
    elif "year" in unit_lower:
        return num, "Years"
    return None, None


def validate_pet_age(age_val, unit_val=None):
    """
    Validates pet age number and unit.
    Accepts:
      - validate_pet_age('2 Years')
      - validate_pet_age('2', 'Years') or validate_pet_age(2, 'Years')
    Returns: (is_valid: bool, result_or_error_message: str)
    If valid, returns (True, normalized_age_str) e.g. (True, '2 Years')
    """
    if unit_val is None:
        if not age_val or not isinstance(age_val, str) or not age_val.strip():
            return False, "Pet age is required."
        parsed_num, parsed_unit = parse_pet_age(age_val)
        if parsed_num is None or parsed_unit is None:
            return False, "Age must be between 1 and 30 with unit Months or Years."
        num, unit = parsed_num, parsed_unit
    else:
        if age_val is None or unit_val is None or str(age_val).strip() == "" or str(unit_val).strip() == "":
            return False, "Please select both an age number and a unit (Months or Years)."
        try:
            num = int(str(age_val).strip())
        except (ValueError, TypeError):
            return False, "Age number must be a valid number between 1 and 30."
        if num < 1 or num > 30:
            return False, "Age number must be between 1 and 30."
        unit_clean = str(unit_val).strip().capitalize()
        if unit_clean in ["Month", "Months"]:
            unit = "Months"
        elif unit_clean in ["Year", "Years"]:
            unit = "Years"
        else:
            return False, "Age unit must be either Months or Years."

    if num == 1:
        formatted = f"1 {'Month' if unit == 'Months' else 'Year'}"
    else:
        formatted = f"{num} {unit}"
    return True, formatted


def validate_pet_fields(name, breed, age, gender, vaccinated, description):
    if not name or len(name.strip()) < 2 or len(name.strip()) > 50:
        return False, "Pet name must be between 2 and 50 characters."
    if not breed or len(breed.strip()) < 2 or len(breed.strip()) > 50:
        return False, "Breed must be between 2 and 50 characters."
    valid_age, age_res = validate_pet_age(age)
    if not valid_age:
        return False, age_res
    if gender not in ["Male", "Female"]:
        return False, "Please select a valid gender (Male or Female)."
    if vaccinated not in ["Yes", "No"]:
        return False, "Please specify vaccination status (Yes or No)."
    if not description or len(description.strip()) < 5 or len(description.strip()) > 1000:
        return False, "Description must be between 5 and 1000 characters."
    return True, "Valid"



def validate_upi_id(upi_id):
    if not upi_id or not isinstance(upi_id, str):
        return False, "UPI ID cannot be empty."
    upi_id = upi_id.strip()
    if len(upi_id) < 4 or len(upi_id) > 60:
        return False, "UPI ID must be between 4 and 60 characters."
    pattern = r"^[a-zA-Z0-9.\-_]{2,50}@[a-zA-Z]{2,30}$"
    if not re.match(pattern, upi_id):
        return False, "Invalid UPI ID format. Please enter a valid UPI ID (e.g. name@upi)."
    return True, upi_id


def get_approximate_time(method=None):
    return ""


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

    # Clean up duplicate / orphaned email accounts and ensure uniqueness
    cursor.execute("""
        DELETE FROM users
        WHERE id IN (
            SELECT u1.id FROM users u1
            JOIN users u2 ON LOWER(TRIM(u1.email)) = LOWER(TRIM(u2.email)) AND u1.id > u2.id
            WHERE u1.id NOT IN (SELECT DISTINCT shelter_id FROM pets WHERE shelter_id IS NOT NULL)
              AND u1.id NOT IN (SELECT DISTINCT adopter_id FROM adoptions WHERE adopter_id IS NOT NULL)
        )
    """)
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique ON users(LOWER(TRIM(email)))")

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
            ADD COLUMN transport_status TEXT DEFAULT 'Pending'
        """)

    if "adopter_id" not in adoption_columns:
        cursor.execute("""
            ALTER TABLE adoptions
            ADD COLUMN adopter_id INTEGER
        """)

    if "upi_id" not in adoption_columns:
        cursor.execute("""
            ALTER TABLE adoptions
            ADD COLUMN upi_id TEXT
        """)

    if "payment_date" not in adoption_columns:
        cursor.execute("""
            ALTER TABLE adoptions
            ADD COLUMN payment_date TEXT
        """)

    if "request_date" not in adoption_columns:
        cursor.execute("""
            ALTER TABLE adoptions
            ADD COLUMN request_date TEXT
        """)

    # Backfill request_date for existing adoptions if empty
    cursor.execute("""
        UPDATE adoptions
        SET request_date = date('now')
        WHERE request_date IS NULL OR request_date = ''
    """)

    # ==========================
    # CONVERSATIONS & MESSAGES TABLES
    # ==========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        adopter_id INTEGER NOT NULL,
        shelter_id INTEGER NOT NULL,
        pet_id INTEGER,
        created_at TEXT,
        updated_at TEXT,
        status TEXT DEFAULT 'Open'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER,
        sender_id INTEGER,
        sender_type TEXT,
        message TEXT,
        sent_at TEXT,
        is_read INTEGER DEFAULT 0,
        user_id INTEGER,
        name TEXT,
        email TEXT,
        subject TEXT,
        status TEXT DEFAULT 'Unread',
        reply TEXT,
        created_at TEXT,
        shelter_id INTEGER,
        pet_id INTEGER
    )
    """)

    # Ensure messages table has all columns
    cursor.execute("PRAGMA table_info(messages)")
    msg_columns = [column[1] for column in cursor.fetchall()]

    if "conversation_id" not in msg_columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN conversation_id INTEGER")
    if "sender_id" not in msg_columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN sender_id INTEGER")
    if "sender_type" not in msg_columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN sender_type TEXT")
    if "sent_at" not in msg_columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN sent_at TEXT")
    if "is_read" not in msg_columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN is_read INTEGER DEFAULT 0")
    if "shelter_id" not in msg_columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN shelter_id INTEGER")
    if "pet_id" not in msg_columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN pet_id INTEGER")
    if "reply" not in msg_columns:
        cursor.execute("ALTER TABLE messages ADD COLUMN reply TEXT")

    # Migrate any legacy messages without conversation_id
    cursor.execute("SELECT id, user_id, shelter_id, pet_id, message, reply, status, created_at FROM messages WHERE conversation_id IS NULL")
    legacy_msgs = cursor.fetchall()
    for row in legacy_msgs:
        mid, u_id, s_id, p_id, msg_txt, reply_txt, st, cr_at = row
        if not u_id or not s_id:
            continue
        if p_id:
            cursor.execute("SELECT id FROM conversations WHERE adopter_id = ? AND shelter_id = ? AND pet_id = ?", (u_id, s_id, p_id))
        else:
            cursor.execute("SELECT id FROM conversations WHERE adopter_id = ? AND shelter_id = ?", (u_id, s_id))
        conv_row = cursor.fetchone()
        if conv_row:
            c_id = conv_row[0]
        else:
            ts = cr_at or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO conversations (adopter_id, shelter_id, pet_id, created_at, updated_at, status)
                VALUES (?, ?, ?, ?, ?, 'Open')
            """, (u_id, s_id, p_id, ts, ts))
            c_id = cursor.lastrowid

        cursor.execute("""
            UPDATE messages
            SET conversation_id = ?,
                sender_id = ?,
                sender_type = 'Adopter',
                sent_at = COALESCE(created_at, datetime('now')),
                is_read = CASE WHEN status = 'Read' THEN 1 ELSE 0 END
            WHERE id = ?
        """, (c_id, u_id, mid))

        if reply_txt and reply_txt.strip():
            cursor.execute("SELECT id FROM messages WHERE conversation_id = ? AND sender_type = 'Shelter' AND message = ?", (c_id, reply_txt.strip()))
            if not cursor.fetchone():
                ts = cr_at or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO messages (
                        conversation_id, sender_id, sender_type, message, sent_at, is_read,
                        user_id, shelter_id, pet_id, status, created_at
                    )
                    VALUES (?, ?, 'Shelter', ?, ?, 1, ?, ?, ?, 'Read', ?)
                """, (c_id, s_id, reply_txt.strip(), ts, u_id, s_id, p_id, ts))

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

    # Find default approved shelter for sample listings
    cursor.execute("SELECT id FROM users WHERE role = 'Shelter' AND account_status = 'Approved' ORDER BY id ASC LIMIT 1")
    default_shelter_row = cursor.fetchone()
    default_shelter_id = default_shelter_row[0] if default_shelter_row else None

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
                "Available",
                default_shelter_id
            ),
            (
                "Kitty",
                "Persian Cat",
                "1 Year",
                "Female",
                "Yes",
                "Calm and affectionate Persian cat.",
                "hero.jpg",
                "Available",
                default_shelter_id
            ),
            (
                "Snow",
                "Rabbit",
                "8 Months",
                "Male",
                "No",
                "Playful white rabbit.",
                "hero.jpg",
                "Available",
                default_shelter_id
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
            status,
            shelter_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, pets)
    # ==========================
    # DATA MIGRATION / SANITIZATION
    # ==========================
    # 1. Enforce fixed 500 adoption fee for all approved, paid, or COD adoptions
    cursor.execute("""
        UPDATE adoptions
        SET payment_amount = 500
        WHERE (request_status = 'Approved' OR payment_status IN ('Paid', 'COD'))
          AND (payment_amount IS NULL OR payment_amount = 0)
    """)

    # 2. Update legacy payment method 'Online' to 'UPI'
    cursor.execute("""
        UPDATE adoptions
        SET payment_method = 'UPI'
        WHERE payment_method = 'Online'
    """)

    # 3. Cleanse any legacy approximate duration strings from transport_time
    cursor.execute("""
        UPDATE adoptions
        SET transport_time = NULL
        WHERE transport_time LIKE '%approx%'
           OR transport_time LIKE '%hour%'
           OR transport_time LIKE '%minute%'
    """)

    # 4. Remove any legacy Transport Provider role users (responsibility moved to Shelter)
    cursor.execute("""
        DELETE FROM users
        WHERE role IN ('Transport', 'Transport Provider')
           OR email = 'transport@petadoption.com'
    """)

    # 5. Standardize legacy transport statuses
    cursor.execute("""
        UPDATE adoptions
        SET transport_status = 'Pending'
        WHERE transport_status IS NULL
           OR transport_status = ''
           OR transport_status = 'Not Scheduled'
    """)

    # 6. Ensure all pets and legacy messages are linked to a specific verified shelter
    if default_shelter_id:
        cursor.execute("UPDATE pets SET shelter_id = ? WHERE shelter_id IS NULL", (default_shelter_id,))
        # Link messages about a known pet to that pet's shelter
        cursor.execute("""
            UPDATE messages
            SET shelter_id = (SELECT shelter_id FROM pets WHERE pets.id = messages.pet_id)
            WHERE messages.pet_id IS NOT NULL AND messages.shelter_id IS NULL
        """)
        # Fallback any remaining orphan messages to the primary approved shelter
        cursor.execute("UPDATE messages SET shelter_id = ? WHERE shelter_id IS NULL", (default_shelter_id,))

    # 7. Normalize legacy pet ages to standard format (e.g. '1' -> '1 Year', '3 years' -> '3 Years')
    try:
        cursor.execute("SELECT id, age FROM pets WHERE age IS NOT NULL")
        existing_pets = cursor.fetchall()
        for p_id, p_age in existing_pets:
            if p_age is not None:
                p_age_str = str(p_age).strip()
                if p_age_str.isdigit():
                    num = int(p_age_str)
                    if 1 <= num <= 30:
                        normalized = "1 Year" if num == 1 else f"{num} Years"
                        cursor.execute("UPDATE pets SET age = ? WHERE id = ?", (normalized, p_id))
                else:
                    parsed_num, parsed_unit = parse_pet_age(p_age_str)
                    if parsed_num is not None and parsed_unit is not None:
                        if parsed_num == 1:
                            normalized = f"1 {'Month' if parsed_unit == 'Months' else 'Year'}"
                        else:
                            normalized = f"{parsed_num} {parsed_unit}"
                        if normalized != p_age_str:
                            cursor.execute("UPDATE pets SET age = ? WHERE id = ?", (normalized, p_id))
    except Exception as e:
        print(f"Error normalizing legacy pet ages: {e}")

    # 8. Clean up orphan adoption records without existing pet
    try:
        cursor.execute("DELETE FROM adoptions WHERE pet_id NOT IN (SELECT id FROM pets)")
    except Exception as e:
        print(f"Error cleaning orphan adoptions: {e}")

    conn.commit()
    conn.close()


# Ensure tables and migrations run on import/startup
create_table()


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
        valid, msg = validate_fullname(fullname)
        if not valid:
            return render_template(
                "register.html",
                error=msg,
                form_data=request.form
            )

        # 3. Email validation
        valid, msg = validate_email(email)
        if not valid:
            return render_template(
                "register.html",
                error=msg,
                form_data=request.form
            )
        email = msg

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
        valid, msg = validate_phone(phone)
        if not valid:
            conn.close()
            return render_template(
                "register.html",
                error=msg,
                form_data=request.form
            )

        # 5. Address validation
        valid, msg = validate_address(address)
        if not valid:
            conn.close()
            return render_template(
                "register.html",
                error=msg,
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

            # 3. Adopter login
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

    valid, msg = validate_fullname(fullname)
    if not valid:
        flash(f"Invalid Shelter Name: {msg}", "danger")
        return redirect(url_for('admin'))

    valid, msg = validate_email(email)
    if not valid:
        flash(f"Invalid Email: {msg}", "danger")
        return redirect(url_for('admin'))
    email = msg

    valid, msg = validate_phone(phone)
    if not valid:
        flash(f"Invalid Phone: {msg}", "danger")
        return redirect(url_for('admin'))

    valid, msg = validate_address(address)
    if not valid:
        flash(f"Invalid Address: {msg}", "danger")
        return redirect(url_for('admin'))

    if account_status not in ["Approved", "Pending", "Rejected", "Deactivated"]:
        account_status = "Approved"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Prevent duplicate email collision
    cursor.execute("SELECT id FROM users WHERE LOWER(TRIM(email)) = LOWER(?) AND id != ?", (email, shelter_id))
    if cursor.fetchone():
        conn.close()
        flash("This email address is already in use by another account.", "danger")
        return redirect(url_for('admin'))

    cursor.execute("""
        UPDATE users
        SET fullname = ?,
            email = ?,
            phone = ?,
            address = ?,
            account_status = ?
        WHERE id = ? AND role = 'Shelter'
    """, (
        fullname,
        email,
        phone,
        address,
        account_status,
        shelter_id
    ))

    # Synchronize shelter name across messages
    cursor.execute("UPDATE messages SET name = ? WHERE shelter_id = ? AND sender_type = 'Shelter'", (fullname, shelter_id))

    conn.commit()
    conn.close()

    flash("Shelter details updated successfully.", "success")
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
# CONVERSATION HELPER
# =========================================================

def get_or_create_conversation(cursor, adopter_id, shelter_id, pet_id=None):
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        pet_id = int(pet_id) if pet_id else None
    except (ValueError, TypeError):
        pet_id = None

    if pet_id:
        cursor.execute("""
            SELECT id FROM conversations
            WHERE adopter_id = ? AND shelter_id = ? AND pet_id = ?
            ORDER BY id DESC LIMIT 1
        """, (adopter_id, shelter_id, pet_id))
    else:
        cursor.execute("""
            SELECT id FROM conversations
            WHERE adopter_id = ? AND shelter_id = ? AND (pet_id IS NULL OR pet_id = '')
            ORDER BY id DESC LIMIT 1
        """, (adopter_id, shelter_id))
    row = cursor.fetchone()
    if row:
        conv_id = row[0]
        cursor.execute("UPDATE conversations SET updated_at = ?, status = 'Open' WHERE id = ?", (now_str, conv_id))
        return conv_id
    else:
        cursor.execute("""
            INSERT INTO conversations (adopter_id, shelter_id, pet_id, created_at, updated_at, status)
            VALUES (?, ?, ?, ?, ?, 'Open')
        """, (adopter_id, shelter_id, pet_id, now_str, now_str))
        return cursor.lastrowid


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

    # Pending adoption requests requiring shelter review
    cursor.execute("""
        SELECT
            adoptions.id,
            pets.name,
            pets.breed,
            adoptions.adopter_name,
            adoptions.phone,
            adoptions.address,
            adoptions.transport_method,
            adoptions.payment_status
        FROM adoptions
        JOIN pets ON adoptions.pet_id = pets.id
        WHERE pets.shelter_id = ? AND adoptions.request_status = 'Pending'
        ORDER BY adoptions.id ASC
    """, (shelter_id,))
    pending_requests = cursor.fetchall()
    pending_count = len(pending_requests)

    # Fetch shelter profile details
    cursor.execute("""
        SELECT id, fullname, email, phone, address, role, account_status
        FROM users
        WHERE id = ?
    """, (shelter_id,))
    shelter_profile = cursor.fetchone()

    # Query all approved adoption deliveries managed by this shelter
    cursor.execute("""
        SELECT
            adoptions.id,
            pets.name,
            pets.breed,
            pets.image,
            adoptions.adopter_name,
            adoptions.phone,
            adoptions.address,
            adoptions.transport_method,
            adoptions.transport_date,
            adoptions.transport_time,
            adoptions.transport_status,
            adoptions.payment_status,
            adoptions.payment_amount
        FROM adoptions
        JOIN pets ON adoptions.pet_id = pets.id
        WHERE pets.shelter_id = ? AND adoptions.request_status = 'Approved'
        ORDER BY adoptions.id ASC
    """, (shelter_id,))
    deliveries = cursor.fetchall()

    # Query all messages sent to this specific shelter
    cursor.execute("""
        SELECT
            m.id,
            m.user_id,
            m.name AS adopter_name,
            m.email AS adopter_email,
            m.subject,
            m.message,
            m.status,
            m.reply,
            m.created_at,
            m.pet_id,
            p.name AS pet_name,
            p.breed AS pet_breed,
            p.image AS pet_image,
            m.conversation_id
        FROM messages m
        LEFT JOIN pets p ON m.pet_id = p.id
        WHERE m.shelter_id = ?
        ORDER BY m.id DESC
    """, (shelter_id,))
    shelter_messages = cursor.fetchall()
    total_messages = len(shelter_messages)
    unread_messages_count = len([m for m in shelter_messages if m[6] == 'Unread'])
    replied_messages_count = len([m for m in shelter_messages if m[7]])

    # Query all conversations belonging to this shelter
    cursor.execute("""
        SELECT
            c.id,
            c.adopter_id,
            c.shelter_id,
            c.pet_id,
            c.created_at,
            c.updated_at,
            c.status,
            u.fullname AS adopter_name,
            u.email AS adopter_email,
            u.phone AS adopter_phone,
            p.name AS pet_name,
            p.breed AS pet_breed,
            p.image AS pet_image
        FROM conversations c
        LEFT JOIN users u ON c.adopter_id = u.id
        LEFT JOIN pets p ON c.pet_id = p.id
        WHERE c.shelter_id = ?
        ORDER BY c.updated_at DESC
    """, (shelter_id,))
    sh_conv_rows = cursor.fetchall()

    shelter_conversations = []
    for c_row in sh_conv_rows:
        cid = c_row[0]
        cursor.execute("""
            SELECT
                m.id,
                m.sender_id,
                m.sender_type,
                m.message,
                m.sent_at,
                m.is_read,
                COALESCE(u.fullname, m.name, m.sender_type) AS sender_name
            FROM messages m
            LEFT JOIN users u ON m.sender_id = u.id
            WHERE m.conversation_id = ?
            ORDER BY m.id ASC
        """, (cid,))
        c_msgs = cursor.fetchall()

        unread_for_shelter = len([m for m in c_msgs if m[2] == 'Adopter' and m[5] == 0])

        shelter_conversations.append({
            'id': c_row[0],
            'adopter_id': c_row[1],
            'shelter_id': c_row[2],
            'pet_id': c_row[3],
            'created_at': c_row[4],
            'updated_at': c_row[5],
            'status': c_row[6],
            'adopter_name': c_row[7] or 'Adopter',
            'adopter_email': c_row[8] or '',
            'adopter_phone': c_row[9] or '',
            'pet_name': c_row[10],
            'pet_breed': c_row[11],
            'pet_image': c_row[12],
            'messages': c_msgs,
            'unread_count': unread_for_shelter
        })

    conn.close()

    total_deliveries = len(deliveries)
    scheduled_count = len([d for d in deliveries if d[10] in ('Scheduled', 'Pickup', 'Picked Up')])
    in_transit_count = len([d for d in deliveries if d[10] in ('In Transit', 'Out for Delivery')])
    delivered_count = len([d for d in deliveries if d[10] in ('Delivered', 'Completed')])
    pending_transport_count = len([d for d in deliveries if d[10] in ('Pending', 'Transport Not Started', 'Not Scheduled', '')])

    today_str = datetime.date.today().isoformat()

    return render_template(
        "shelter_dashboard.html",
        total_pets=total_pets,
        available_pets=available_pets,
        adopted_pets=adopted_pets,
        total_requests=total_requests,
        pending_requests=pending_requests,
        pending_count=pending_count,
        shelter_profile=shelter_profile,
        deliveries=deliveries,
        total_deliveries=total_deliveries,
        scheduled_count=scheduled_count,
        in_transit_count=in_transit_count,
        delivered_count=delivered_count,
        pending_transport_count=pending_transport_count,
        shelter_messages=shelter_messages,
        shelter_conversations=shelter_conversations,
        total_messages=total_messages,
        unread_messages_count=unread_messages_count,
        replied_messages_count=replied_messages_count,
        today=today_str
    )


@app.route('/shelter-reply-message/<int:message_id>', methods=['POST'])
def shelter_reply_message(message_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'Shelter':
        flash("Access Denied: Only verified shelters can reply to adopter inquiries.", "danger")
        return redirect(url_for('login'))

    shelter_id = session.get('user_id')
    reply_text = request.form.get('reply', '').strip()

    if not reply_text or len(reply_text) < 2 or len(reply_text) > 2000:
        flash("Reply must be between 2 and 2000 characters.", "danger")
        return redirect(url_for('shelter_dashboard') + "#messages-section")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # STRICT SECURITY: Verify this message strictly belongs to THIS shelter
    cursor.execute("SELECT id, user_id, pet_id, conversation_id FROM messages WHERE id = ? AND shelter_id = ?", (message_id, shelter_id))
    msg = cursor.fetchone()
    if not msg:
        conn.close()
        flash("Access Denied: You do not have permission to access or reply to this message.", "danger")
        return redirect(url_for('shelter_dashboard'))

    m_id, u_id, p_id, conv_id = msg
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not conv_id:
        conv_id = get_or_create_conversation(cursor, u_id, shelter_id, p_id)
        cursor.execute("UPDATE messages SET conversation_id = ? WHERE id = ?", (conv_id, message_id))

    # 1. Update initial message row for backward-compatibility with tests
    cursor.execute("""
        UPDATE messages
        SET reply = ?,
            status = 'Read'
        WHERE id = ? AND shelter_id = ?
    """, (reply_text, message_id, shelter_id))

    # 2. Insert new message row into conversation for continuous chat
    cursor.execute("SELECT fullname FROM users WHERE id = ?", (shelter_id,))
    sh_u = cursor.fetchone()
    sh_name = sh_u[0] if sh_u and sh_u[0] else session.get('user', 'Shelter')

    cursor.execute("""
        INSERT INTO messages (
            conversation_id, sender_id, sender_type, message, sent_at, is_read,
            user_id, shelter_id, pet_id, status, created_at, name
        )
        VALUES (?, ?, 'Shelter', ?, ?, 0, ?, ?, ?, 'Read', ?, ?)
    """, (
        conv_id, shelter_id, reply_text, now_str,
        u_id, shelter_id, p_id, now_str, sh_name
    ))

    # Keep conversation open
    cursor.execute("UPDATE conversations SET updated_at = ?, status = 'Open' WHERE id = ?", (now_str, conv_id))

    conn.commit()
    conn.close()

    flash("Your reply has been sent directly to the adopter!", "success")
    return redirect(url_for('shelter_dashboard') + "#messages-section")


@app.route('/shelter-edit-profile', methods=['POST'])
def shelter_edit_profile():
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'Shelter':
        return "Access Denied!"

    shelter_id = session.get('user_id')
    fullname = request.form.get('fullname', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    address = request.form.get('address', '').strip()
    new_password = request.form.get('new_password', '').strip()

    valid, msg = validate_fullname(fullname, allow_digits=True)
    if not valid:
        flash(msg, "danger")
        return redirect(url_for('shelter_dashboard') + "#profile-section")

    valid, msg = validate_email(email)
    if not valid:
        flash(msg, "danger")
        return redirect(url_for('shelter_dashboard') + "#profile-section")
    email = msg

    valid, msg = validate_phone(phone)
    if not valid:
        flash(msg, "danger")
        return redirect(url_for('shelter_dashboard') + "#profile-section")
    phone = msg

    valid, msg = validate_address(address)
    if not valid:
        flash(msg, "danger")
        return redirect(url_for('shelter_dashboard') + "#profile-section")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Check for email collision with other users (case-insensitive)
    cursor.execute("SELECT id FROM users WHERE LOWER(TRIM(email)) = LOWER(?) AND id != ?", (email, shelter_id))
    if cursor.fetchone():
        conn.close()
        flash("This email address is already in use by another account.", "danger")
        return redirect(url_for('shelter_dashboard') + "#profile-section")

    if new_password:
        if len(new_password) < 6:
            conn.close()
            flash("New password must be at least 6 characters long.", "danger")
            return redirect(url_for('shelter_dashboard') + "#profile-section")
        cursor.execute("""
            UPDATE users
            SET fullname = ?, email = ?, phone = ?, address = ?, password = ?
            WHERE id = ? AND role = 'Shelter'
        """, (fullname, email, phone, address, new_password, shelter_id))
    else:
        cursor.execute("""
            UPDATE users
            SET fullname = ?, email = ?, phone = ?, address = ?
            WHERE id = ? AND role = 'Shelter'
        """, (fullname, email, phone, address, shelter_id))

    # Synchronize shelter name across messages table so past inquiries reflect the updated organization name
    cursor.execute("UPDATE messages SET name = ? WHERE shelter_id = ? AND sender_type = 'Shelter'", (fullname, shelter_id))

    conn.commit()
    conn.close()

    session['user'] = fullname
    flash("Shelter profile updated successfully!", "success")
    return redirect(url_for('shelter_dashboard') + "#profile-section")


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
        gender = request.form.get('gender', '').strip()
        vaccinated = request.form.get('vaccinated', '').strip()
        description = request.form.get('description', '').strip()

        # Handle age from dropdown selects or fallback direct field
        age_number = request.form.get('age_number')
        age_unit = request.form.get('age_unit')

        if age_number is not None or age_unit is not None:
            valid_age, age_res = validate_pet_age(age_number, age_unit)
            if not valid_age:
                return render_template("shelter_add_pet.html", error=age_res, form_data=request.form)
            age = age_res
        else:
            age = request.form.get('age', '').strip()
            valid_age, age_res = validate_pet_age(age)
            if not valid_age:
                return render_template("shelter_add_pet.html", error=age_res, form_data=request.form)
            age = age_res

        valid, msg = validate_pet_fields(name, breed, age, gender, vaccinated, description)
        if not valid:
            return render_template("shelter_add_pet.html", error=msg, form_data=request.form)

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

    selected_age_num, selected_age_unit = parse_pet_age(pet[3])

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        breed = request.form.get('breed', '').strip()
        gender = request.form.get('gender', '').strip()
        vaccinated = request.form.get('vaccinated', '').strip()
        description = request.form.get('description', '').strip()
        status = request.form.get('status', 'Available').strip()

        # Handle age from dropdown selects or fallback direct field
        age_number = request.form.get('age_number')
        age_unit = request.form.get('age_unit')

        if age_number is not None or age_unit is not None:
            valid_age, age_res = validate_pet_age(age_number, age_unit)
            if not valid_age:
                conn.close()
                return render_template("shelter_edit_pet.html", pet=pet, selected_age_num=selected_age_num, selected_age_unit=selected_age_unit, error=age_res, form_data=request.form)
            age = age_res
        else:
            age = request.form.get('age', '').strip()
            valid_age, age_res = validate_pet_age(age)
            if not valid_age:
                conn.close()
                return render_template("shelter_edit_pet.html", pet=pet, selected_age_num=selected_age_num, selected_age_unit=selected_age_unit, error=age_res, form_data=request.form)
            age = age_res

        valid, msg = validate_pet_fields(name, breed, age, gender, vaccinated, description)
        if not valid:
            conn.close()
            return render_template("shelter_edit_pet.html", pet=pet, selected_age_num=selected_age_num, selected_age_unit=selected_age_unit, error=msg, form_data=request.form)

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
    return render_template("shelter_edit_pet.html", pet=pet, selected_age_num=selected_age_num, selected_age_unit=selected_age_unit)


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
            adoptions.refund_status,
            COALESCE(adoptions.request_date, adoptions.payment_date, date('now')) AS request_date
        FROM adoptions
        JOIN pets ON adoptions.pet_id = pets.id
        WHERE pets.shelter_id = ?
        ORDER BY adoptions.id ASC
    """, (shelter_id,))

    requests = cursor.fetchall()

    # Query shelter info for pickup details
    cursor.execute("SELECT fullname, phone, address FROM users WHERE id = ?", (shelter_id,))
    shelter_info = cursor.fetchone()
    conn.close()

    today_str = datetime.date.today().isoformat()

    pending_count = sum(1 for r in requests if r[8] == 'Pending')
    approved_count = sum(1 for r in requests if r[8] == 'Approved')
    rejected_count = sum(1 for r in requests if r[8] == 'Rejected')

    return render_template(
        "shelter_requests.html",
        requests=requests,
        shelter_info=shelter_info,
        today=today_str,
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count
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

    # Get delivery date chosen by the shelter
    delivery_date = request.form.get("delivery_date", "").strip() or request.args.get("delivery_date", "").strip()
    if not delivery_date:
        delivery_date = datetime.date.today().isoformat()

    cursor.execute("""
        UPDATE adoptions
        SET request_status = 'Approved',
            payment_amount = 500,
            transport_status = 'Scheduled',
            transport_date = ?
        WHERE id = ?
    """, (delivery_date, request_id))

    cursor.execute("""
        UPDATE pets
        SET status = 'Adopted'
        WHERE id = ? AND shelter_id = ?
    """, (pet_id, shelter_id))

    conn.commit()
    conn.close()

    flash(f"Adoption request #{request_id} approved successfully! Delivery date: {delivery_date}.", "success")
    return redirect(url_for('shelter_requests'))


@app.route('/shelter-set-delivery-date/<int:request_id>', methods=['POST'])
def shelter_set_delivery_date(request_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Shelter":
        return "Access Denied!"

    shelter_id = session['user_id']
    delivery_date = request.form.get("delivery_date", "").strip()

    redirect_target = request.referrer or url_for('shelter_requests')
    target_url = url_for('shelter_dashboard') if 'shelter-dashboard' in redirect_target else url_for('shelter_requests')

    if not delivery_date:
        flash("Please select a valid delivery date.", "danger")
        return redirect(target_url)

    try:
        datetime.date.fromisoformat(delivery_date)
    except ValueError:
        flash("Invalid delivery date format.", "danger")
        return redirect(target_url)

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

    # Keep selected delivery method strictly unchanged; update only transport_date
    cursor.execute("""
        UPDATE adoptions
        SET transport_date = ?
        WHERE id = ?
    """, (delivery_date, request_id))

    conn.commit()
    conn.close()

    flash(f"Scheduled date for request #{request_id} updated to {delivery_date}.", "success")
    return redirect(target_url)


@app.route('/shelter-update-transport-status/<int:request_id>', methods=['POST'])
def shelter_update_transport_status(request_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Shelter":
        return "Access Denied!"

    shelter_id = session['user_id']
    new_status = request.form.get("transport_status", "").strip()
    valid_statuses = [
        "Pending",
        "Scheduled",
        "In Transit",
        "Delivered",
        "Transport Not Started",
        "Picked Up",
        "Pickup",
        "Out for Delivery",
        "Completed"
    ]

    redirect_target = request.referrer or url_for('shelter_requests')
    target_url = url_for('shelter_dashboard') if 'shelter-dashboard' in redirect_target else url_for('shelter_requests')

    if new_status not in valid_statuses:
        flash("Invalid transport status selected.", "danger")
        return redirect(target_url)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

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
        SET transport_status = ?
        WHERE id = ?
    """, (new_status, request_id))

    conn.commit()
    conn.close()

    flash(f"Transport status for request #{request_id} updated to '{new_status}'.", "success")
    return redirect(target_url)


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
        'Refund Pending' if payment_status in ['Paid', 'Successful'] else 'Not Applicable',
        request_id
    ))

    cursor.execute("""
        UPDATE pets
        SET status = 'Available'
        WHERE id = ? AND shelter_id = ?
    """, (pet_id, shelter_id))

    conn.commit()
    conn.close()

    flash(f"Adoption request #{request_id} has been rejected. Pet is now available.", "danger")
    return redirect(url_for('shelter_requests'))


# =========================================================
# SHELTER TRANSPORT SCHEDULING (SHELTER ROLE ONLY)
# =========================================================

@app.route('/shelter-schedule-transport/<int:request_id>', methods=['GET', 'POST'])
def shelter_schedule_transport(request_id):
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
        flash("Transport can only be scheduled after approving the adoption request.", "warning")
        return redirect(url_for('shelter_requests'))

    # Fetch shelter address for pickup reference
    cursor.execute("SELECT fullname, phone, address FROM users WHERE id = ?", (shelter_id,))
    shelter_info = cursor.fetchone()

    if request.method == "POST":
        transport_date = request.form.get("transport_date", "").strip()
        transport_time = request.form.get("transport_time", "").strip()
        transport_status = request.form.get("transport_status", "Scheduled").strip()

        if not transport_date:
            conn.close()
            flash("Please select a transport date.", "danger")
            return redirect(url_for('shelter_schedule_transport', request_id=request_id))

        # Adopter delivery method is strictly preserved; only date, time, and status are updated
        cursor.execute("""
            UPDATE adoptions
            SET
                transport_date = ?,
                transport_time = ?,
                transport_status = ?
            WHERE id = ?
        """, (
            transport_date,
            transport_time,
            transport_status if transport_status in ["Pending", "Scheduled", "In Transit", "Delivered"] else "Scheduled",
            request_id
        ))

        conn.commit()
        conn.close()

        flash(f"Transport for request #{request_id} scheduled for {transport_date}.", "success")
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
        SELECT
            p.id, p.name, p.breed, p.age, p.gender, p.vaccinated, p.description, p.image, p.status, p.shelter_id,
            u.id, u.fullname, u.email, u.phone, u.address
        FROM pets p
        LEFT JOIN users u ON p.shelter_id = u.id
        WHERE p.id = ?
    """, (pet_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return "Pet not found."

    shelter_id = row[9]
    shelter_name = row[11]
    if not shelter_id:
        cursor.execute("SELECT id, fullname, email, phone, address FROM users WHERE role = 'Shelter' ORDER BY id ASC LIMIT 1")
        sh = cursor.fetchone()
        if sh:
            shelter_id = sh[0]
            shelter_name = sh[1]
            cursor.execute("UPDATE pets SET shelter_id = ? WHERE id = ?", (shelter_id, pet_id))
            conn.commit()

    conn.close()

    shelter_info = {
        'id': shelter_id,
        'name': shelter_name or "Verified Shelter Organization",
        'email': row[12] or "",
        'phone': row[13] or "",
        'address': row[14] or ""
    }

    return render_template("pet_details.html", pet=row[:10], shelter=shelter_info)


@app.route('/contact-shelter/<int:pet_id>', methods=['POST'])
def contact_shelter(pet_id):
    if 'user' not in session:
        flash("Please log in as an adopter to contact the shelter.", "info")
        return redirect(url_for('login'))

    if session.get('role') == 'Shelter':
        flash("Shelters cannot send adopter inquiries.", "warning")
        return redirect(url_for('shelter_dashboard'))

    if session.get('role') == 'Admin':
        return redirect(url_for('admin'))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.id, p.name, p.shelter_id, u.fullname, u.email
        FROM pets p
        LEFT JOIN users u ON p.shelter_id = u.id
        WHERE p.id = ?
    """, (pet_id,))
    pet_row = cursor.fetchone()

    if not pet_row:
        conn.close()
        flash("Pet not found.", "danger")
        return redirect(url_for('pets'))

    pet_id_val, pet_name, shelter_id, shelter_name, shelter_email = pet_row

    if not shelter_id:
        cursor.execute("SELECT id, fullname FROM users WHERE role = 'Shelter' ORDER BY id ASC LIMIT 1")
        default_sh = cursor.fetchone()
        if default_sh:
            shelter_id = default_sh[0]
            shelter_name = default_sh[1]
            cursor.execute("UPDATE pets SET shelter_id = ? WHERE id = ?", (shelter_id, pet_id))
            conn.commit()

    message_text = request.form.get('message', '').strip()
    valid, msg = validate_message(message_text)
    if not valid:
        conn.close()
        flash(msg, "danger")
        return redirect(url_for('pet_details', pet_id=pet_id))

    user_id = session.get('user_id')
    cursor.execute("SELECT fullname, email FROM users WHERE id = ?", (user_id,))
    user_rec = cursor.fetchone()
    user_name = user_rec[0] if user_rec and user_rec[0] else session.get('user', 'Adopter')
    user_email = user_rec[1] if user_rec and user_rec[1] else "adopter@petadoption.com"

    adoption_id = request.form.get('adoption_id', '').strip()
    if adoption_id:
        subject = f"Inquiry regarding {pet_name} (Adoption #{adoption_id})"
    else:
        subject = f"Inquiry regarding {pet_name}"

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conv_id = get_or_create_conversation(cursor, user_id, shelter_id, pet_id)

    cursor.execute("""
        INSERT INTO messages (
            conversation_id,
            sender_id,
            sender_type,
            message,
            sent_at,
            is_read,
            user_id,
            name,
            email,
            subject,
            status,
            created_at,
            shelter_id,
            pet_id
        )
        VALUES (?, ?, 'Adopter', ?, ?, 0, ?, ?, ?, ?, 'Unread', ?, ?, ?)
    """, (
        conv_id,
        user_id,
        message_text,
        now_str,
        user_id,
        user_name,
        user_email,
        subject,
        now_str,
        shelter_id,
        pet_id
    ))
    cursor.execute("UPDATE conversations SET updated_at = ?, status = 'Open' WHERE id = ?", (now_str, conv_id))
    conn.commit()
    conn.close()

    flash(f"Your inquiry regarding {pet_name} has been sent directly to {shelter_name or 'the shelter'}! The conversation remains open for unlimited messaging.", "success")
    return redirect(url_for('view_conversation', conversation_id=conv_id))


@app.route('/conversation/<int:conversation_id>')
def view_conversation(conversation_id):
    if 'user' not in session:
        flash("Please log in to view this conversation.", "info")
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    user_role = session.get('role')

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            c.id,
            c.adopter_id,
            c.shelter_id,
            c.pet_id,
            c.created_at,
            c.updated_at,
            c.status,
            u_adopter.fullname AS adopter_name,
            u_adopter.email AS adopter_email,
            u_adopter.phone AS adopter_phone,
            u_shelter.fullname AS shelter_name,
            u_shelter.email AS shelter_email,
            u_shelter.phone AS shelter_phone,
            p.name AS pet_name,
            p.breed AS pet_breed,
            p.image AS pet_image,
            p.status AS pet_status
        FROM conversations c
        LEFT JOIN users u_adopter ON c.adopter_id = u_adopter.id
        LEFT JOIN users u_shelter ON c.shelter_id = u_shelter.id
        LEFT JOIN pets p ON c.pet_id = p.id
        WHERE c.id = ?
    """, (conversation_id,))
    conv_row = cursor.fetchone()

    if not conv_row:
        conn.close()
        flash("Conversation not found.", "danger")
        return redirect(url_for('shelter_dashboard') if user_role == 'Shelter' else url_for('my_messages'))

    adopter_id = conv_row[1]
    shelter_id = conv_row[2]

    # STRICT SECURITY CHECK: Only participant adopter, participant shelter, or Admin can access
    if user_role != 'Admin' and user_id != adopter_id and user_id != shelter_id:
        conn.close()
        flash("Access Denied: You do not have permission to view this conversation.", "danger")
        return redirect(url_for('shelter_dashboard') if user_role == 'Shelter' else url_for('my_messages'))

    # Mark incoming messages as read
    if user_id == adopter_id or user_role == 'Adopter':
        cursor.execute("UPDATE messages SET is_read = 1 WHERE conversation_id = ? AND sender_type = 'Shelter' AND is_read = 0", (conversation_id,))
    elif user_id == shelter_id or user_role == 'Shelter':
        cursor.execute("UPDATE messages SET is_read = 1, status = 'Read' WHERE conversation_id = ? AND sender_type = 'Adopter' AND is_read = 0", (conversation_id,))
    conn.commit()

    # Query all messages in chronological order (oldest at top, newest at bottom)
    cursor.execute("""
        SELECT
            m.id,
            m.conversation_id,
            m.sender_id,
            m.sender_type,
            m.message,
            m.sent_at,
            m.is_read,
            COALESCE(u.fullname, m.name, m.sender_type) AS sender_name
        FROM messages m
        LEFT JOIN users u ON m.sender_id = u.id
        WHERE m.conversation_id = ?
        ORDER BY m.id ASC
    """, (conversation_id,))
    conv_messages = cursor.fetchall()
    conn.close()

    conv_data = {
        'id': conv_row[0],
        'adopter_id': conv_row[1],
        'shelter_id': conv_row[2],
        'pet_id': conv_row[3],
        'created_at': conv_row[4],
        'updated_at': conv_row[5],
        'status': conv_row[6],
        'adopter_name': conv_row[7] or 'Adopter',
        'adopter_email': conv_row[8] or '',
        'adopter_phone': conv_row[9] or '',
        'shelter_name': conv_row[10] or 'Shelter',
        'shelter_email': conv_row[11] or '',
        'shelter_phone': conv_row[12] or '',
        'pet_name': conv_row[13],
        'pet_breed': conv_row[14],
        'pet_image': conv_row[15],
        'pet_status': conv_row[16]
    }

    return render_template(
        "conversation.html",
        conversation=conv_data,
        messages=conv_messages,
        current_user_id=user_id,
        user_role=user_role
    )


@app.route('/conversation/<int:conversation_id>/send', methods=['POST'])
def send_conversation_message(conversation_id):
    if 'user' not in session:
        flash("Please log in to send a message.", "info")
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    user_role = session.get('role')

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.id, c.adopter_id, c.shelter_id, c.pet_id, c.status, p.name AS pet_name
        FROM conversations c
        LEFT JOIN pets p ON c.pet_id = p.id
        WHERE c.id = ?
    """, (conversation_id,))
    conv = cursor.fetchone()

    if not conv:
        conn.close()
        flash("Conversation not found.", "danger")
        return redirect(url_for('shelter_dashboard') if user_role == 'Shelter' else url_for('my_messages'))

    adopter_id = conv[1]
    shelter_id = conv[2]
    pet_id = conv[3]
    pet_name = conv[5]

    # STRICT SECURITY CHECK: Sender must be either adopter or shelter of this conversation
    if user_id == adopter_id:
        sender_type = 'Adopter'
    elif user_id == shelter_id:
        sender_type = 'Shelter'
    elif user_role == 'Admin':
        sender_type = 'Shelter'
    else:
        conn.close()
        flash("Access Denied: You do not have permission to send messages in this conversation.", "danger")
        return redirect(url_for('shelter_dashboard') if user_role == 'Shelter' else url_for('my_messages'))

    message_text = request.form.get('message', '').strip()
    if not message_text or len(message_text) < 2 or len(message_text) > 2000:
        conn.close()
        flash("Message must be between 2 and 2000 characters.", "danger")
        return redirect(request.referrer or url_for('view_conversation', conversation_id=conversation_id))

    cursor.execute("SELECT fullname, email FROM users WHERE id = ?", (user_id,))
    user_rec = cursor.fetchone()
    user_name = user_rec[0] if user_rec and user_rec[0] else session.get('user', sender_type)
    user_email = user_rec[1] if user_rec and user_rec[1] else ""

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if sender_type == 'Adopter':
        subject = f"Inquiry regarding {pet_name}" if pet_name else "Inquiry"
        cursor.execute("""
            INSERT INTO messages (
                conversation_id, sender_id, sender_type, message, sent_at, is_read,
                user_id, name, email, subject, status, created_at, shelter_id, pet_id
            )
            VALUES (?, ?, 'Adopter', ?, ?, 0, ?, ?, ?, ?, 'Unread', ?, ?, ?)
        """, (
            conversation_id, user_id, message_text, now_str,
            adopter_id, user_name, user_email, subject, now_str, shelter_id, pet_id
        ))
    else: # Shelter
        cursor.execute("""
            INSERT INTO messages (
                conversation_id, sender_id, sender_type, message, sent_at, is_read,
                user_id, shelter_id, pet_id, name, status, created_at
            )
            VALUES (?, ?, 'Shelter', ?, ?, 0, ?, ?, ?, ?, 'Read', ?)
        """, (
            conversation_id, user_id, message_text, now_str,
            adopter_id, shelter_id, pet_id, user_name, now_str
        ))
        # Update most recent unreplied adopter message's reply field for legacy assertions
        cursor.execute("""
            UPDATE messages
            SET reply = ?, status = 'Read'
            WHERE id = (
                SELECT id FROM messages
                WHERE conversation_id = ? AND sender_type = 'Adopter'
                ORDER BY id DESC LIMIT 1
            )
        """, (message_text, conversation_id))

    # Keep conversation Open and update timestamp
    cursor.execute("UPDATE conversations SET updated_at = ?, status = 'Open' WHERE id = ?", (now_str, conversation_id))
    conn.commit()
    conn.close()

    flash("Your message has been sent!" if sender_type == 'Adopter' else "Your reply has been sent!", "success")
    ref = request.referrer or ""
    if "my-messages" in ref:
        return redirect(url_for('my_messages'))
    elif "shelter-dashboard" in ref:
        return redirect(url_for('shelter_dashboard') + "#messages-section")
    return redirect(url_for('view_conversation', conversation_id=conversation_id))


@app.route('/adoption/<int:pet_id>', methods=['GET', 'POST'])
def adoption(pet_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') == "Shelter":
        return redirect(url_for('shelter_dashboard'))

    if session.get('role') == "Admin":
        return redirect(url_for('admin'))

    if request.method == "POST":
        adopter_name = request.form.get("adopter_name", "").strip() or session.get('user', '').strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        transport_method = request.form.get("transport_method", "Home Delivery").strip()

        valid, msg = validate_fullname(adopter_name)
        if not valid:
            return render_template("adoption.html", pet_id=pet_id, error=msg, form_data=request.form)

        valid, msg = validate_phone(phone)
        if not valid:
            return render_template("adoption.html", pet_id=pet_id, error=msg, form_data=request.form)

        valid, msg = validate_address(address)
        if not valid:
            return render_template("adoption.html", pet_id=pet_id, error=msg, form_data=request.form)

        if transport_method not in ["Home Delivery", "Shelter Pickup"]:
            transport_method = "Home Delivery"

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
            request_status,
            payment_amount,
            transport_status,
            adopter_id,
            request_date
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pet_id,
            adopter_name,
            phone,
            address,
            "Pending",
            transport_method,
            "Pending",
            500,
            "Pending",
            session.get('user_id'),
            datetime.date.today().isoformat()
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
    user_id = session.get('user_id')

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
            adoptions.transport_status,
            adoptions.payment_amount,
            pets.shelter_id,
            COALESCE(shelters.fullname, 'Verified Shelter') AS shelter_name
        FROM adoptions
        JOIN pets ON adoptions.pet_id = pets.id
        LEFT JOIN users shelters ON pets.shelter_id = shelters.id
        WHERE adoptions.adopter_id = ? OR adoptions.adopter_name = ?
        ORDER BY adoptions.id ASC
    """, (user_id, adopter_name))

    requests = cursor.fetchall()
    conn.close()

    today_str = datetime.date.today().isoformat()
    return render_template("my_requests.html", requests=requests, today=today_str)


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
        SELECT id, request_status, payment_status
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
    current_payment_status = adoption_record[2]

    # Payment is strictly allowed only after shelter approval
    if request_status != "Approved":
        conn.close()
        return "Payment is available only after the shelter approves your request."

    # If already paid, redirect directly to payment success page
    if current_payment_status == "Paid":
        conn.close()
        return redirect(url_for("payment_success", adoption_id=request_id))

    if request.method == "POST":
        payment_method = request.form.get("payment_method", "").strip()

        # Enforce strictly UPI or COD
        if payment_method not in ["UPI", "COD"]:
            conn.close()
            return render_template(
                "payment.html",
                pet_id=pet_id,
                request_id=request_id,
                error="Please select a valid payment method (UPI / Pay Online or Cash on Delivery).",
                form_data=request.form,
                payment_amount=500
            )

        # Fixed payment amount enforced in backend: strictly 500
        payment_amount = 500
        refund_status = "Not Applicable"
        now_str = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")

        if payment_method == "UPI":
            upi_id_raw = request.form.get("upi_id", "").strip()
            valid, msg = validate_upi_id(upi_id_raw)
            if not valid:
                conn.close()
                return render_template(
                    "payment.html",
                    pet_id=pet_id,
                    request_id=request_id,
                    error=msg,
                    form_data=request.form,
                    payment_amount=500
                )
            upi_id = msg
            payment_status = "Paid"

            cursor.execute("""
                UPDATE adoptions
                SET
                    payment_method = ?,
                    payment_status = ?,
                    payment_amount = ?,
                    refund_status = ?,
                    upi_id = ?,
                    payment_date = ?
                WHERE id = ?
            """, (
                payment_method,
                payment_status,
                payment_amount,
                refund_status,
                upi_id,
                now_str,
                request_id
            ))

            conn.commit()
            conn.close()

            return redirect(url_for("payment_success", adoption_id=request_id))

        else:  # Cash on Delivery
            payment_status = "COD"
            cursor.execute("""
                UPDATE adoptions
                SET
                    payment_method = ?,
                    payment_status = ?,
                    payment_amount = ?,
                    refund_status = ?,
                    upi_id = NULL,
                    payment_date = ?
                WHERE id = ?
            """, (
                payment_method,
                payment_status,
                payment_amount,
                refund_status,
                now_str,
                request_id
            ))

            conn.commit()
            conn.close()

            flash("Cash on Delivery selected. You will pay ₹500 upon pet delivery.", "info")
            return redirect(url_for("my_requests"))

    conn.close()

    return render_template(
        "payment.html",
        pet_id=pet_id,
        request_id=request_id,
        payment_amount=500
    )


@app.route('/transport/<int:pet_id>', methods=['GET', 'POST'])
def transport(pet_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    # Adopters choose delivery method only during adoption application; not editable after submission
    flash("Delivery method is chosen during the adoption application and cannot be changed after submission.", "info")
    return redirect(url_for('my_requests'))


@app.route('/payment-success/<int:adoption_id>')
def payment_success(adoption_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            adoptions.id,
            pets.name,
            adoptions.payment_amount,
            adoptions.upi_id,
            adoptions.payment_date,
            adoptions.payment_status,
            adoptions.payment_method,
            adoptions.adopter_name
        FROM adoptions
        JOIN pets ON adoptions.pet_id = pets.id
        WHERE adoptions.id = ?
    """, (adoption_id,))

    adoption = cursor.fetchone()
    conn.close()

    if not adoption:
        return "Adoption order not found."

    # Authorization: Must be the adopter or an Admin
    if session.get('role') != 'Admin' and session.get('user') != adoption[7]:
        return "Access Denied!"

    raw_status = adoption[5]
    display_status = "Successful" if raw_status in ["Paid", "Successful"] else (raw_status or "Successful")

    return render_template(
        "payment_success.html",
        adoption_id=adoption[0],
        pet_name=adoption[1],
        payment_amount=int(adoption[2]) if adoption[2] else 500,
        upi_id=adoption[3],
        payment_date=adoption[4] or datetime.datetime.now().strftime("%d %b %Y, %I:%M %p"),
        payment_status=display_status,
        payment_method=adoption[6]
    )


@app.route('/success')
def success():
    adoption_id = request.args.get('adoption_id')
    if adoption_id:
        return redirect(url_for('payment_success', adoption_id=adoption_id))
    return render_template("success.html")


# =========================================================
# DELIVERY & TRANSPORT MANAGEMENT (ASSIGNED TO SHELTER)
# =========================================================

@app.route('/transport-dashboard')
def transport_dashboard():
    # Transport provider module has been removed; transport management belongs to Shelter
    if 'user' not in session:
        return redirect(url_for('login'))
    if session.get('role') == 'Shelter':
        flash("Delivery and transport management is integrated directly into your Shelter Hub.", "info")
        return redirect(url_for('shelter_dashboard'))
    return redirect(url_for('pets'))


@app.route('/transport-update-status/<int:adoption_id>', methods=['POST'])
def transport_update_status(adoption_id):
    # Delegate transport status updates directly to shelter handler
    if 'user' not in session:
        return redirect(url_for('login'))
    if session.get('role') != 'Shelter':
        return "Access Denied! Only shelters manage pet transport."
    return shelter_update_transport_status(adoption_id)


@app.route('/transport-update-transit/<int:adoption_id>', methods=['POST'])
def transport_update_transit(adoption_id):
    # Adopter delivery method selection cannot be altered by anyone
    flash("The delivery method was selected by the adopter during request and cannot be changed.", "warning")
    return redirect(url_for('shelter_requests'))


@app.route('/transport-update-date/<int:adoption_id>', methods=['POST'])
def transport_update_date(adoption_id):
    # Delegate delivery date scheduling directly to shelter handler
    if 'user' not in session:
        return redirect(url_for('login'))
    if session.get('role') != 'Shelter':
        return "Access Denied! Only shelters schedule pet delivery."
    return shelter_set_delivery_date(adoption_id)


# ==========================
# INFORMATIONAL & MESSAGES
# ==========================

@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Query approved shelters for specific direct message routing
    cursor.execute("""
        SELECT id, fullname, address
        FROM users
        WHERE role = 'Shelter' AND account_status = 'Approved'
        ORDER BY fullname ASC
    """)
    shelters = cursor.fetchall()

    pet_id = request.form.get('pet_id') or request.args.get('pet_id')
    pet_name = None
    selected_shelter_id = request.args.get('shelter_id')

    if pet_id:
        try:
            pet_id = int(pet_id)
            cursor.execute("SELECT name, shelter_id FROM pets WHERE id = ?", (pet_id,))
            p_row = cursor.fetchone()
            if p_row:
                pet_name = p_row[0]
                if p_row[1]:
                    selected_shelter_id = p_row[1]
        except (ValueError, TypeError):
            pet_id = None

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        shelter_id = request.form.get('shelter_id') or selected_shelter_id

        # 1. Name validation
        valid, msg = validate_fullname(name)
        if not valid:
            conn.close()
            return render_template("contact.html", error=msg, form_data=request.form, shelters=shelters, pet_id=pet_id, selected_shelter_id=selected_shelter_id)

        # 2. Email validation
        valid, msg = validate_email(email)
        if not valid:
            conn.close()
            return render_template("contact.html", error=msg, form_data=request.form, shelters=shelters, pet_id=pet_id, selected_shelter_id=selected_shelter_id)
        email = msg

        # 3. Subject validation
        valid, msg = validate_subject(subject)
        if not valid:
            conn.close()
            return render_template("contact.html", error=msg, form_data=request.form, shelters=shelters, pet_id=pet_id, selected_shelter_id=selected_shelter_id)

        # 4. Message validation
        valid, msg = validate_message(message)
        if not valid:
            conn.close()
            return render_template("contact.html", error=msg, form_data=request.form, shelters=shelters, pet_id=pet_id, selected_shelter_id=selected_shelter_id)

        # Ensure shelter_id is associated with a specific shelter (never orphan or common inbox)
        if not shelter_id:
            if shelters:
                shelter_id = shelters[0][0]
            else:
                cursor.execute("SELECT id FROM users WHERE role = 'Shelter' ORDER BY id ASC LIMIT 1")
                sh_row = cursor.fetchone()
                shelter_id = sh_row[0] if sh_row else None

        u_id = session.get('user_id')
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conv_id = None
        if u_id and shelter_id:
            conv_id = get_or_create_conversation(cursor, u_id, shelter_id, pet_id)

        cursor.execute("""
            INSERT INTO messages
            (
                conversation_id,
                sender_id,
                sender_type,
                message,
                sent_at,
                is_read,
                user_id,
                name,
                email,
                subject,
                status,
                created_at,
                shelter_id,
                pet_id
            )
            VALUES (?, ?, 'Adopter', ?, ?, 0, ?, ?, ?, ?, 'Unread', ?, ?, ?)
        """, (
            conv_id,
            u_id,
            message,
            now_str,
            u_id,
            name,
            email,
            subject,
            now_str,
            shelter_id,
            pet_id
        ))

        if conv_id:
            cursor.execute("UPDATE conversations SET updated_at = ?, status = 'Open' WHERE id = ?", (now_str, conv_id))

        conn.commit()
        conn.close()

        return render_template(
            "contact.html",
            success="Your message has been sent directly to the shelter!",
            shelters=shelters
        )

    conn.close()
    default_subject = f"Inquiry regarding {pet_name}" if pet_name else ""
    return render_template(
        "contact.html",
        shelters=shelters,
        pet_id=pet_id,
        selected_shelter_id=selected_shelter_id,
        default_subject=default_subject
    )


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_role = session.get('role')
    user_id = session.get('user_id')

    # If Shelter visits /profile, redirect to shelter dashboard profile section
    if user_role == 'Shelter':
        return redirect(url_for('shelter_dashboard') + "#profile-section")

    if user_role == 'Admin':
        return redirect(url_for('admin'))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == 'POST':
        fullname = request.form.get('fullname', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        new_password = request.form.get('new_password', '').strip()

        # 1. Full name validation
        valid, msg = validate_fullname(fullname, allow_digits=False)
        if not valid:
            conn.close()
            flash(msg, "danger")
            return redirect(url_for('profile'))

        # 2. Email validation
        valid, msg = validate_email(email)
        if not valid:
            conn.close()
            flash(msg, "danger")
            return redirect(url_for('profile'))
        email = msg

        # 3. Phone validation
        valid, msg = validate_phone(phone)
        if not valid:
            conn.close()
            flash(msg, "danger")
            return redirect(url_for('profile'))
        phone = msg

        # 4. Address validation
        valid, msg = validate_address(address)
        if not valid:
            conn.close()
            flash(msg, "danger")
            return redirect(url_for('profile'))

        # 5. Check email uniqueness against other users
        cursor.execute("SELECT id FROM users WHERE LOWER(TRIM(email)) = LOWER(?) AND id != ?", (email, user_id))
        if cursor.fetchone():
            conn.close()
            flash("This email address is already in use by another account.", "danger")
            return redirect(url_for('profile'))

        # 6. Apply updates
        if new_password:
            if len(new_password) < 6:
                conn.close()
                flash("New password must be at least 6 characters long.", "danger")
                return redirect(url_for('profile'))
            cursor.execute("""
                UPDATE users
                SET fullname = ?, email = ?, phone = ?, address = ?, password = ?
                WHERE id = ? AND role = 'Adopter'
            """, (fullname, email, phone, address, new_password, user_id))
        else:
            cursor.execute("""
                UPDATE users
                SET fullname = ?, email = ?, phone = ?, address = ?
                WHERE id = ? AND role = 'Adopter'
            """, (fullname, email, phone, address, user_id))

        # Synchronize adopter name across their adoption requests
        cursor.execute("UPDATE adoptions SET adopter_name = ? WHERE adopter_id = ?", (fullname, user_id))

        conn.commit()
        session['user'] = fullname
        conn.close()

        flash("Your profile has been updated successfully!", "success")
        return redirect(url_for('profile'))

    # GET Request: Fetch user record and engagement statistics
    cursor.execute("""
        SELECT id, fullname, email, phone, address, role, account_status
        FROM users
        WHERE id = ?
    """, (user_id,))
    user_record = cursor.fetchone()

    if not user_record:
        conn.close()
        flash("User profile not found.", "danger")
        return redirect(url_for('login'))

    user_name = user_record[1]

    cursor.execute("SELECT COUNT(*) FROM adoptions WHERE adopter_id = ? OR adopter_name = ?", (user_id, user_name))
    total_requests = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM adoptions WHERE (adopter_id = ? OR adopter_name = ?) AND request_status = 'Approved'", (user_id, user_name))
    approved_requests = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM messages WHERE user_id = ?", (user_id,))
    total_messages = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "profile.html",
        user=user_record,
        total_requests=total_requests,
        approved_requests=approved_requests,
        total_messages=total_messages
    )


@app.route('/my-messages')
def my_messages():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_id = session.get('user_id')

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
    u_row = cursor.fetchone()
    user_email = u_row[0] if u_row else None

    # 1. Fetch conversations for this adopter
    cursor.execute("""
        SELECT
            c.id,
            c.adopter_id,
            c.shelter_id,
            c.pet_id,
            c.created_at,
            c.updated_at,
            c.status,
            u.fullname AS shelter_name,
            u.email AS shelter_email,
            u.phone AS shelter_phone,
            p.name AS pet_name,
            p.breed AS pet_breed,
            p.image AS pet_image
        FROM conversations c
        LEFT JOIN users u ON c.shelter_id = u.id
        LEFT JOIN pets p ON c.pet_id = p.id
        WHERE c.adopter_id = ?
        ORDER BY c.updated_at DESC
    """, (user_id,))
    conv_rows = cursor.fetchall()

    conversations = []
    for c_row in conv_rows:
        cid = c_row[0]
        cursor.execute("""
            SELECT
                m.id,
                m.sender_id,
                m.sender_type,
                m.message,
                m.sent_at,
                m.is_read,
                COALESCE(u.fullname, m.name, m.sender_type) AS sender_name
            FROM messages m
            LEFT JOIN users u ON m.sender_id = u.id
            WHERE m.conversation_id = ?
            ORDER BY m.id ASC
        """, (cid,))
        c_msgs = cursor.fetchall()

        latest_reply = None
        has_reply = False
        unread_count = 0
        for m in c_msgs:
            if m[2] == 'Shelter':
                has_reply = True
                latest_reply = m[3]
                if m[5] == 0:
                    unread_count += 1

        conversations.append({
            'id': c_row[0],
            'adopter_id': c_row[1],
            'shelter_id': c_row[2],
            'pet_id': c_row[3],
            'created_at': c_row[4],
            'updated_at': c_row[5],
            'status': c_row[6],
            'shelter_name': c_row[7] or 'Verified Shelter',
            'shelter_email': c_row[8] or '',
            'shelter_phone': c_row[9] or '',
            'pet_name': c_row[10],
            'pet_breed': c_row[11],
            'pet_image': c_row[12],
            'messages': c_msgs,
            'latest_reply': latest_reply,
            'has_reply': has_reply,
            'unread_count': unread_count
        })

    # 2. Fetch messages flat list for backwards compatibility
    cursor.execute("""
        SELECT
            m.id,
            m.name,
            m.email,
            m.subject,
            m.message,
            m.status,
            m.reply,
            m.created_at,
            m.shelter_id,
            u.fullname AS shelter_name,
            m.pet_id,
            p.name AS pet_name,
            p.image AS pet_image,
            m.conversation_id
        FROM messages m
        LEFT JOIN users u ON m.shelter_id = u.id
        LEFT JOIN pets p ON m.pet_id = p.id
        WHERE (m.user_id = ? OR (m.user_id IS NULL AND m.email = ?)) AND (m.sender_type IS NULL OR m.sender_type = 'Adopter')
        ORDER BY m.id DESC
    """, (user_id, user_email))
    raw_user_messages = cursor.fetchall()

    user_messages = []
    for r in raw_user_messages:
        r_list = list(r)
        if not r_list[6] and r_list[13]:
            cursor.execute("""
                SELECT message FROM messages
                WHERE conversation_id = ? AND sender_type = 'Shelter'
                ORDER BY id DESC LIMIT 1
            """, (r_list[13],))
            rep_row = cursor.fetchone()
            if rep_row:
                r_list[6] = rep_row[0]
                r_list[5] = 'Read'
        user_messages.append(r_list)

    conn.close()

    return render_template("my_messages.html", messages=user_messages, conversations=conversations)


@app.route('/messages')
def messages():
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') == 'Shelter':
        return redirect(url_for('shelter_dashboard') + "#messages-section")

    if session.get('role') != 'Admin':
        return "Access Denied!"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            m.id,
            m.user_id,
            m.name,
            m.email,
            m.subject,
            m.message,
            m.status,
            m.reply,
            m.created_at,
            m.shelter_id,
            u.fullname AS shelter_name,
            m.pet_id,
            p.name AS pet_name
        FROM messages m
        LEFT JOIN users u ON m.shelter_id = u.id
        LEFT JOIN pets p ON m.pet_id = p.id
        ORDER BY m.id DESC
    """)
    all_messages = cursor.fetchall()
    conn.close()

    return render_template("messages.html", messages=all_messages)


@app.route('/reply-message/<int:message_id>', methods=['POST'])
def reply_message(message_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') == 'Shelter':
        return shelter_reply_message(message_id)

    if session.get('role') != 'Admin':
        return "Access Denied!"

    reply = request.form.get('reply', '').strip()

    if not reply or len(reply) < 2 or len(reply) > 2000:
        return "Reply must be between 2 and 2000 characters."

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
