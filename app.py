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

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

import sqlite3
import os
import hashlib
import secrets
import time
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

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

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
                    student_number,
                    email,
                    email_verified,
                    password,
                    role,
                    disabled
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    full_name,
                    student_number,
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
                is_anonymous
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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

                is_anonymous
            )
        )


        incident_id = cursor.lastrowid

        connection.commit()

        connection.close()

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
# CAMPUS SOS
# =========================================================

@app.route(
    "/sos",
    methods=["GET", "POST"]
)
def sos():

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


    if request.method == "POST":

        user_id = session.get(
            "user_id"
        )

        username = session.get(
            "username"
        )


        location = request.form.get(
            "location",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()


        if not location:

            return render_template(
                "sos.html",
                username=username,
                role=session.get(
                    "role"
                ),
                error=(
                    "Please provide your location."
                )
            )


        if not description:

            description = (
                "Emergency assistance requested."
            )


        connection = sqlite3.connect(
            DATABASE_PATH
        )

        cursor = connection.cursor()


        cursor.execute("""
            INSERT INTO incidents
            (
                user_id,
                full_name,
                student_number,
                incident_type,
                location,
                description,
                priority,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            username,
            username,
            "Emergency SOS",
            location,
            description,
            "High",
            "Pending"
        ))


        connection.commit()

        incident_id = (
            cursor.lastrowid
        )


        connection.close()

        send_sos_confirmation(
            user_id,
            incident_id
        )

        send_security_alert(
            incident_id,
            "Emergency SOS",
            location,
            "High"
        )


        return render_template(
            "sos_success.html",
            incident_id=incident_id,
            location=location,
            username=username
        )


    return render_template(
        "sos.html",
        username=session.get(
            "username"
        ),
        role=session.get(
            "role"
        )
    )


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
        send_status_update_email(
            incident[0],
            incident_id,
            incident[1],
            new_status
        )

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
# START APPLICATION
# =========================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    )