from flask import Flask, request, redirect
import sqlite3
import hashlib
import secrets
import math

app = Flask(__name__)

DB = "minicalc.db"

# ---------- DB ----------
def get_db():
    return sqlite3.connect(DB, timeout=10, check_same_thread=False)

def init_db():
    with get_db() as db:
        c = db.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            password TEXT,
            approved INTEGER DEFAULT 0,
            activation_key TEXT
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS calculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            expression TEXT,
            result TEXT
        )
        """)

# ---------- UTIL ----------
def sanitize(text):
    return text.replace("<", "").replace(">", "")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_key():
    return secrets.token_hex(16)

# ---------- USERS ----------
def create_user(url, password):
    key = generate_key()

    with get_db() as db:
        c = db.cursor()
        c.execute(
            "INSERT INTO users (url, password, activation_key) VALUES (?, ?, ?)",
            (url, hash_password(password), key)
        )
        user_id = c.lastrowid

    link = f"http://127.0.0.1:5000/activate/{user_id}/{key}"

    with open("approve.txt", "a") as f:
        f.write(f"{url}|||{link}\n")

def check_user(url, password):
    with get_db() as db:
        c = db.cursor()
        c.execute("SELECT id, password, approved FROM users WHERE url=?", (url,))
        row = c.fetchone()

    if row:
        if row[1] != hash_password(password):
            return "wrong_pass", None
        if row[2] == 0:
            return "not_approved", None
        return "ok", row[0]

    return "not_exist", None

# ---------- CALC ----------
def safe_eval(expr):
    try:
        allowed = {
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "sqrt": math.sqrt,
            "log": math.log,
            "pi": math.pi,
            "e": math.e
        }

        return str(eval(expr, {"__builtins__": None}, allowed))
    except:
        return "erro"

def save_calc(user_id, expr, result):
    with get_db() as db:
        c = db.cursor()
        c.execute(
            "INSERT INTO calculations (user_id, expression, result) VALUES (?, ?, ?)",
            (user_id, expr, result)
        )

def load_calcs(user_id):
    with get_db() as db:
        c = db.cursor()
        c.execute(
            "SELECT expression, result FROM calculations WHERE user_id=? ORDER BY id DESC",
            (user_id,)
        )
        return c.fetchall()

# ---------- ROUTES ----------

@app.route("/", methods=["GET", "POST"])
def home():
    error = ""

    if request.method == "POST":
        url = sanitize(request.form.get("url"))
        password = request.form.get("password")

        res, uid = check_user(url, password)

        if res == "ok":
            return redirect(f"/user/{uid}")
        else:
            error = "Erro login"

    return f"""
    <body style="background:#0f0f0f;color:white;font-family:sans-serif;">
    <h1>Mini Scientific Calculator 🧪</h1>

    <form method="POST">
        <input name="url" placeholder="user"><br>
        <input type="password" name="password"><br>
        <button>Login</button>
    </form>

    <a href="/register">➕ Registar</a>
    <p>{error}</p>
    </body>
    """

# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    msg = ""

    if request.method == "POST":
        url = sanitize(request.form.get("url"))
        password = request.form.get("password")

        if url and password:
            try:
                create_user(url, password)
                msg = "Criado! Aguarda aprovação."
            except:
                msg = "Já existe"

    return f"""
    <body style="background:#0f0f0f;color:white;">
    <h2>Registar</h2>
    <form method="POST">
        <input name="url"><br>
        <input type="password" name="password"><br>
        <button>Registar</button>
    </form>
    <p>{msg}</p>
    </body>
    """

# ACTIVATE
@app.route("/activate/<int:user_id>/<key>")
def activate(user_id, key):
    with get_db() as db:
        c = db.cursor()
        c.execute("SELECT activation_key FROM users WHERE id=?", (user_id,))
        row = c.fetchone()

        if row and row[0] == key:
            c.execute("UPDATE users SET approved=1 WHERE id=?", (user_id,))
            db.commit()
            return "Conta ativada!"

    return "Link inválido"

# USER PAGE
@app.route("/user/<int:user_id>", methods=["GET", "POST"])
def user_page(user_id):
    error = ""

    if request.method == "POST":
        url = sanitize(request.form.get("url"))
        password = request.form.get("password")
        expr = sanitize(request.form.get("expr"))

        res, uid = check_user(url, password)

        if res == "ok" and uid == user_id:
            result = safe_eval(expr)
            save_calc(user_id, expr, result)
            return redirect(f"/user/{user_id}")
        else:
            error = "Erro autenticação"

    calcs = load_calcs(user_id)

    html = f"""
    <body style="background:#0f0f0f;color:white;font-family:sans-serif;">
    <h2>Calculadora #{user_id}</h2>

    <form method="POST" onsubmit="return validar()">
        <input name="url" placeholder="user"><br>
        <input type="password" name="password"><br>
        <input name="expr" id="expr" placeholder="equação"><br>
        <button>Calcular</button>
    </form>

    <p>{error}</p>
    <hr>

    <script>
    function validar() {{
        try {{
            eval(document.getElementById("expr").value);
            return true;
        }} catch(e) {{
            alert("Expressão inválida!");
            return false;
        }}
    }}
    </script>
    """

    for expr, res in calcs:
        html += f"<p>{res} = {expr}</p>"

    html += "</body>"
    return html

# ---------- START ----------
if __name__ == "__main__":
    init_db()
    app.run(debug=True, use_reloader=False)
