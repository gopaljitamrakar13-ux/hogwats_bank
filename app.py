from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS

import random

def generate_account_number():
    while True:
        acc = str(random.randint(100000000000, 999999999999))
        cursor.execute("SELECT id FROM users WHERE account_number=%s", (acc,))
        if not cursor.fetchone():
            return acc


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

        # ✅ Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
         return jsonify({
        "success": False,
        "error": "Email already registered ❌"
        })

        account_number = generate_account_number()

        cursor.execute("""
            INSERT INTO users 
            (name, email, password, phone, balance, loan_taken, loan_amount, account_number)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """,(name,email,password,phone,50000,False,0,account_number))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Account Created Successfully ✅",
            "account_number": account_number
        })

    except Exception as e:
        conn.rollback()
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
    
#=========forget password========
    
@app.route("/forgot_password", methods=["POST"])
def forgot_password():

    data = request.json
    email = data["email"]

    # Check if email exists
    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()

    if user:
        return jsonify({
            "success": True,
            "message": "Password reset request sent to your email ✅"
        })
    else:
        return jsonify({
            "success": False,
            "message": "Email not found in our records ❌"
        })
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
        SELECT name, email, phone, balance, loan_taken, loan_amount, account_number
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

    # ✅ Instant approval
    if amount <= 50000:

        cursor.execute("""
            UPDATE users
            SET loan_taken = TRUE,
                loan_amount = %s,
                balance = balance + %s
            WHERE email = %s
        """, (amount, amount, email))

        conn.commit()

        return jsonify({"message": "Loan Approved ✅ Amount Added to Balance"})

    # ⏳ Loan under review
    else:

        cursor.execute("""
            UPDATE users
            SET loan_taken = TRUE,
                loan_amount = %s
            WHERE email = %s
        """, (amount, email))

        conn.commit()

        return jsonify({"message": "Loan Under Review ⏳ Approval within 24 hours"})


# ================= TRANSFER MONEY =================    
@app.route("/transfer", methods=["POST"])
def transfer():

    if "user_email" not in session:
        return jsonify({"message": "Please login first ❌"}), 401

    data = request.json
    amount = int(data["amount"])
    receiver_account = data["receiver_account"]
    sender_email = session["user_email"]

    # Check sender balance
    cursor.execute("""
    SELECT name, account_number, balance 
    FROM users 
    WHERE email=%s
    """, (sender_email,))
    sender = cursor.fetchone()

    if not sender:
        return jsonify({"message": "Sender not found ❌"})

    if sender["balance"] < amount:
        return jsonify({"message": "❌ Insufficient Balance"})

    # Check receiver account
    cursor.execute("""
    SELECT name, email 
    FROM users 
    WHERE account_number=%s
    """, (receiver_account,))
    receiver = cursor.fetchone()

    if not receiver:
        return jsonify({"message": "Receiver account not found ❌"})

    receiver_email = receiver["email"]
    
    # ❌ Prevent self transfer
    if receiver_email == sender_email:
      return jsonify({
        "success": False,
        "message": "You cannot transfer money to your own account ❌"
    })

    # Deduct sender balance
    cursor.execute("""
        UPDATE users
        SET balance = balance - %s
        WHERE email = %s
    """, (amount, sender_email))

    # Add receiver balance
    cursor.execute("""
        UPDATE users
        SET balance = balance + %s
        WHERE account_number = %s
    """, (amount, receiver_account))

    # Store transaction
    cursor.execute("""
    INSERT INTO transactions 
    (email, receiver_account, type, amount, sender_name, sender_account, receiver_name)
    VALUES (%s,%s,%s,%s,%s,%s,%s)
    """,(
        sender_email,
        receiver_account,
        "Sent",
        amount,
        sender["name"],
        sender["account_number"],
        receiver["name"]
))

    conn.commit()

    return jsonify({
        "success": True,
        "message": "Money Transferred Successfully ✅"
    })


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
    SELECT type, amount, receiver_account, receiver_name
    FROM transactions
    WHERE email=%s
    ORDER BY id DESC
    """, (email,))

    transactions = cursor.fetchall()
    return jsonify(transactions)


if __name__ == "__main__":
    app.run(debug=True)