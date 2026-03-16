from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS

import uuid

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
        (name, email, password, phone, balance, account_number)
         VALUES (%s,%s,%s,%s,%s,%s)
        """,(name,email,password,phone,50000,account_number))

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
        phone = data["phone"]
        
        cursor.execute(
        "SELECT * FROM users WHERE email=%s AND password=%s AND phone=%s",
         (email, password, phone)
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
    SELECT name, email, phone, balance, account_number
    FROM users
    WHERE email=%s
    """, (email,))
    user = cursor.fetchone()

    cursor.execute("""
    SELECT COALESCE(SUM(loan_amount),0) AS total_loan
    FROM loans
    WHERE email=%s
    """, (email,))
    loan = cursor.fetchone()

    user["loan_amount"] = loan["total_loan"]
    

    if user:
        return jsonify(user)
    else:
        return jsonify({"message": "User not found"})
    
# ================= CREDIT HISTORY =================
@app.route("/credit_history")
def credit_history():

    if "user_email" not in session:
        return jsonify({"message": "Please login first ❌"}), 401

    email = session["user_email"]

    cursor.execute("""
    SELECT amount, sender_name, sender_account, created_at
    FROM transactions
    WHERE email=%s AND type='Received'
    ORDER BY id DESC
    """, (email,))

    credits = cursor.fetchall()

    return jsonify(credits)


# ================= APPLY LOAN =================

@app.route("/apply_loan", methods=["POST"])
def apply_loan():

    if "user_email" not in session:
        return jsonify({"message": "Please login first ❌"}), 401

    data = request.json
    amount = int(data["amount"])
    email = session["user_email"]
    cursor.execute(
    "SELECT account_number FROM users WHERE email=%s",
    (email,)
)

    user_account = cursor.fetchone()
    account_number = user_account["account_number"]
    txn_id = "TXN" + str(uuid.uuid4().int)[:9]
    # Check if user already took loan today
    cursor.execute("""
    SELECT created_at FROM transactions
    WHERE email=%s AND type='Loan'
    AND DATE(created_at) = CURRENT_DATE
    """, (email,))

    loan_today = cursor.fetchone()

    if loan_today:
     return jsonify({"message": "You can only take one loan per day ❌"})

    if amount < 5000:
        return jsonify({"message": "❌ Minimum loan amount is ₹5,000"})
    
    #Prevent Loan Spam


    # ✅ Instant approval
    if amount <= 50000:

        cursor.execute("""
        UPDATE users
        SET balance = balance + %s
        WHERE email = %s
        """, (amount, email))
        
        txn_id = "TXN" + str(random.randint(100000000,999999999))

        cursor.execute("""
        INSERT INTO transactions
        (transaction_id, email, type, amount, receiver_name)
        VALUES (%s,%s,%s,%s,%s)
        """, (
            txn_id,
            email,
            "Loan",
            amount,
            "Bank Loan"
))      
        cursor.execute("""
        INSERT INTO loans
        (email, account_number, loan_amount, transaction_id)
        VALUES (%s,%s,%s,%s)
        """,(email, account_number, amount, txn_id))

        conn.commit()

        return jsonify({"message": "Loan Approved ✅ Amount Added to Balance"})

    # ⏳ Loan under review
    else:

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
    if amount <= 0:
     return jsonify({
        "success": False,
        "message": "Invalid transfer amount ❌"
     })

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
    txn_id = "TXN" + str(uuid.uuid4().int)[:9]
    cursor.execute("""
    INSERT INTO transactions 
    (transaction_id, email, receiver_account, type, amount, sender_name, sender_account, receiver_name)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """,(
        txn_id,
        sender_email,
        receiver_account,
        "Sent",
        amount,
        sender["name"],
        sender["account_number"],
        receiver["name"]
    ))  
    # Store receiver transaction
    # Store receiver transaction
    cursor.execute("""
    INSERT INTO transactions 
    (transaction_id, email, receiver_account, type, amount, sender_name, sender_account, receiver_name)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
""",(
    txn_id,
    receiver_email,
    sender["account_number"],
    "Received",
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
    SELECT transaction_id, type, amount, receiver_account, receiver_name,
    sender_name, sender_account, created_at
    FROM transactions
    WHERE email=%s
    ORDER BY id DESC
    """, (email,))

    transactions = cursor.fetchall()
    return jsonify(transactions)


if __name__ == "__main__":
    app.run(debug=True)
    
    
#============feedback========
@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    data = request.json
    email = session["user_email"]
    rating = data["rating"]
    message = data["message"]

    cursor.execute("""
    INSERT INTO feedback (email, rating, message)
    VALUES (%s,%s,%s)
    """,(email, rating, message))

    conn.commit()

    return jsonify({"message":"Thank you for your feedback "})

#========feedback stats ==========
@app.route("/feedback_stats")
def feedback_stats():

    cursor.execute("""
    SELECT 
    COUNT(*) AS total_feedback,
    COALESCE(AVG(rating),0) AS avg_rating
    FROM feedback
    """)

    stats = cursor.fetchone()

    return jsonify(stats)