from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'kunci_rahasia_pondok'  # Ganti dengan kunci rahasia yang lebih kuat
DATABASE = 'database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initialize the database."""
    init_db()
    print('Initialized the database.')

@app.route('/daftar', methods=['GET', 'POST'])
def daftar():
    if request.method == 'POST':
        nama_lengkap = request.form['nama_lengkap']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        error = None

        if not nama_lengkap:
            error = 'Nama lengkap wajib diisi.'
        elif not username:
            error = 'Username wajib diisi.'
        elif not email:
            error = 'Email wajib diisi.'
        elif not password:
            error = 'Password wajib diisi.'

        if error is None:
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO santri (nama_lengkap, username, email, password) VALUES (?, ?, ?, ?)",
                    (nama_lengkap, username, email, generate_password_hash(password))
                )
                db.commit()
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                error = 'Username atau email sudah terdaftar.'
            finally:
                db.close()
        flash(error)
    return render_template('daftar.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute(
            "SELECT * FROM santri WHERE username = ?", (username,)
        ).fetchone()
        db.close()

        if user is None:
            error = 'Username tidak ditemukan.'
        elif not check_password_hash(user['password'], password):
            error = 'Password salah.'
        else:
            session['user_id'] = user['id']
            return redirect(url_for('dashboard')) # Alihkan ke halaman dashboard setelah login berhasil
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        db = get_db()
        user = db.execute("SELECT nama_lengkap FROM santri WHERE id = ?", (session['user_id'],)).fetchone()
        db.close()
        if user:
            return f"Selamat datang, {user['nama_lengkap']}!"
        else:
            return redirect(url_for('login'))
    return redirect(url_for('login'))

@app.route('/')
def index():
    return redirect(url_for('login')) # Alihkan ke halaman login sebagai halaman utama

if __name__ == '__main__':
    app.run(debug=True)
