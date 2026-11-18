import os
import uuid
import sqlite3
from datetime import datetime

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, send_file, abort
)
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from image_utils import analyse_image
from compliance import assess_compliance
from report import create_pdf_report

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
REPORT_FOLDER = os.path.join(BASE_DIR, "reports")
DB_PATH = os.path.join(BASE_DIR, "project.db")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)


# DATABASE CONNECTION
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# CREATE DATABASE TABLE
def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id TEXT PRIMARY KEY,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                destination TEXT,
                batch_number TEXT,
                net_weight TEXT,
                country_origin TEXT,
                extracted_text TEXT,
                score INTEGER,
                status TEXT,
                observations TEXT,
                image_names TEXT,
                created_at TEXT NOT NULL
            )
        """)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# HOME PAGE
@app.route("/")
def home():
    return render_template("index.html")


# SUBMIT PRODUCT FOR ASSESSMENT
@app.route("/assess", methods=["POST"])
def assess():

    product_name = request.form.get("product_name", "").strip()
    category = request.form.get("category", "").strip()
    destination = request.form.get("destination", "").strip()
    batch_number = request.form.get("batch_number", "").strip()
    net_weight = request.form.get("net_weight", "").strip()
    country_origin = request.form.get("country_origin", "").strip()

    if not product_name or not category:
        flash("Enter the product name and category.", "error")
        return redirect(url_for("home"))

    uploaded_files = request.files.getlist("images")
    uploaded_files = [
        file for file in uploaded_files if file and file.filename
    ]

    if not uploaded_files:
        flash("Please upload at least one image.", "error")
        return redirect(url_for("home"))

    if len(uploaded_files) > 5:
        flash("You can upload a maximum of 5 images.", "error")
        return redirect(url_for("home"))

    image_results = []
    saved_names = []
    extracted_texts = []

    for file in uploaded_files:

        if not allowed_file(file.filename):
            flash("Use PNG, JPG, JPEG or WEBP images.", "error")
            return redirect(url_for("home"))

        safe_name = secure_filename(file.filename)
        unique_name = uuid.uuid4().hex + "_" + safe_name

        image_path = os.path.join(UPLOAD_FOLDER, unique_name)
        file.save(image_path)

        saved_names.append(unique_name)

        result = analyse_image(image_path)
        image_results.append(result)

        if result.get("text"):
            extracted_texts.append(result["text"])

    extracted_text = "\n\n".join(extracted_texts)

    # COMPLIANCE ASSESSMENT
    assessment = assess_compliance(
        product_name,
        category,
        destination,
        batch_number,
        net_weight,
        country_origin,
        extracted_text,
        image_results
    )

    assessment_id = (
        "EQC-" + datetime.now().strftime("%Y%m%d")
        + "-" + uuid.uuid4().hex[:6].upper()
    )

    created_at = datetime.now().strftime("%d %B %Y, %I:%M %p")

    observations = "\n".join(assessment["observations"])

    # SAVE RESULT IN SQLITE DATABASE
    with get_db() as conn:
        conn.execute("""
            INSERT INTO assessments (
                id, product_name, category, destination,
                batch_number, net_weight, country_origin,
                extracted_text, score, status, observations,
                image_names, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assessment_id,
            product_name,
            category,
            destination,
            batch_number,
            net_weight,
            country_origin,
            extracted_text,
            assessment["score"],
            assessment["status"],
            observations,
            ",".join(saved_names),
            created_at
        ))

    # GENERATE PDF REPORT
    report_path = os.path.join(
        REPORT_FOLDER, assessment_id + ".pdf"
    )

    product = {
        "name": product_name,
        "category": category,
        "destination": destination,
        "batch_number": batch_number,
        "net_weight": net_weight,
        "country_origin": country_origin
    }

    create_pdf_report(
        report_path,
        assessment_id,
        created_at,
        product,
        assessment,
        extracted_text,
        len(saved_names)
    )

    return render_template(
        "result.html",
        assessment=assessment,
        assessment_id=assessment_id,
        created_at=created_at,
        product=product,
        extracted_text=extracted_text,
        image_count=len(saved_names)
    )


# DOWNLOAD PDF
@app.route("/report/<assessment_id>")
def download_report(assessment_id):

    if (
        not assessment_id.startswith("EQC-")
        or "/" in assessment_id
        or "\\" in assessment_id
    ):
        abort(404)

    path = os.path.join(
        REPORT_FOLDER,
        assessment_id + ".pdf"
    )

    if not os.path.isfile(path):
        abort(404)

    return send_file(
        path,
        as_attachment=True,
        download_name=assessment_id + "_report.pdf"
    )


# ASSESSMENT HISTORY
@app.route("/history")
def history():

    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, product_name, category,
                   score, status, created_at
            FROM assessments
            ORDER BY rowid DESC
            LIMIT 30
        """).fetchall()

    return render_template("history.html", rows=rows)


# FILE SIZE ERROR
@app.errorhandler(RequestEntityTooLarge)
def file_too_large(error):
    flash("Total uploaded image size must be below 12 MB.", "error")
    return redirect(url_for("home"))


@app.errorhandler(404)
def not_found(error):
    return render_template(
        "error.html",
        message="The requested page or report was not found."
    ), 404


init_db()


if __name__ == "__main__":
    app.run(debug=True)