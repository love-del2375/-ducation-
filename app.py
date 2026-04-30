from flask import Flask, render_template, request, redirect, session, url_for
from models import db, Student, Note, User
import plotly.graph_objs as go
import plotly.offline as pyo

# --- Initialisation Flask ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "secret_key_for_sessions"
db.init_app(app)

with app.app_context():
    db.create_all()

# --- Dashboard principal ---
@app.route("/", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        student_id = request.form["student_id"]
        subject = request.form["subject"]
        note = float(request.form["note"])
        new_note = Note(student_id=student_id, subject=subject, note=note)
        db.session.add(new_note)
        db.session.commit()
        return redirect("/")

    notes = Note.query.all()
    students = Student.query.all()

    # Graphique 1 : Histogramme des notes
    noms = [n.student.name for n in notes]
    valeurs = [n.note for n in notes]
    fig1 = go.Figure([go.Bar(x=noms, y=valeurs)])
    graph1 = pyo.plot(fig1, output_type="div")

    # Graphique 2 : Répartition des performances
    categories = ["Excellent (>=16)", "Bien (12-15)", "Passable (10-11)", "Échec (<10)"]
    counts = [sum(1 for n in valeurs if n >= 16),
              sum(1 for n in valeurs if 12 <= n < 16),
              sum(1 for n in valeurs if 10 <= n < 12),
              sum(1 for n in valeurs if n < 10)]
    fig2 = go.Figure([go.Pie(labels=categories, values=counts)])
    graph2 = pyo.plot(fig2, output_type="div")

    return render_template("dashboard.html", graph1=graph1, graph2=graph2, students=students, notes=notes)

# --- Ajouter un étudiant ---
@app.route("/add_student", methods=["GET", "POST"])
def add_student():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]
        new_student = Student(name=name)
        db.session.add(new_student)
        db.session.commit()
        return redirect("/")
    return render_template("add_student.html")

# --- Ajouter une note ---
@app.route("/add_note", methods=["GET", "POST"])
def add_note():
    if "user_id" not in session:
        return redirect(url_for("login"))

    students = Student.query.all()
    if request.method == "POST":
        student_id = request.form["student_id"]
        subject = request.form["subject"]
        note = float(request.form["note"])
        new_note = Note(student_id=student_id, subject=subject, note=note)
        db.session.add(new_note)
        db.session.commit()
        return redirect("/")
    return render_template("add_note.html", students=students)

# --- Statistiques ---
@app.route("/stats")
def stats():
    if "user_id" not in session:
        return redirect(url_for("login"))

    notes = Note.query.all()
    subjects = list(set([n.subject for n in notes]))
    averages = [sum(n.note for n in notes if n.subject == s)/len([n for n in notes if n.subject == s]) for s in subjects]
    fig = go.Figure([go.Bar(x=subjects, y=averages)])
    graph_matiere = pyo.plot(fig, output_type="div")
    return render_template("stats.html", graph_matiere=graph_matiere)

# --- Historique ---
@app.route("/historique")
def historique():
    if "user_id" not in session:
        return redirect(url_for("login"))

    notes = Note.query.all()
    return render_template("historique.html", notes=notes)

# --- Gestion des utilisateurs ---
@app.route("/manage_users")
def manage_users():
    if "user_id" not in session:
        return redirect(url_for("login"))

    users = User.query.all()
    return render_template("manage_users.html", users=users)

# --- Connexion ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            return redirect("/")
    return render_template("login.html")

# --- Inscription ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return redirect("/login")
    return render_template("register.html")

# --- Déconnexion ---
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/login")

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)