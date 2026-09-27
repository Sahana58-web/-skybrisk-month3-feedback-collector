from flask import Flask, render_template, request, redirect, jsonify, Response
import sqlite3
import csv
import io
from datetime import datetime

app = Flask(__name__)
DATABASE = "database.db"


def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            rating INTEGER NOT NULL,
            comments TEXT,
            date_submitted TEXT
        )
    """)
    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/submit-feedback", methods=["POST"])
def submit_feedback():
    name = request.form.get("name")
    email = request.form.get("email")
    rating = request.form.get("rating")
    comments = request.form.get("comments")
    date_submitted = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO feedback (name, email, rating, comments, date_submitted) VALUES (?, ?, ?, ?, ?)",
        (name, email, rating, comments, date_submitted)
    )
    conn.commit()
    conn.close()

    return redirect("/?success=true")


@app.route("/admin-dashboard")
def admin_dashboard():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM feedback ORDER BY date_submitted DESC")
    all_feedback = cursor.fetchall()

    total_feedback = len(all_feedback)
    if total_feedback > 0:
        average_rating = sum(row["rating"] for row in all_feedback) / total_feedback
    else:
        average_rating = 0

    # Count how many feedback entries got each rating (1 to 5), for the chart
    rating_counts = {str(i): 0 for i in range(1, 6)}
    for row in all_feedback:
        rating_counts[str(row["rating"])] += 1

    conn.close()

    return render_template(
        "admin.html",
        feedback_list=all_feedback,
        total_feedback=total_feedback,
        average_rating=round(average_rating, 2),
        rating_counts=rating_counts
    )


@app.route("/api/feedback")
def api_feedback():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM feedback")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/export-csv")
def export_csv():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM feedback")
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Email", "Rating", "Comments", "Date Submitted"])
    for row in rows:
        writer.writerow([row["id"], row["name"], row["email"], row["rating"], row["comments"], row["date_submitted"]])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=feedback_export.csv"}
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)