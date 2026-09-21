from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_from_directory
)

from flask_mail import Mail, Message

from werkzeug.utils import secure_filename

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

import sqlite3
import os
import hashlib
import secrets
import time
import math
import uuid
import json
from dotenv import load_dotenv

load_dotenv()


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)

STATIC_FOLDER = os.path.join(
    BASE_DIR,
    "static"
)

TEMPLATE_FOLDER = os.path.join(
    BASE_DIR,
    "templates"
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "campus_security.db"
)


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(
    __name__,
    static_folder=None,
    template_folder=TEMPLATE_FOLDER
)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "dev-campus-security-secret-key"
)


# =========================================================
# EMAIL CONFIGURATION
# =========================================================

app.config["MAIL_SERVER"] = os.environ.get(
    "MAIL_SERVER",
    "smtp.gmail.com"
)

app.config["MAIL_PORT"] = int(
    os.environ.get(
        "MAIL_PORT",
        587
    )
)

app.config["MAIL_USE_TLS"] = (
    os.environ.get(
        "MAIL_USE_TLS",
        "true"
    ).lower()
    == "true"
)

app.config["MAIL_USE_SSL"] = (
    os.environ.get(
        "MAIL_USE_SSL",
        "false"
    ).lower()
    == "true"
)

app.config["MAIL_USERNAME"] = os.environ.get(
    "MAIL_USERNAME"
)

app.config["MAIL_PASSWORD"] = os.environ.get(
    "MAIL_PASSWORD"
)

app.config["MAIL_DEFAULT_SENDER"] = (
    os.environ.get("MAIL_DEFAULT_SENDER")
    or app.config["MAIL_USERNAME"]
)

mail = Mail(app)


# =========================================================
# EMAIL NOTIFICATION SETTINGS
# =========================================================

SECURITY_ALERT_EMAILS = [
    address.strip()
    for address in os.environ.get(
        "SECURITY_ALERT_EMAILS",
        app.config.get("MAIL_USERNAME") or ""
    ).split(",")
    if address.strip()
]


# =========================================================
# EMAIL NOTIFICATION HELPERS
# =========================================================

def send_system_email(subject, recipients, body):

    recipients = [
        recipient
        for recipient in recipients
        if recipient
    ]

    if not recipients:
        return False

    if (
        not app.config.get("MAIL_USERNAME")
        or not app.config.get("MAIL_PASSWORD")
        or not app.config.get("MAIL_DEFAULT_SENDER")
    ):
        print("Email skipped: mail settings are incomplete.")
        return False

    message = Message(
        subject=subject,
        recipients=recipients,
        body=body
    )

    try:
        mail.send(message)
        return True
    except Exception as error:
        print("System email send error:", error)
        return False


def get_user_contact(user_id):

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            full_name,
            email,
            username,
            email_verified
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    )

    user = cursor.fetchone()
    connection.close()
    return user


def send_welcome_email(email, full_name):

    return send_system_email(
        "UFH Security - Account Activated",
        [email],
        f"""Hello {full_name},

Your UFH Campus Security Management System Student account has been successfully verified and activated.

You can now sign in and use the Student Dashboard, report incidents, view your reports, access emergency contacts and use Campus SOS.

If you did not create this account, please contact Campus Security.

UFH Campus Security Management System
Alice Campus
"""
    )


def send_incident_confirmation(user_id, incident_id, incident_type, location, priority, is_anonymous):

    user = get_user_contact(user_id)

    if not user or not user[1] or user[3] != 1:
        return False

    privacy_note = (
        "This report was submitted using the anonymous reporting option. "
        "Your identity is hidden from operational Security/Admin incident views."
        if is_anonymous == 1
        else "This report is linked to your verified Student account."
    )

    return send_system_email(
        f"UFH Security - Incident #{incident_id} Received",
        [user[1]],
        f"""Hello {user[0] or user[2]},

Your incident report has been received.

Incident ID: #{incident_id}
Incident Type: {incident_type}
Location: {location}
Priority: {priority}
Status: Pending

{privacy_note}

Keep Incident #{incident_id} for your records. You can view updates under My Reports.

UFH Campus Security Management System
Alice Campus
"""
    )


def send_sos_confirmation(user_id, incident_id):

    user = get_user_contact(user_id)

    if not user or not user[1] or user[3] != 1:
        return False

    return send_system_email(
        f"UFH Security - SOS #{incident_id} Received",
        [user[1]],
        f"""Hello {user[0] or user[2]},

Your Campus SOS request has been recorded as Emergency #{incident_id}.

Priority: High
Status: Pending

For privacy, this email does not repeat your precise location. If you remain in immediate danger, contact Campus Control, SAPS or emergency services directly.

UFH Campus Security Management System
Alice Campus
"""
    )


def send_status_update_email(user_id, incident_id, incident_type, new_status):

    if not user_id:
        return False

    user = get_user_contact(user_id)

    if not user or not user[1] or user[3] != 1:
        return False

    return send_system_email(
        f"UFH Security - Incident #{incident_id} Updated",
        [user[1]],
        f"""Hello {user[0] or user[2]},

The status of your incident report has changed.

Incident ID: #{incident_id}
Incident Type: {incident_type}
New Status: {new_status}

You can sign in to the Campus Security Management System and open My Reports for the latest information.

UFH Campus Security Management System
Alice Campus
"""
    )


def get_security_alert_recipients():
    """Return active, verified Security Officer emails plus optional .env recipients."""
    recipients = list(SECURITY_ALERT_EMAILS)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT email
        FROM users
        WHERE role = 'Security Officer'
          AND disabled = 0
          AND email_verified = 1
          AND email IS NOT NULL
          AND TRIM(email) <> ''
        """
    )
    recipients.extend(row[0].strip().lower() for row in cursor.fetchall() if row[0])
    connection.close()

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(recipients))


def send_security_alert(incident_id, incident_type, location, priority):

    recipients = get_security_alert_recipients()
    if not recipients:
        return False

    return send_system_email(
        f"UFH Security Alert - {priority} Priority #{incident_id}",
        recipients,
        f"""A {priority.lower()}-priority incident has been submitted.

Incident ID: #{incident_id}
Incident Type: {incident_type}
Location: {location}
Priority: {priority}
Status: Pending

Open the Security Dashboard for the complete incident record.

UFH Campus Security Management System
Alice Campus
"""
    )


def create_account_code(table_name, user_id):

    allowed_tables = {
        "password_reset_codes",
        "email_change_codes"
    }

    if table_name not in allowed_tables:
        raise ValueError("Invalid verification table.")

    code = str(secrets.randbelow(900000) + 100000)
    code_hash = hash_verification_code(code)
    now = int(time.time())
    expires_at = now + 600

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    if table_name == "password_reset_codes":
        cursor.execute(
            """
            INSERT INTO password_reset_codes
            (user_id, code_hash, expires_at, last_sent_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET
                code_hash = excluded.code_hash,
                expires_at = excluded.expires_at,
                last_sent_at = excluded.last_sent_at
            """,
            (user_id, code_hash, expires_at, now)
        )
    else:
        raise ValueError("Use the email-change helper for email changes.")

    connection.commit()
    connection.close()
    return code


def send_password_reset_email(user_id, email, full_name):

    code = create_account_code("password_reset_codes", user_id)

    return send_system_email(
        "UFH Security - Password Reset Code",
        [email],
        f"""Hello {full_name},

A password reset was requested for your UFH Campus Security account.

Your 6-digit password reset code is:

{code}

This code expires in 10 minutes.

If you did not request a password reset, you can ignore this email. Your password has not been changed.

UFH Campus Security Management System
Alice Campus
"""
    )


def send_password_changed_email(email, full_name):

    return send_system_email(
        "UFH Security - Password Changed",
        [email],
        f"""Hello {full_name},

The password for your UFH Campus Security account was changed successfully.

If you did not make or request this change, contact the system administrator or Campus Security immediately.

UFH Campus Security Management System
Alice Campus
"""
    )


def create_email_change_code(user_id, new_email):

    code = str(secrets.randbelow(900000) + 100000)
    code_hash = hash_verification_code(code)
    now = int(time.time())
    expires_at = now + 600

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO email_change_codes
        (user_id, new_email, code_hash, expires_at, last_sent_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            new_email = excluded.new_email,
            code_hash = excluded.code_hash,
            expires_at = excluded.expires_at,
            last_sent_at = excluded.last_sent_at
        """,
        (user_id, new_email, code_hash, expires_at, now)
    )

    connection.commit()
    connection.close()
    return code


def send_email_change_code(user_id, new_email, full_name):

    code = create_email_change_code(user_id, new_email)

    return send_system_email(
        "UFH Security - Verify New Email Address",
        [new_email],
        f"""Hello {full_name},

A request was made to use this email address for your UFH Campus Security account.

Your 6-digit verification code is:

{code}

This code expires in 10 minutes. The email address on the account will not change until this code is verified.

UFH Campus Security Management System
Alice Campus
"""
    )


# =========================================================
# STATIC FILES
# =========================================================
@app.route("/service-worker.js")
def service_worker():
    response = send_from_directory(
        "static",
        "service-worker.js"
    )
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response

@app.route("/static/<path:filename>")
def static_files(filename):

    return send_from_directory(
        STATIC_FOLDER,
        filename
    )


# =========================================================
# PRIORITY ALGORITHM
# =========================================================

def calculate_priority(incident_type):

    high_priority_incidents = [
        "Assault",
        "Harassment",
        "Emergency SOS"
    ]

    medium_priority_incidents = [
        "Theft",
        "Suspicious Activity"
    ]

    if incident_type in high_priority_incidents:

        return "High"

    elif incident_type in medium_priority_incidents:

        return "Medium"

    else:

        return "Low"


# =========================================================
# LOGIN CHECK
# =========================================================

def login_required():

    return session.get(
        "logged_in",
        False
    )


# =========================================================
# ADMIN CHECK
# =========================================================

def admin_required():

    if not session.get("logged_in"):

        return False

    if session.get("role") != "Admin":

        return False

    return True


# =========================================================
# SECURITY CHECK
# =========================================================

def security_required():

    if not session.get("logged_in"):

        return False

    if session.get("role") != "Security Officer":

        return False

    return True


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )

# =========================================================
# EMAIL VERIFICATION HELPERS
# =========================================================

def hash_verification_code(code):

    return hashlib.sha256(
        code.encode("utf-8")
    ).hexdigest()


def create_verification_code(user_id):

    code = str(
        secrets.randbelow(900000) + 100000
    )

    code_hash = hash_verification_code(
        code
    )

    now = int(
        time.time()
    )

    expires_at = (
        now + 600
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO email_verification_codes
        (
            user_id,
            code_hash,
            expires_at,
            last_sent_at
        )
        VALUES (?, ?, ?, ?)

        ON CONFLICT(user_id)
        DO UPDATE SET
            code_hash = excluded.code_hash,
            expires_at = excluded.expires_at,
            last_sent_at = excluded.last_sent_at
        """,
        (
            user_id,
            code_hash,
            expires_at,
            now
        )
    )

    connection.commit()
    connection.close()

    return code


def send_verification_email(
    user_id,
    email,
    full_name
):

    code = create_verification_code(
        user_id
    )

    if (
        not app.config.get("MAIL_USERNAME")
        or not app.config.get("MAIL_PASSWORD")
        or not app.config.get("MAIL_DEFAULT_SENDER")
    ):

        return False

    message = Message(
        subject=(
            "UFH Security - Verify Your Email"
        ),
        recipients=[
            email
        ]
    )

    message.body = f"""Hello {full_name},

Your UFH Campus Security Management System verification code is:

{code}

This code expires in 10 minutes.

If you did not create this account, you can ignore this email.

UFH Campus Security Management System
Alice Campus
"""

    try:

        mail.send(
            message
        )

        return True

    except Exception as error:

        print(
            "Email verification send error:",
            error
        )

        return False


# =========================================================
# CREATE STUDENT ACCOUNT
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    # -----------------------------------------------------
    # IF USER IS ALREADY LOGGED IN
    # -----------------------------------------------------

    if session.get("user_id"):

        role = session.get("role")

        if role == "Student":

            return redirect(
                url_for("student_dashboard")
            )

        elif role == "Admin":

            return redirect(
                url_for("admin")
            )

        else:

            return redirect(
                url_for("dashboard")
            )


    # -----------------------------------------------------
    # REGISTRATION FORM SUBMITTED
    # -----------------------------------------------------

    if request.method == "POST":

        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        full_name = request.form.get("full_name", "").strip()
        if first_name or last_name:
            full_name = (first_name + " " + last_name).strip()
        elif full_name:
            name_parts = full_name.split()
            first_name = name_parts[0] if name_parts else ""
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        phone_number = request.form.get("phone_number", "").strip()

        student_number = request.form.get(
            "student_number",
            ""
        ).strip().upper()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )


        form_values = {
            "full_name_value": full_name,
            "student_number_value": student_number,
            "email_value": email,
            "username_value": username
        }


        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if (
            not full_name
            or not student_number
            or not email
            or not username
            or not password
            or not confirm_password
        ):

            return render_template(
                "register.html",
                error="Please complete all required fields.",
                **form_values
            )


        if len(full_name) < 3:

            return render_template(
                "register.html",
                error="Please enter your full name.",
                **form_values
            )


        if (
            "@" not in email
            or "." not in email.split("@")[-1]
            or email.startswith("@")
            or email.endswith("@")
            or " " in email
        ):

            return render_template(
                "register.html",
                error="Please enter a valid email address.",
                **form_values
            )


        if len(username) < 3:

            return render_template(
                "register.html",
                error=(
                    "Username must contain at least "
                    "3 characters."
                ),
                **form_values
            )


        if len(password) < 6:

            return render_template(
                "register.html",
                error=(
                    "Password must contain at least "
                    "6 characters."
                ),
                **form_values
            )


        if password != confirm_password:

            return render_template(
                "register.html",
                error="The passwords do not match.",
                **form_values
            )


        # -------------------------------------------------
        # DATABASE
        # -------------------------------------------------

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        cursor = connection.cursor()


        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE LOWER(username) = LOWER(?)
            """,
            (
                username,
            )
        )

        if cursor.fetchone():

            connection.close()

            return render_template(
                "register.html",
                error=(
                    "That username is already registered. "
                    "Please choose another username."
                ),
                **form_values
            )


        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE UPPER(student_number) = UPPER(?)
            """,
            (
                student_number,
            )
        )

        if cursor.fetchone():

            connection.close()

            return render_template(
                "register.html",
                error=(
                    "That student number is already linked "
                    "to an account."
                ),
                **form_values
            )


        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE LOWER(email) = LOWER(?)
            """,
            (
                email,
            )
        )

        if cursor.fetchone():

            connection.close()

            return render_template(
                "register.html",
                error=(
                    "That email address is already linked "
                    "to an account."
                ),
                **form_values
            )


        hashed_password = (
            generate_password_hash(
                password
            )
        )


        try:

            cursor.execute(
                """
                INSERT INTO users
                (
                    username,
                    full_name,
                    first_name,
                    last_name,
                    student_number,
                    student_staff_number,
                    phone_number,
                    email,
                    email_verified,
                    password,
                    role,
                    disabled
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    full_name,
                    first_name,
                    last_name,
                    student_number,
                    student_number,
                    phone_number,
                    email,
                    0,
                    hashed_password,
                    "Student",
                    0
                )
            )

            user_id = (
                cursor.lastrowid
            )

            connection.commit()


        except sqlite3.IntegrityError:

            connection.close()

            return render_template(
                "register.html",
                error=(
                    "An account with those details "
                    "already exists."
                ),
                **form_values
            )


        connection.close()


        # -------------------------------------------------
        # EMAIL VERIFICATION
        # -------------------------------------------------

        session[
            "pending_verification_user_id"
        ] = user_id

        session[
            "pending_verification_email"
        ] = email

        email_sent = send_verification_email(
            user_id,
            email,
            full_name
        )


        return redirect(
            url_for(
                "verify_email",
                sent=(
                    "1"
                    if email_sent
                    else "0"
                )
            )
        )


    return render_template(
        "register.html"
    )


# =========================================================
# VERIFY EMAIL
# =========================================================

@app.route(
    "/verify-email",
    methods=["GET", "POST"]
)
def verify_email():

    user_id = session.get(
        "pending_verification_user_id"
    )

    if not user_id:

        return redirect(
            url_for("login")
        )


    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            email,
            full_name,
            email_verified
        FROM users
        WHERE id = ?
        AND role = 'Student'
        """,
        (
            user_id,
        )
    )

    user = cursor.fetchone()

    connection.close()


    if not user:

        session.pop(
            "pending_verification_user_id",
            None
        )

        session.pop(
            "pending_verification_email",
            None
        )

        return redirect(
            url_for("register")
        )


    email = user[0]
    full_name = user[1]
    email_verified = user[2]


    if email_verified == 1:

        session.pop(
            "pending_verification_user_id",
            None
        )

        session.pop(
            "pending_verification_email",
            None
        )

        return redirect(
            url_for(
                "login",
                verified="1"
            )
        )


    error = None
    success = None


    if request.method == "POST":

        code = request.form.get(
            "code",
            ""
        ).strip()


        if (
            not code.isdigit()
            or len(code) != 6
        ):

            error = (
                "Please enter the 6-digit "
                "verification code."
            )

        else:

            connection = sqlite3.connect(
                DATABASE_PATH
            )

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    code_hash,
                    expires_at
                FROM email_verification_codes
                WHERE user_id = ?
                """,
                (
                    user_id,
                )
            )

            verification = (
                cursor.fetchone()
            )


            if not verification:

                error = (
                    "No verification code was found. "
                    "Please request a new code."
                )

            elif int(time.time()) > verification[1]:

                error = (
                    "That verification code has expired. "
                    "Please request a new code."
                )

            elif (
                hash_verification_code(code)
                != verification[0]
            ):

                error = (
                    "The verification code is incorrect."
                )

            else:

                cursor.execute(
                    """
                    UPDATE users
                    SET email_verified = 1
                    WHERE id = ?
                    """,
                    (
                        user_id,
                    )
                )

                cursor.execute(
                    """
                    DELETE FROM email_verification_codes
                    WHERE user_id = ?
                    """,
                    (
                        user_id,
                    )
                )

                connection.commit()
                connection.close()

                send_welcome_email(
                    email,
                    full_name
                )

                session.pop(
                    "pending_verification_user_id",
                    None
                )

                session.pop(
                    "pending_verification_email",
                    None
                )

                return redirect(
                    url_for(
                        "login",
                        verified="1"
                    )
                )


            connection.close()


    sent_status = request.args.get(
        "sent"
    )

    if sent_status == "1":

        success = (
            "A 6-digit verification code "
            "was sent to your email."
        )

    elif sent_status == "0":

        error = (
            "Your account was created, but the "
            "verification email could not be sent. "
            "Check the mail settings and use "
            "Resend Code."
        )


    return render_template(
        "verify_email.html",
        email=email,
        full_name=full_name,
        error=error,
        success=success
    )


# =========================================================
# RESEND EMAIL VERIFICATION CODE
# =========================================================

@app.route(
    "/resend-verification",
    methods=["POST"]
)
def resend_verification():

    user_id = session.get(
        "pending_verification_user_id"
    )

    if not user_id:

        return redirect(
            url_for("login")
        )


    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            email,
            full_name,
            email_verified
        FROM users
        WHERE id = ?
        AND role = 'Student'
        """,
        (
            user_id,
        )
    )

    user = cursor.fetchone()


    if not user:

        connection.close()

        return redirect(
            url_for("register")
        )


    if user[2] == 1:

        connection.close()

        return redirect(
            url_for(
                "login",
                verified="1"
            )
        )


    cursor.execute(
        """
        SELECT last_sent_at
        FROM email_verification_codes
        WHERE user_id = ?
        """,
        (
            user_id,
        )
    )

    previous_code = (
        cursor.fetchone()
    )

    connection.close()


    if previous_code:

        seconds_since_last_send = (
            int(time.time())
            - previous_code[0]
        )

        if seconds_since_last_send < 60:

            wait_seconds = (
                60
                - seconds_since_last_send
            )

            return redirect(
                url_for(
                    "verify_email",
                    wait=wait_seconds
                )
            )


    email_sent = send_verification_email(
        user_id,
        user[0],
        user[1]
    )


    return redirect(
        url_for(
            "verify_email",
            sent=(
                "1"
                if email_sent
                else "0"
            )
        )
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    error = None
    success = None


    if request.args.get("registered") == "1":

        success = (
            "Account created successfully. "
            "You can now sign in."
        )


    if request.args.get("verified") == "1":

        success = (
            "Email verified successfully. "
            "You can now sign in."
        )


    if request.args.get("password_reset") == "1":

        success = (
            "Your password was changed successfully. "
            "You can now sign in."
        )


    # -----------------------------------------------------
    # USER ALREADY LOGGED IN
    # -----------------------------------------------------

    if session.get("logged_in"):

        if session.get("role") == "Student":

            return redirect(
                url_for(
                    "student_dashboard"
                )
            )

        elif session.get("role") == "Admin":

            return redirect(
                url_for(
                    "admin"
                )
            )

        elif session.get("role") == "Security Officer":

            return redirect(
                url_for(
                    "dashboard"
                )
            )


    # -----------------------------------------------------
    # LOGIN FORM SUBMITTED
    # -----------------------------------------------------

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )


        if not username or not password:

            error = (
                "Please enter your username and password."
            )

            return render_template(
                "login.html",
                error=error,
                success=success
            )


        connection = sqlite3.connect(
            DATABASE_PATH
        )

        cursor = connection.cursor()


        cursor.execute(
            """
            SELECT
                id,
                username,
                password,
                role,
                disabled,
                email,
                email_verified
            FROM users
            WHERE username = ?
            """,
            (
                username,
            )
        )


        user = cursor.fetchone()

        connection.close()


        if user:

            if user[4] == 1:

                error = (
                    "This account has been disabled. "
                    "Please contact an administrator."
                )

                return render_template(
                    "login.html",
                    error=error,
                    success=success
                )


            if check_password_hash(
                user[2],
                password
            ):

                # -----------------------------------------
                # STUDENT EMAIL MUST BE VERIFIED
                # -----------------------------------------

                if (
                    user[3] == "Student"
                    and user[5]
                    and user[6] == 0
                ):

                    session[
                        "pending_verification_user_id"
                    ] = user[0]

                    session[
                        "pending_verification_email"
                    ] = user[5]

                    return redirect(
                        url_for(
                            "verify_email"
                        )
                    )


                session["logged_in"] = True
                session["user_id"] = user[0]
                session["username"] = user[1]
                session["role"] = user[3]


                if user[3] == "Student":

                    return redirect(
                        url_for(
                            "student_dashboard"
                        )
                    )


                elif user[3] == "Admin":

                    return redirect(
                        url_for(
                            "admin"
                        )
                    )


                elif user[3] == "Security Officer":

                    return redirect(
                        url_for(
                            "dashboard"
                        )
                    )


                else:

                    session.clear()

                    error = (
                        "Your account does not have "
                        "a valid system role."
                    )

                    return render_template(
                        "login.html",
                        error=error,
                        success=success
                    )


        error = (
            "Incorrect username or password."
        )


    return render_template(
        "login.html",
        error=error,
        success=success
    )


# =========================================================
# FORGOT / RESET PASSWORD
# =========================================================

@app.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    error = None
    success = None

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, full_name, email, email_verified, disabled
            FROM users
            WHERE LOWER(email) = LOWER(?)
            """,
            (email,)
        )
        user = cursor.fetchone()
        connection.close()

        # Generic response avoids revealing whether an email is registered.
        success = (
            "If that email is linked to an active verified account, "
            "a 6-digit password reset code has been sent."
        )

        if user and user[3] == 1 and user[4] == 0:
            if send_password_reset_email(
                user[0],
                user[2],
                user[1] or "Student"
            ):
                session["password_reset_user_id"] = user[0]
                return redirect(url_for("reset_password", sent="1"))

    return render_template(
        "forgot_password.html",
        error=error,
        success=success
    )


@app.route(
    "/reset-password",
    methods=["GET", "POST"]
)
def reset_password():

    user_id = session.get("password_reset_user_id")

    if not user_id:
        return redirect(url_for("forgot_password"))

    error = None
    success = (
        "A 6-digit password reset code was sent to your email."
        if request.args.get("sent") == "1"
        else None
    )

    if request.method == "POST":
        code = request.form.get("code", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not code.isdigit() or len(code) != 6:
            error = "Please enter the 6-digit reset code."
        elif len(password) < 6:
            error = "Password must contain at least 6 characters."
        elif password != confirm_password:
            error = "The passwords do not match."
        else:
            connection = sqlite3.connect(DATABASE_PATH)
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT code_hash, expires_at
                FROM password_reset_codes
                WHERE user_id = ?
                """,
                (user_id,)
            )
            reset_code = cursor.fetchone()

            cursor.execute(
                "SELECT full_name, email FROM users WHERE id = ?",
                (user_id,)
            )
            user = cursor.fetchone()

            if not reset_code:
                error = "No password reset code was found. Request a new code."
            elif int(time.time()) > reset_code[1]:
                error = "That password reset code has expired. Request a new code."
            elif hash_verification_code(code) != reset_code[0]:
                error = "The password reset code is incorrect."
            else:
                cursor.execute(
                    "UPDATE users SET password = ? WHERE id = ?",
                    (generate_password_hash(password), user_id)
                )
                cursor.execute(
                    "DELETE FROM password_reset_codes WHERE user_id = ?",
                    (user_id,)
                )
                connection.commit()
                connection.close()
                session.pop("password_reset_user_id", None)

                if user and user[1]:
                    send_password_changed_email(
                        user[1],
                        user[0] or "Student"
                    )

                return redirect(url_for("login", password_reset="1"))

            connection.close()

    return render_template(
        "reset_password.html",
        error=error,
        success=success
    )


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@app.route("/student-dashboard")
def student_dashboard():

    if not login_required():

        return redirect(
            url_for("login")
        )


    # -----------------------------------------------------
    # ROLE PROTECTION
    # -----------------------------------------------------

    if session.get("role") != "Student":

        if session.get("role") == "Admin":

            return redirect(
                url_for("admin")
            )

        return redirect(
            url_for("dashboard")
        )


    user_id = session.get(
        "user_id"
    )


    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()


    # -----------------------------------------------------
    # MOST RECENT STUDENT REPORT
    # -----------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            incident_type,
            location,
            priority,
            status,
            date_reported
        FROM incidents
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (
        user_id,
    ))


    recent_report = (
        cursor.fetchone()
    )


    connection.close()


    return render_template(
        "student_dashboard.html",
        username=session.get(
            "username"
        ),
        role=session.get(
            "role"
        ),
        recent_report=recent_report
    )


# =========================================================
# STUDENT ACCOUNT
# =========================================================

@app.route("/account")
def account():

    if not login_required():
        return redirect(url_for("login"))

    if session.get("role") != "Student":
        if session.get("role") == "Admin":
            return redirect(url_for("admin"))
        return redirect(url_for("dashboard"))

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            full_name,
            student_number,
            email,
            email_verified,
            username,
            role
        FROM users
        WHERE id = ?
        """,
        (session.get("user_id"),)
    )

    profile = cursor.fetchone()
    connection.close()

    if not profile:
        session.clear()
        return redirect(url_for("login"))

    return render_template(
        "account.html",
        full_name=profile[0],
        student_number=profile[1],
        email=profile[2],
        email_verified=profile[3],
        username=profile[4],
        role=profile[5],
        email_changed=(request.args.get("email_changed") == "1")
    )


# =========================================================
# CHANGE STUDENT EMAIL
# =========================================================

@app.route(
    "/change-email",
    methods=["GET", "POST"]
)
def change_email():

    if not login_required() or session.get("role") != "Student":
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    error = None

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute(
        "SELECT full_name, email FROM users WHERE id = ?",
        (user_id,)
    )
    user = cursor.fetchone()
    connection.close()

    if not user:
        session.clear()
        return redirect(url_for("login"))

    if request.method == "POST":
        new_email = request.form.get("email", "").strip().lower()

        if (
            "@" not in new_email
            or "." not in new_email.split("@")[-1]
            or " " in new_email
        ):
            error = "Please enter a valid email address."
        elif new_email == (user[1] or "").lower():
            error = "That is already your current email address."
        else:
            connection = sqlite3.connect(DATABASE_PATH)
            cursor = connection.cursor()
            cursor.execute(
                "SELECT id FROM users WHERE LOWER(email) = LOWER(?) AND id != ?",
                (new_email, user_id)
            )
            exists = cursor.fetchone()
            connection.close()

            if exists:
                error = "That email address is already linked to another account."
            else:
                sent = send_email_change_code(
                    user_id,
                    new_email,
                    user[0] or session.get("username")
                )

                if sent:
                    session["pending_new_email"] = new_email
                    return redirect(url_for("verify_new_email", sent="1"))

                error = "The verification email could not be sent. Please try again."

    return render_template(
        "change_email.html",
        current_email=user[1],
        error=error
    )


@app.route(
    "/verify-new-email",
    methods=["GET", "POST"]
)
def verify_new_email():

    if not login_required() or session.get("role") != "Student":
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    error = None

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT new_email, code_hash, expires_at
        FROM email_change_codes
        WHERE user_id = ?
        """,
        (user_id,)
    )
    pending = cursor.fetchone()
    connection.close()

    if not pending:
        return redirect(url_for("change_email"))

    if request.method == "POST":
        code = request.form.get("code", "").strip()

        if not code.isdigit() or len(code) != 6:
            error = "Please enter the 6-digit verification code."
        elif int(time.time()) > pending[2]:
            error = "That verification code has expired. Start the email change again."
        elif hash_verification_code(code) != pending[1]:
            error = "The verification code is incorrect."
        else:
            connection = sqlite3.connect(DATABASE_PATH)
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    UPDATE users
                    SET email = ?, email_verified = 1
                    WHERE id = ?
                    """,
                    (pending[0], user_id)
                )
                cursor.execute(
                    "DELETE FROM email_change_codes WHERE user_id = ?",
                    (user_id,)
                )
                connection.commit()
            except sqlite3.IntegrityError:
                connection.rollback()
                connection.close()
                return render_template(
                    "verify_new_email.html",
                    email=pending[0],
                    error="That email address is already linked to another account."
                )
            connection.close()
            session.pop("pending_new_email", None)
            return redirect(url_for("account", email_changed="1"))

    return render_template(
        "verify_new_email.html",
        email=pending[0],
        error=error,
        success=(
            "A verification code was sent to your new email address."
            if request.args.get("sent") == "1"
            else None
        )
    )


# =========================================================
# REPORT INCIDENT
# =========================================================

@app.route(
    "/report",
    methods=["GET", "POST"]
)
def report_incident():

    # -----------------------------------------------------
    # LOGIN REQUIRED
    # -----------------------------------------------------

    if not login_required():

        return redirect(
            url_for("login")
        )


    # -----------------------------------------------------
    # STUDENT ONLY
    # -----------------------------------------------------

    if session.get("role") != "Student":

        if session.get("role") == "Admin":

            return redirect(
                url_for("admin")
            )

        return redirect(
            url_for("dashboard")
        )


    # -----------------------------------------------------
    # GET LOGGED-IN STUDENT PROFILE
    # -----------------------------------------------------

    user_id = session.get(
        "user_id"
    )


    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT
            full_name,
            student_number
        FROM users
        WHERE id = ?
        AND role = 'Student'
        """,
        (
            user_id,
        )
    )


    student_profile = (
        cursor.fetchone()
    )


    connection.close()


    # -----------------------------------------------------
    # CHECK STUDENT PROFILE
    # -----------------------------------------------------

    if not student_profile:

        session.clear()

        return redirect(
            url_for("login")
        )


    full_name = (
        student_profile[0] or ""
    ).strip()

    student_number = (
        student_profile[1] or ""
    ).strip()


    # -----------------------------------------------------
    # PROFILE MUST CONTAIN STUDENT DETAILS
    # -----------------------------------------------------
    #
    # Old Student accounts created before this feature
    # may not yet have a full name / student number.
    #
    # -----------------------------------------------------

    if (
        not full_name
        or not student_number
    ):

        return render_template(
            "report_incident.html",

            username=session.get(
                "username"
            ),

            role=session.get(
                "role"
            ),

            error=(
                "Your Student account does not yet have "
                "a full name and student number linked to it. "
                "Please use a Student account created with "
                "the new registration form."
            )
        )


    # -----------------------------------------------------
    # SUBMIT REPORT
    # -----------------------------------------------------

    if request.method == "POST":

        incident_type = request.form.get(
            "incident_type",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()


        # -------------------------------------------------
        # ANONYMOUS REPORTING
        # -------------------------------------------------

        anonymous_value = request.form.get(
            "anonymous"
        )


        if anonymous_value == "on":

            is_anonymous = 1

        else:

            is_anonymous = 0


        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if (
            not incident_type
            or not location
            or not description
        ):

            return render_template(
                "report_incident.html",

                username=session.get(
                    "username"
                ),

                role=session.get(
                    "role"
                ),

                error=(
                    "Please complete all required fields."
                )
            )


        # -------------------------------------------------
        # DETERMINE STORED REPORTER DETAILS
        # -------------------------------------------------

        if is_anonymous == 1:

            stored_full_name = (
                "Anonymous Reporter"
            )

            stored_student_number = (
                "Anonymous"
            )

        else:

            stored_full_name = (
                full_name
            )

            stored_student_number = (
                student_number
            )


        # -------------------------------------------------
        # CALCULATE PRIORITY
        # -------------------------------------------------

        priority = calculate_priority(
            incident_type
        )


        # -------------------------------------------------
        # SAVE REPORT
        # -------------------------------------------------

        connection = sqlite3.connect(
            DATABASE_PATH
        )

        cursor = connection.cursor()


        cursor.execute(
            """
            INSERT INTO incidents
            (
                user_id,
                full_name,
                student_number,
                incident_type,
                location,
                description,
                priority,
                status,
                is_anonymous,
                latitude,
                longitude
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,

                stored_full_name,

                stored_student_number,

                incident_type,

                location,

                description,

                priority,

                "Pending",

                is_anonymous,
                request.form.get("latitude") or None,
                request.form.get("longitude") or None
            )
        )


        incident_id = cursor.lastrowid

        connection.commit()

        # Optional evidence uploads (images, video, PDF/documents).
        upload_dir = os.path.join(BASE_DIR, "uploads", "evidence")
        os.makedirs(upload_dir, exist_ok=True)
        allowed_ext = {"png","jpg","jpeg","gif","webp","pdf","doc","docx","mp4","mov","avi"}
        for evidence_file in request.files.getlist("evidence"):
            if not evidence_file or not evidence_file.filename:
                continue
            safe_original = secure_filename(evidence_file.filename)
            ext = safe_original.rsplit(".", 1)[-1].lower() if "." in safe_original else ""
            if ext not in allowed_ext:
                continue
            stored_name = f"{incident_id}_{uuid.uuid4().hex}.{ext}"
            stored_path = os.path.join(upload_dir, stored_name)
            evidence_file.save(stored_path)
            cursor.execute("""INSERT INTO incident_evidence
                (incident_id,user_id,original_name,stored_name,mime_type,file_size)
                VALUES (?,?,?,?,?,?)""", (incident_id,user_id,safe_original,stored_name,evidence_file.mimetype,os.path.getsize(stored_path)))
        connection.commit()
        connection.close()

        create_notification(user_id, "Report received", f"Incident #{incident_id} was received with {priority} priority.", "INCIDENT", incident_id)
        audit_event("INCIDENT_CREATED", "incident", incident_id, f"priority={priority}; anonymous={is_anonymous}")

        send_incident_confirmation(
            user_id,
            incident_id,
            incident_type,
            location,
            priority,
            is_anonymous
        )

        if priority == "High":
            send_security_alert(
                incident_id,
                incident_type,
                location,
                priority
            )


        # -------------------------------------------------
        # GO TO MY REPORTS
        # -------------------------------------------------

        return redirect(
            url_for(
                "my_reports"
            )
        )


    # -----------------------------------------------------
    # DISPLAY REPORT PAGE
    # -----------------------------------------------------

    return render_template(
        "report_incident.html",

        username=session.get(
            "username"
        ),

        role=session.get(
            "role"
        )
    )

# =========================================================
# MY REPORTS
# =========================================================

@app.route("/my-reports")
def my_reports():

    if not login_required():

        return redirect(
            url_for("login")
        )


    if session.get("role") != "Student":

        if session.get("role") == "Admin":

            return redirect(
                url_for("admin")
            )

        return redirect(
            url_for("dashboard")
        )


    user_id = session.get(
        "user_id"
    )


    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()


    cursor.execute("""
        SELECT
            id,
            incident_type,
            location,
            description,
            priority,
            status,
            date_reported
        FROM incidents
        WHERE user_id = ?
        ORDER BY id DESC
    """, (
        user_id,
    ))


    reports = cursor.fetchall()


    connection.close()


    return render_template(
        "my_reports.html",
        reports=reports,
        incidents=reports,
        username=session.get(
            "username"
        ),
        role=session.get(
            "role"
        )
    )


# =========================================================
# CAMPUS SOS - DEDICATED EMERGENCY ALERTS + GPS
# =========================================================

@app.route("/sos", methods=["GET", "POST"])
def sos():
    if not login_required(): return redirect(url_for("login"))
    if session.get("role") != "Student":
        return redirect(url_for("admin" if session.get("role") == "Admin" else "dashboard"))
    if request.method == "POST":
        user_id=session.get("user_id")
        location=request.form.get("location","").strip()
        latitude=request.form.get("latitude","").strip() or None
        longitude=request.form.get("longitude","").strip() or None
        if not location and not (latitude and longitude):
            return render_template("sos.html", username=session.get("username"), role=session.get("role"), error="Allow GPS access or enter your location manually.")
        if not location and latitude and longitude:
            location=f"GPS: {float(latitude):.6f}, {float(longitude):.6f}"
        con=sqlite3.connect(DATABASE_PATH); cur=con.cursor()
        cur.execute("SELECT COALESCE(full_name,username), COALESCE(student_staff_number,student_number,username) FROM users WHERE id=?",(user_id,))
        profile=cur.fetchone() or (session.get("username"),session.get("username"))
        cur.execute("""INSERT INTO incidents(user_id,full_name,student_number,incident_type,location,description,priority,status,is_anonymous,latitude,longitude)
                       VALUES(?,?,?,?,?,?,?,?,0,?,?)""",(user_id,profile[0],profile[1],"Emergency SOS",location,"Emergency assistance requested.","High","Pending",latitude,longitude))
        incident_id=cur.lastrowid
        cur.execute("""INSERT INTO emergency_alerts(user_id,incident_id,location_text,latitude,longitude,status)
                       VALUES(?,?,?,?,?,'ACTIVE')""",(user_id,incident_id,location,latitude,longitude))
        emergency_id=cur.lastrowid; con.commit(); con.close()
        create_notification(user_id,"SOS received",f"Emergency alert #{emergency_id} is ACTIVE. Security has been alerted.","EMERGENCY",emergency_id)
        notify_security_users("New emergency SOS",f"Emergency #{emergency_id} at {location}. Open Emergency Control to assign an officer.","EMERGENCY",emergency_id)
        audit_event("SOS_CREATED","emergency",emergency_id,location)
        send_sos_confirmation(user_id,incident_id); send_security_alert(incident_id,"Emergency SOS",location,"High")
        return render_template("sos_success.html",incident_id=incident_id,location=location,username=session.get("username"))
    return render_template("sos.html",username=session.get("username"),role=session.get("role"))

# =========================================================
# EMERGENCY CONTACTS
# =========================================================

@app.route("/emergency-contacts")
def emergency_contacts():

    if not login_required():

        return redirect(
            url_for("login")
        )


    return render_template(
        "emergency_contacts.html",
        username=session.get(
            "username"
        ),
        role=session.get(
            "role"
        )
    )


# =========================================================
# SECURITY DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if not login_required():

        return redirect(
            url_for("login")
        )


    # -----------------------------------------------------
    # ROLE PROTECTION
    # -----------------------------------------------------

    if session.get("role") == "Student":

        return redirect(
            url_for(
                "student_dashboard"
            )
        )


    if session.get("role") == "Admin":

        return redirect(
            url_for("admin")
        )


    if session.get("role") != "Security Officer":

        return redirect(
            url_for("login")
        )


    # -----------------------------------------------------
    # FILTER VALUES
    # -----------------------------------------------------

    search = request.args.get(
        "search",
        ""
    ).strip()

    incident_type = request.args.get(
        "incident_type",
        ""
    ).strip()

    priority = request.args.get(
        "priority",
        ""
    ).strip()

    status = request.args.get(
        "status",
        ""
    ).strip()


    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()


    # =====================================================
    # INCIDENT QUERY
    # =====================================================

    query = """
        SELECT
    id,
    full_name,
    student_number,
    incident_type,
    location,
    description,
    priority,
    status,
    date_reported,
    is_anonymous
FROM incidents
WHERE 1 = 1
    """


    parameters = []


    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    if search:

        query += """
            AND
            (
                full_name LIKE ?
                OR student_number LIKE ?
                OR incident_type LIKE ?
                OR location LIKE ?
                OR description LIKE ?
            )
        """

        search_value = (
            "%" + search + "%"
        )

        parameters.extend([
            search_value,
            search_value,
            search_value,
            search_value,
            search_value
        ])


    # -----------------------------------------------------
    # INCIDENT TYPE FILTER
    # -----------------------------------------------------

    if incident_type:

        query += """
            AND incident_type = ?
        """

        parameters.append(
            incident_type
        )


    # -----------------------------------------------------
    # PRIORITY FILTER
    # -----------------------------------------------------

    if priority:

        query += """
            AND priority = ?
        """

        parameters.append(
            priority
        )


    # -----------------------------------------------------
    # STATUS FILTER
    # -----------------------------------------------------

    if status:

        query += """
            AND status = ?
        """

        parameters.append(
            status
        )


    # -----------------------------------------------------
    # HIGH PRIORITY FIRST
    # -----------------------------------------------------

    query += """
        ORDER BY

            CASE priority

                WHEN 'High'
                    THEN 1

                WHEN 'Medium'
                    THEN 2

                WHEN 'Low'
                    THEN 3

                ELSE 4

            END,

            id DESC
    """


    cursor.execute(
        query,
        parameters
    )


    incidents = cursor.fetchall()


    # =====================================================
    # DASHBOARD STATISTICS
    # =====================================================

    cursor.execute("""
        SELECT COUNT(*)
        FROM incidents
    """)

    total_incidents = (
        cursor.fetchone()[0]
    )


    cursor.execute("""
        SELECT COUNT(*)
        FROM incidents
        WHERE status = 'Pending'
    """)

    pending_incidents = (
        cursor.fetchone()[0]
    )


    cursor.execute("""
        SELECT COUNT(*)
        FROM incidents
        WHERE status = 'In Progress'
    """)

    in_progress_incidents = (
        cursor.fetchone()[0]
    )


    cursor.execute("""
        SELECT COUNT(*)
        FROM incidents
        WHERE status = 'Resolved'
    """)

    resolved_incidents = (
        cursor.fetchone()[0]
    )


    cursor.execute("""
        SELECT COUNT(*)
        FROM incidents
        WHERE priority = 'High'
    """)

    high_priority_incidents = (
        cursor.fetchone()[0]
    )


    connection.close()


    return render_template(
        "dashboard.html",

        incidents=incidents,

        username=session.get(
            "username"
        ),

        role=session.get(
            "role"
        ),

        total_incidents=(
            total_incidents
        ),

        pending_incidents=(
            pending_incidents
        ),

        in_progress_incidents=(
            in_progress_incidents
        ),

        resolved_incidents=(
            resolved_incidents
        ),

        high_priority_incidents=(
            high_priority_incidents
        ),

        search=search,

        selected_incident_type=(
            incident_type
        ),

        selected_priority=(
            priority
        ),

        selected_status=(
            status
        )
    )


# =========================================================
# UPDATE INCIDENT STATUS
# =========================================================

@app.route(
    "/update-status/<int:incident_id>",
    methods=["POST"]
)
def update_status(incident_id):

    if not login_required():
        return redirect(url_for("login"))

    if not security_required():
        if session.get("role") == "Admin":
            return redirect(url_for("admin"))
        if session.get("role") == "Student":
            return redirect(url_for("student_dashboard"))
        return ("Access denied.", 403)

    new_status = request.form.get("status", "")
    allowed_statuses = ["Pending", "In Progress", "Resolved"]

    if new_status not in allowed_statuses:
        return ("Invalid status.", 400)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT user_id, incident_type, status
        FROM incidents
        WHERE id = ?
        """,
        (incident_id,)
    )
    incident = cursor.fetchone()

    if not incident:
        connection.close()
        return ("Incident not found.", 404)

    cursor.execute(
        "UPDATE incidents SET status = ? WHERE id = ?",
        (new_status, incident_id)
    )
    connection.commit()
    connection.close()

    if incident[2] != new_status:
        send_status_update_email(incident[0], incident_id, incident[1], new_status)
        create_notification(incident[0], "Incident status updated", f"Incident #{incident_id} is now {new_status}.", "STATUS", incident_id)
        audit_event("INCIDENT_STATUS_CHANGED", "incident", incident_id, f"{incident[2]} -> {new_status}")

    return redirect(url_for("dashboard"))


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin():

    if not login_required():

        return redirect(
            url_for("login")
        )


    if not admin_required():

        if session.get("role") == "Student":

            return redirect(
                url_for(
                    "student_dashboard"
                )
            )

        return redirect(
            url_for("dashboard")
        )


    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()


    # -----------------------------------------------------
    # GET ALL USERS
    # -----------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            username,
            role,
            disabled,
            email,
            email_verified
        FROM users
        ORDER BY id ASC
    """)


    users = cursor.fetchall()


    connection.close()


    # -----------------------------------------------------
    # STATISTICS
    # -----------------------------------------------------

    total_users = len(
        users
    )


    student_count = sum(
        1
        for user in users
        if user[2] == "Student"
    )


    security_count = sum(
        1
        for user in users
        if user[2] == "Security Officer"
    )


    admin_count = sum(
        1
        for user in users
        if user[2] == "Admin"
    )


    return render_template(
        "admin.html",

        users=users,

        username=session.get(
            "username"
        ),

        role=session.get(
            "role"
        ),

        current_user_id=session.get(
            "user_id"
        ),

        total_users=total_users,

        student_count=student_count,

        security_count=security_count,

        admin_count=admin_count
    )


# =========================================================
# ADMIN - ADD USER
# =========================================================

@app.route(
    "/admin/add-user",
    methods=["POST"]
)
def add_user():

    if not admin_required():

        return (
            "Access denied.",
            403
        )


    username = request.form.get(
        "username",
        ""
    ).strip()


    password = request.form.get(
        "password",
        ""
    )


    role = request.form.get(
        "role",
        ""
    ).strip()


    email = request.form.get(
        "email",
        ""
    ).strip().lower()


    allowed_roles = [
        "Student",
        "Security Officer",
        "Admin"
    ]


    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not username:

        return redirect(
            url_for("admin")
        )


    if len(password) < 6:

        return redirect(
            url_for("admin")
        )


    if role not in allowed_roles:

        return redirect(
            url_for("admin")
        )


    if not email or "@" not in email or "." not in email.split("@")[-1]:

        return redirect(
            url_for("admin")
        )


    password_hash = (
        generate_password_hash(
            password
        )
    )


    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()


    try:

        cursor.execute("""
            INSERT INTO users
            (
                username,
                email,
                password,
                role,
                disabled,
                email_verified
            )
            VALUES (?, ?, ?, ?, 0, 1)
        """, (
            username,
            email,
            password_hash,
            role
        ))


        connection.commit()


    except sqlite3.IntegrityError:

        # Username already exists
        pass


    finally:

        connection.close()


    return redirect(
        url_for("admin")
    )


# =========================================================
# ADMIN - UPDATE USER EMAIL
# =========================================================

@app.route(
    "/admin/update-email/<int:user_id>",
    methods=["POST"]
)
def admin_update_user_email(user_id):

    if not admin_required():
        return ("Access denied.", 403)

    email = request.form.get("email", "").strip().lower()

    if not email or "@" not in email or "." not in email.split("@")[-1]:
        return redirect(url_for("admin"))

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE users
            SET email = ?, email_verified = 1
            WHERE id = ?
            """,
            (email, user_id)
        )
        connection.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        connection.close()

    return redirect(url_for("admin"))


# =========================================================
# ADMIN - CHANGE USER ROLE
# =========================================================

@app.route(
    "/admin/change-role/<int:user_id>",
    methods=["POST"]
)
def change_user_role(user_id):

    if not admin_required():

        return (
            "Access denied.",
            403
        )


    # -----------------------------------------------------
    # PROTECT CURRENT ADMIN
    # -----------------------------------------------------

    if user_id == session.get(
        "user_id"
    ):

        return redirect(
            url_for("admin")
        )


    new_role = request.form.get(
        "role",
        ""
    )


    allowed_roles = [
        "Student",
        "Security Officer",
        "Admin"
    ]


    if new_role not in allowed_roles:

        return redirect(
            url_for("admin")
        )


    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()


    cursor.execute("""
        UPDATE users
        SET role = ?
        WHERE id = ?
    """, (
        new_role,
        user_id
    ))


    connection.commit()

    connection.close()


    return redirect(
        url_for("admin")
    )


# =========================================================
# ADMIN - RESET PASSWORD
# =========================================================

@app.route(
    "/admin/reset-password/<int:user_id>",
    methods=["POST"]
)
def reset_user_password(user_id):

    if not admin_required():
        return ("Access denied.", 403)

    new_password = request.form.get("new_password", "")

    if len(new_password) < 6:
        return redirect(url_for("admin"))

    password_hash = generate_password_hash(new_password)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT full_name, email, email_verified FROM users WHERE id = ?",
        (user_id,)
    )
    user = cursor.fetchone()

    cursor.execute(
        "UPDATE users SET password = ? WHERE id = ?",
        (password_hash, user_id)
    )
    connection.commit()
    connection.close()

    if user and user[1] and user[2] == 1:
        send_password_changed_email(
            user[1],
            user[0] or "UFH Security user"
        )

    return redirect(url_for("admin"))


# =========================================================
# ADMIN - ENABLE / DISABLE USER
# =========================================================

@app.route(
    "/admin/toggle-user/<int:user_id>",
    methods=["POST"]
)
def toggle_user(user_id):

    if not admin_required():
        return ("Access denied.", 403)

    if user_id == session.get("user_id"):
        return redirect(url_for("admin"))

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT disabled, full_name, email, email_verified
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    )
    user = cursor.fetchone()

    if user:
        new_status = 0 if user[0] == 1 else 1
        cursor.execute(
            "UPDATE users SET disabled = ? WHERE id = ?",
            (new_status, user_id)
        )
        connection.commit()
    else:
        new_status = None

    connection.close()

    if user and user[2] and user[3] == 1:
        state = "disabled" if new_status == 1 else "enabled"
        send_system_email(
            f"UFH Security - Account {state.title()}",
            [user[2]],
            f"""Hello {user[1] or 'UFH Security user'},

Your UFH Campus Security account has been {state} by an administrator.

If you have questions about this change, please contact the system administrator or Campus Security.

UFH Campus Security Management System
Alice Campus
"""
        )

    return redirect(url_for("admin"))


# =========================================================
# ADMIN - DELETE USER
# =========================================================

@app.route(
    "/admin/delete-user/<int:user_id>",
    methods=["POST"]
)
def delete_user(user_id):

    if not admin_required():

        return (
            "Access denied.",
            403
        )


    # -----------------------------------------------------
    # ADMIN CANNOT DELETE THEIR OWN ACCOUNT
    # -----------------------------------------------------

    if user_id == session.get(
        "user_id"
    ):

        return redirect(
            url_for("admin")
        )


    connection = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = connection.cursor()


    # -----------------------------------------------------
    # KEEP INCIDENT RECORDS
    # Remove link to account before deleting account
    # -----------------------------------------------------

    cursor.execute("""
        UPDATE incidents
        SET user_id = NULL
        WHERE user_id = ?
    """, (
        user_id,
    ))


    cursor.execute("""
        DELETE FROM users
        WHERE id = ?
    """, (
        user_id,
    ))


    connection.commit()

    connection.close()


    return redirect(
        url_for("admin")
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()


    return redirect(
        url_for("home")
    )



# =========================================================
# INTEGRATED FEATURES: NOTIFICATIONS, OFFICERS, EMERGENCIES,
# EVIDENCE, MAP, ANALYTICS AND AUDIT LOGGING
# =========================================================

def db_rows(query, params=()):
    con=sqlite3.connect(DATABASE_PATH); con.row_factory=sqlite3.Row
    rows=con.execute(query,params).fetchall(); con.close(); return rows

def create_notification(user_id,title,message,category="GENERAL",related_id=None):
    if not user_id: return
    con=sqlite3.connect(DATABASE_PATH); con.execute("INSERT INTO notifications(user_id,title,message,category,related_id) VALUES(?,?,?,?,?)",(user_id,title,message,category,related_id)); con.commit(); con.close()

def notify_security_users(title,message,category="GENERAL",related_id=None):
    for row in db_rows("SELECT id FROM users WHERE role='Security Officer' AND disabled=0"):
        create_notification(row["id"],title,message,category,related_id)

def audit_event(action,entity_type=None,entity_id=None,details=None):
    try:
        con=sqlite3.connect(DATABASE_PATH); con.execute("INSERT INTO audit_logs(user_id,username,action,entity_type,entity_id,details,ip_address) VALUES(?,?,?,?,?,?,?)",(session.get("user_id"),session.get("username"),action,entity_type,entity_id,details,request.remote_addr)); con.commit(); con.close()
    except Exception: pass

def haversine_km(lat1,lon1,lat2,lon2):
    r=6371.0; p1=math.radians(lat1); p2=math.radians(lat2); dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return r*2*math.atan2(math.sqrt(a),math.sqrt(1-a))

@app.context_processor
def notification_context():
    count=0
    if session.get("user_id"):
        rows=db_rows("SELECT COUNT(*) c FROM notifications WHERE user_id=? AND is_read=0",(session["user_id"],)); count=rows[0]["c"] if rows else 0
    return {"notification_unread_count":count}

@app.route("/notifications")
def notifications_page():
    if not login_required(): return redirect(url_for("login"))
    notes=db_rows("SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 100",(session["user_id"],))
    return render_template("notifications.html",notifications=notes,username=session.get("username"),role=session.get("role"))

@app.route("/notifications/read-all",methods=["POST"])
def notifications_read_all():
    if not login_required(): return redirect(url_for("login"))
    con=sqlite3.connect(DATABASE_PATH); con.execute("UPDATE notifications SET is_read=1 WHERE user_id=?",(session["user_id"],)); con.commit(); con.close(); return redirect(url_for("notifications_page"))

@app.route("/security/officer-status",methods=["GET","POST"])
def officer_status():
    if not security_required(): return ("Access denied",403)
    con=sqlite3.connect(DATABASE_PATH); cur=con.cursor(); cur.execute("INSERT OR IGNORE INTO security_officers(user_id) VALUES(?)",(session["user_id"],))
    if request.method=="POST":
        availability=request.form.get("availability","OFF_DUTY")
        if availability not in {"AVAILABLE","BUSY","OFF_DUTY"}: availability="OFF_DUTY"
        lat=request.form.get("latitude") or None; lon=request.form.get("longitude") or None
        cur.execute("UPDATE security_officers SET availability=?,latitude=?,longitude=?,location_updated_at=CURRENT_TIMESTAMP WHERE user_id=?",(availability,lat,lon,session["user_id"])); con.commit(); audit_event("OFFICER_STATUS_CHANGED","officer",session["user_id"],availability)
    row=cur.execute("SELECT * FROM security_officers WHERE user_id=?",(session["user_id"],)).fetchone(); con.close()
    return render_template("officer_status.html",officer=row,username=session.get("username"),role=session.get("role"))

@app.route("/security/emergencies")
def emergency_control():
    if not security_required(): return ("Access denied",403)
    emergencies=db_rows("""SELECT e.*,u.username,u.full_name,so.user_id officer_user_id,ou.username officer_username
        FROM emergency_alerts e JOIN users u ON u.id=e.user_id
        LEFT JOIN security_officers so ON so.id=e.assigned_officer_id LEFT JOIN users ou ON ou.id=so.user_id
        ORDER BY CASE e.status WHEN 'ACTIVE' THEN 1 WHEN 'ASSIGNED' THEN 2 WHEN 'RESPONDING' THEN 3 ELSE 4 END,e.id DESC""")
    officers=db_rows("""SELECT so.*,u.username,u.full_name FROM security_officers so JOIN users u ON u.id=so.user_id WHERE u.disabled=0 ORDER BY so.availability,u.username""")
    enriched=[]
    for e in emergencies:
        d=dict(e); candidates=[]
        if e["latitude"] is not None and e["longitude"] is not None:
            for o in officers:
                if o["availability"]=="AVAILABLE" and o["latitude"] is not None and o["longitude"] is not None:
                    candidates.append((haversine_km(e["latitude"],e["longitude"],o["latitude"],o["longitude"]),dict(o)))
        candidates.sort(key=lambda x:x[0]); d["nearest"]=[{"distance":round(x[0],2),**x[1]} for x in candidates[:5]]; enriched.append(d)
    return render_template("emergencies.html",emergencies=enriched,officers=officers,username=session.get("username"),role=session.get("role"))

@app.route("/security/emergency/<int:emergency_id>/assign",methods=["POST"])
def assign_emergency(emergency_id):
    if not security_required(): return ("Access denied",403)
    officer_id=request.form.get("officer_id",type=int)
    con=sqlite3.connect(DATABASE_PATH); cur=con.cursor(); cur.execute("SELECT user_id FROM security_officers WHERE id=? AND availability='AVAILABLE'",(officer_id,)); off=cur.fetchone()
    if off:
        cur.execute("SELECT user_id, incident_id FROM emergency_alerts WHERE id=? AND status='ACTIVE'",(emergency_id,)); emergency=cur.fetchone()
        if emergency:
            cur.execute("UPDATE emergency_alerts SET assigned_officer_id=?,status='ASSIGNED',assigned_at=CURRENT_TIMESTAMP WHERE id=?",(officer_id,emergency_id))
            cur.execute("UPDATE security_officers SET availability='BUSY' WHERE id=?",(officer_id,))
            if emergency[1]: cur.execute("UPDATE incidents SET status='In Progress' WHERE id=?",(emergency[1],))
            con.commit()
            create_notification(off[0],"Emergency assigned",f"Emergency #{emergency_id} has been assigned to you.","EMERGENCY",emergency_id)
            create_notification(emergency[0],"Officer assigned",f"A security officer has been assigned to emergency #{emergency_id}.","EMERGENCY",emergency_id)
            audit_event("OFFICER_ASSIGNED","emergency",emergency_id,f"officer_id={officer_id}")
    con.close(); return redirect(url_for("emergency_control"))

@app.route("/security/emergency/<int:emergency_id>/status",methods=["POST"])
def emergency_status(emergency_id):
    if not security_required(): return ("Access denied",403)
    status=request.form.get("status","")
    if status not in {"RESPONDING","RESOLVED"}: return ("Invalid status",400)
    con=sqlite3.connect(DATABASE_PATH); cur=con.cursor(); cur.execute("SELECT e.user_id,e.assigned_officer_id,e.incident_id,so.user_id FROM emergency_alerts e LEFT JOIN security_officers so ON so.id=e.assigned_officer_id WHERE e.id=?",(emergency_id,)); e=cur.fetchone()
    if not e: con.close(); return ("Not found",404)
    if not e[1]: con.close(); return ("Assign an officer first",400)
    if e[3] != session.get("user_id"): con.close(); return ("Only the assigned officer can update this emergency",403)
    stamp="responding_at" if status=="RESPONDING" else "resolved_at"
    cur.execute(f"UPDATE emergency_alerts SET status=?,{stamp}=CURRENT_TIMESTAMP WHERE id=?",(status,emergency_id))
    if e[2]: cur.execute("UPDATE incidents SET status=? WHERE id=?",("Resolved" if status=="RESOLVED" else "In Progress",e[2]))
    if status=="RESOLVED": cur.execute("UPDATE security_officers SET availability='AVAILABLE' WHERE id=?",(e[1],))
    con.commit(); con.close()
    create_notification(e[0],"Emergency update",f"Emergency #{emergency_id} is now {status}.","EMERGENCY",emergency_id)
    audit_event("EMERGENCY_STATUS_CHANGED","emergency",emergency_id,status)
    return redirect(url_for("emergency_control"))

@app.route("/evidence/<int:evidence_id>")
def evidence_file(evidence_id):
    if not login_required(): return redirect(url_for("login"))
    rows=db_rows("SELECT * FROM incident_evidence WHERE id=?",(evidence_id,))
    if not rows: return ("Not found",404)
    e=rows[0]
    if session.get("role")=="Student":
        own=db_rows("SELECT id FROM incidents WHERE id=? AND user_id=?",(e["incident_id"],session["user_id"]))
        if not own: return ("Access denied",403)
    return send_from_directory(os.path.join(BASE_DIR,"uploads","evidence"),e["stored_name"],as_attachment=True,download_name=e["original_name"])

@app.route("/campus-map")
def campus_map():
    if not login_required(): return redirect(url_for("login"))
    if session.get("role") == "Student":
        incidents=db_rows("SELECT id,incident_type,location,priority,status,latitude,longitude,date_reported FROM incidents WHERE user_id=? AND latitude IS NOT NULL AND longitude IS NOT NULL ORDER BY id DESC LIMIT 250",(session["user_id"],))
        emergencies=db_rows("SELECT id,location_text,status,latitude,longitude,created_at FROM emergency_alerts WHERE user_id=? AND latitude IS NOT NULL AND longitude IS NOT NULL ORDER BY id DESC LIMIT 100",(session["user_id"],))
    else:
        incidents=db_rows("SELECT id,incident_type,location,priority,status,latitude,longitude,date_reported FROM incidents WHERE latitude IS NOT NULL AND longitude IS NOT NULL ORDER BY id DESC LIMIT 250")
        emergencies=db_rows("SELECT id,location_text,status,latitude,longitude,created_at FROM emergency_alerts WHERE latitude IS NOT NULL AND longitude IS NOT NULL ORDER BY id DESC LIMIT 100")
    locations=db_rows("SELECT * FROM campus_locations ORDER BY name")
    return render_template("campus_map.html",incidents=[dict(x) for x in incidents],emergencies=[dict(x) for x in emergencies],locations=[dict(x) for x in locations],username=session.get("username"),role=session.get("role"))

@app.route("/admin/analytics")
def admin_analytics():
    if not admin_required(): return ("Access denied",403)
    by_type=db_rows("SELECT incident_type label,COUNT(*) value FROM incidents GROUP BY incident_type ORDER BY value DESC")
    by_location=db_rows("SELECT location label,COUNT(*) value FROM incidents GROUP BY location ORDER BY value DESC LIMIT 10")
    by_priority=db_rows("SELECT priority label,COUNT(*) value FROM incidents GROUP BY priority")
    by_status=db_rows("SELECT status label,COUNT(*) value FROM incidents GROUP BY status")
    emergencies=db_rows("SELECT status label,COUNT(*) value FROM emergency_alerts GROUP BY status")
    return render_template("analytics.html",by_type=by_type,by_location=by_location,by_priority=by_priority,by_status=by_status,emergency_stats=emergencies,username=session.get("username"),role=session.get("role"))

@app.route("/admin/audit-logs")
def audit_logs():
    if not admin_required(): return ("Access denied",403)
    logs=db_rows("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 300")
    return render_template("audit_logs.html",logs=logs,username=session.get("username"),role=session.get("role"))


@app.route("/account/profile", methods=["GET","POST"])
def edit_profile():
    if not login_required(): return redirect(url_for("login"))
    con=sqlite3.connect(DATABASE_PATH); con.row_factory=sqlite3.Row; cur=con.cursor()
    if request.method=="POST":
        first=request.form.get("first_name","").strip(); last=request.form.get("last_name","").strip(); number=request.form.get("student_staff_number","").strip().upper(); phone=request.form.get("phone_number","").strip()
        if not first or not last or not number:
            profile=cur.execute("SELECT * FROM users WHERE id=?",(session["user_id"],)).fetchone(); con.close(); return render_template("edit_profile.html",profile=profile,error="First name, last name and student/staff number are required.")
        try:
            cur.execute("UPDATE users SET first_name=?,last_name=?,full_name=?,student_staff_number=?,student_number=?,phone_number=? WHERE id=?",(first,last,(first+' '+last).strip(),number,number,phone,session["user_id"])); con.commit(); audit_event("PROFILE_UPDATED","user",session["user_id"],"Profile details updated")
        except sqlite3.IntegrityError:
            profile=cur.execute("SELECT * FROM users WHERE id=?",(session["user_id"],)).fetchone(); con.close(); return render_template("edit_profile.html",profile=profile,error="That student/staff number is already in use.")
    profile=cur.execute("SELECT * FROM users WHERE id=?",(session["user_id"],)).fetchone(); con.close(); return render_template("edit_profile.html",profile=profile,success="Profile saved." if request.method=="POST" else None)

@app.route("/incident/<int:incident_id>/evidence")
def incident_evidence(incident_id):
    if not login_required(): return redirect(url_for("login"))
    if session.get("role")=="Student" and not db_rows("SELECT id FROM incidents WHERE id=? AND user_id=?",(incident_id,session["user_id"])): return ("Access denied",403)
    files=db_rows("SELECT * FROM incident_evidence WHERE incident_id=? ORDER BY id DESC",(incident_id,))
    return render_template("incident_evidence.html",files=files,incident_id=incident_id,username=session.get("username"),role=session.get("role"))

# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    )