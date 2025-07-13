from flask import Flask, render_template, request, redirect, session, flash
from datetime import timedelta
import bcrypt
from mysql.connector import Error
import mysql.connector
import os

'''
 maintainer: mivel
 contact: mivelkhansa6@gmail.com
 note: this just a hobby project not for serious use, it's just for fun and learning purposes
'''

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.permanent_session_lifetime = timedelta(days=30)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        port=os.getenv("MYSQL_PORT"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )

def get_user(email):
    cursor = None
    db = None
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user:
            return user[0]
    except Error as e:
        print(f"Error: {e}")
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()

@app.route("/", methods = ["GET","POST"])
def home():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        new_task = request.form.get("add_task")
        if new_task:
            cursor = None
            db = None
            try:
                db = get_db_connection()
                cursor = db.cursor()
                # Insert the task
                cursor.execute("INSERT INTO todo (user_id, task) VALUES (%s,%s);", (session['user_id'], new_task))
                db.commit()
            except Error as e:
                print(f"MySql error: {e}")
            finally:
                if cursor:
                    cursor.close()
                if db:
                    db.close()
        return redirect("/")
    else:
        todo_item = []
        cursor = None
        db = None
        try:
            db = get_db_connection()
            cursor = db.cursor()
            # todo check if user exists | not hardcoded
            cursor.execute("SELECT id FROM users WHERE email = ")
            user = cursor.fetchone()
            if user:
                cursor.execute("SELECT task FROM todo where user_id = %s;", (session['user_id'],))
                rows = cursor.fetchall()
                if rows:
                    todo_item = [row[0] for row in rows]
                print("Fetched tasks:", todo_item)
        except Error as e:
            print(e)
        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()
            print("Fetched tasks:", todo_item)
        return render_template("index.html", todo_item = todo_item)

@app.route("/login",methods = ["GET","POST"])
def login():
    if request.method == "POST":
        db = get_db_connection()
        cursor = db.cursor()
        email = request.form['email']
        password = request.form['password']

        '''
            if password != confirm:
            flash('Passwords do not match')
            return redirect("/login")
        '''

        if not email or not password:
            flash('Email and password are required')
            return redirect("/login")

        cursor.execute("SELECT id, password FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if user:
            if bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
                session['user_id'] = user[0]
                if cursor:
                    cursor.close()
                if db:
                    db.close()
                return redirect("/")
        else:
            if cursor:
                cursor.close()
            if db:
                db.close()
            flash('Invalid email or password')
            return redirect("/login")
    return render_template("login.html")

@app.route("/signup", methods = ["GET","POST"])
def signup():
    db = None
    cursor = None
    if request.method == "POST":
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm = request.form['confirm']

        if not email or not password or not confirm:
            flash('Email, password, and confirm password are required',"error")
            return redirect("/signup")

        if password != confirm:
            flash('Passwords do not match',"error")
            return redirect("/signup")

        try:
            db = get_db_connection()
            cursor = db.cursor()

            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash("Email already registered", "error")
                return redirect("/signup")

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, hashed_password))
            db.commit()
        except Exception:
            flash('Error connecting to database',"error")
            return redirect("/signup")

        if cursor:
            cursor.close()
        if db:
            db.close()
        flash('Account created successfully',"success")
        return redirect("/login")
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
