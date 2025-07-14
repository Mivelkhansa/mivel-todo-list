from flask import Flask, render_template, request, redirect, session, flash
from datetime import timedelta
import re
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
port = os.getenv("MYSQL_PORT")

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        port=port,
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        autocommit=False
    )

def email_validation(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

#todo refactor to shorten code
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
    # for get request
    else:
        todo_item = []
        cursor = None
        db = None
        try:
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute("SELECT id,task FROM todo WHERE user_id = %s;", (session['user_id'],))
            rows = cursor.fetchall()
            if rows:
                todo_item = [row for row in rows]
            app.logger.info("Fetched tasks:", todo_item)
        except Error as e:
            print(e)
        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()
            app.logger.info("Fetched tasks:", todo_item)
        return render_template("index.html", todo_item = todo_item)

@app.route("/delete/<int:id>", methods=["POST"])
def delete_task(id):
    if "user_id" not in session:
        flash('You are not logged in')
        app.logger.error('User not logged in')
        return redirect("/login")

    if not id:
        flash('Task ID is required')
        return redirect("/")
    db = None
    cursor = None
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("DELETE FROM todo WHERE id = %s AND user_id = %s", (id, session['user_id']))
        db.commit()
        cursor.close()
        db.close()
        flash('Task deleted successfully')
    except Error as e:
        app.logger.error('Error deleting task:', e)
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()
    return redirect("/")

@app.route("/login",methods = ["GET","POST"])
def login():
    db = None
    cursor = None
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        if not email_validation(email):
            flash('Invalid email',"error")
            return redirect("/login")

        if not password:
            flash('Password is required',"error")
            return redirect("/login")

        try:
            db = get_db_connection()
            cursor = db.cursor()

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
                app.logger.error(f'Email: {email}, Password: {password}')
                return redirect("/login")
        except Exception as e:
            if cursor:
                cursor.close()
            if db:
                db.close()
            app.logger.error(f'Error: {e}')
            flash('An error occurred')
            return redirect("/login")
    return render_template("login.html")

@app.route("/signup", methods = ["GET","POST"])
def signup():
    db = None
    cursor = None
    if request.method == "POST":
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if not email_validation(email):
            flash('Invalid email',"error")
            return redirect("/signup")

        if not password or not confirm_password:
            flash('Email, password, and confirm password are required',"error")
            return redirect("/signup")

        if password != confirm_password:
            flash('Passwords do not match',"error")
            return redirect("/signup")

        try:
            db = get_db_connection()
            cursor = db.cursor()

            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash("Email already registered", "error")
                app.logger.error(f'User creation failed: {email}')
                return redirect("/signup")

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, hashed_password))
            db.commit()
        except Exception as e:
            flash('Error connecting to database',"error")
            app.logger.error(f'failed connection to database: {e}')
            return redirect("/signup")

        if cursor:
            cursor.close()
        if db:
            db.close()
        flash('Account created successfully',"success")
        app.logger.info(f'User created: {email}')
        return redirect("/login")
    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
