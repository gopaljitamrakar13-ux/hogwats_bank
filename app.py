from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS


app = Flask(__name__)
app.secret_key = "hogwarts_secret_key_123"
CORS(app)

# ================= DATABASE CONNECTION =================
import os
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set!")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# ================= HOME =================
@app.route("/")
def home():
    return render_template("index2.html")


# ================= CREATE ACCOUNT =================
@app.route("/create_account", methods=["POST"])
def create_account():
    try:
        data = request.json
        name = data["name"]
        email = data["email"]
        password = data["password"]
        phone = data["phone"]

        cursor.execute("""
            INSERT INTO users (name, email, password, phone, balance, loan_taken, loan_amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (name, email, password, phone, 50000, False, 0))

        conn.commit()

        return jsonify({"success": True, "message": "Account Created Successfully ✅"})

 
    except Exception as e:
        conn.rollback()   # VERY IMPORTANT
        return jsonify({"success": False, "error": str(e)}), 500


# ================= LOGIN =================

    
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.json
        email = data["email"]
        password = data["password"]

        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cursor.fetchone()

        if user:
            session["user_id"] = user["id"]
            session["user_email"] = user["email"]
            return jsonify({"success": True, "message": "Login Successful ✅"})
        else:
            return jsonify({"success": False, "message": "Invalid Credentials ❌"})

    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    
@app.route("/forgot_password", methods=["POST"])
def forgot_password():

    data = request.json
    email = data["email"]

    cursor.execute("SELECT * FROM users WHERE email=%s",(email,))
    user = cursor.fetchone()

    if user:
        return jsonify({"message":"Password Reset Request Has Been Sent To Your Email.✅"})
    else:
        return jsonify({"message":"Email not found ❌"})
    
    user = cursor.fetchone()




# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"})


# ================= USER DETAILS =================
@app.route("/user_details")
def user_details():
    if "user_email" not in session:
        return jsonify({"message": "Please login first ❌"}), 401

    email = session["user_email"]

    cursor.execute("""
        SELECT name, email, phone, balance, loan_taken, loan_amount
        FROM users WHERE email=%s
    """, (email,))
    user = cursor.fetchone()

    if user:
        return jsonify(user)
    else:
        return jsonify({"message": "User not found"})


# ================= APPLY LOAN =================
@app.route("/apply_loan", methods=["POST"])
def apply_loan():
    if "user_email" not in session:
        return jsonify({"message": "Please login first ❌"}), 401

    data = request.json
    amount = int(data["amount"])
    email = session["user_email"]

    if amount < 5000:
        return jsonify({"message": "❌ Minimum loan amount is ₹5,000"})

    if amount <= 50000:
        status_message = "Loan Approved ✅"
    else:
        status_message = "Loan Under Review ⏳"

    cursor.execute("""
        UPDATE users
        SET loan_taken = TRUE,
            loan_amount = %s,
            balance = balance + %s
        WHERE email = %s
    """, (amount, amount, email))

    conn.commit()

    return jsonify({"message": status_message})


# ================= TRANSFER MONEY =================
@app.route("/transfer", methods=["POST"])
def transfer():
    if "user_email" not in session:
        return jsonify({"message": "Please login first ❌"}), 401

    data = request.json
    amount = int(data["amount"])
    sender_email = session["user_email"]

    cursor.execute("SELECT balance FROM users WHERE email=%s", (sender_email,))
    user = cursor.fetchone()

    if not user:
        return jsonify({"message": "User not found"})

    if user["balance"] < amount:
        return jsonify({"message": "❌ Insufficient Balance"})

    cursor.execute("""
        UPDATE users
        SET balance = balance - %s
        WHERE email = %s
    """, (amount, sender_email))

    cursor.execute("""
        INSERT INTO transactions (email, type, amount)
        VALUES (%s, %s, %s)
    """, (sender_email, "Sent", amount))

    conn.commit()

    return jsonify({"message": "Money Transferred Successfully ✅"})


# ================= UPDATE PROFILE =================
@app.route("/update_profile", methods=["POST"])
def update_profile():
    if "user_email" not in session:
        return jsonify({"message": "Please login first ❌"}), 401

    data = request.get_json()

    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    new_email = data.get("email", "").strip()
    old_email = session["user_email"]

    # ✅ Validate empty fields
    if not name or not phone or not new_email:
        return jsonify({"message": "All fields are required ❌"}), 400

    # ✅ Validate phone
    if not phone.isdigit() or len(phone) != 10:
        return jsonify({"message": "Phone must be 10 digits ❌"}), 400

    # ✅ Check if email already exists (but allow same email)
    cursor.execute("SELECT email FROM users WHERE email=%s", (new_email,))
    existing_user = cursor.fetchone()

    if existing_user and new_email != old_email:
        return jsonify({"message": "Email already exists ❌"}), 400

    # ✅ Update profile
    cursor.execute("""
        UPDATE users
        SET name=%s, phone=%s, email=%s
        WHERE email=%s
    """, (name, phone, new_email, old_email))

    conn.commit()

    # ✅ Update session email
    session["user_email"] = new_email

    return jsonify({"message": "Profile Updated Successfully ✅"}), 200


# ================= TRANSACTION HISTORY =================
@app.route("/transactions")
def get_transactions():
    if "user_email" not in session:
        return jsonify({"message": "Please login first ❌"}), 401

    email = session["user_email"]

    cursor.execute("""
        SELECT type, amount
        FROM transactions
        WHERE email=%s
    """, (email,))

    transactions = cursor.fetchall()
    return jsonify(transactions)


if __name__ == "__main__":
    app.run(debug=True)