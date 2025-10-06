# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, make_response
from werkzeug.utils import secure_filename
import io
import csv
from utils.hash_functions import generate_hash, verify_file_integrity, batch_hash_files, compare_hashes

# CONFIG
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = None  # None => accept any; set to a set to restrict types
MAX_MB = 10

app = Flask(__name__)
app.secret_key = 'replace_with_a_real_secret_for_production'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_MB * 1024 * 1024

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    if ALLOWED_EXTENSIONS is None:
        return True
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------- Routes ----------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hash', methods=['POST'])
def do_hash():
    algorithm = request.form.get('algorithm', 'sha256')
    text = request.form.get('text_input', '').strip()
    file = request.files.get('file_input')

    filename = None
    hash_result = None
    error = None

    if text:
        hash_result = generate_hash(text, algorithm)
    elif file and file.filename:
        if not allowed_file(file.filename):
            error = "This file type is not allowed."
        else:
            filename = secure_filename(file.filename)
            data = file.read()
            hash_result = generate_hash(data, algorithm)
    else:
        error = "No text or file provided."

    return render_template('result.html',
                           algorithm=algorithm,
                           hash_result=hash_result,
                           filename=filename,
                           error=error)

# Compare two inputs (text or files)
@app.route('/compare', methods=['GET', 'POST'])
def compare():
    result = None
    left_hash = None
    right_hash = None
    algorithm = request.form.get('algorithm', 'sha256')

    if request.method == 'POST':
        algorithm = request.form.get('algorithm', 'sha256')

        # left: can be text or file
        left_text = request.form.get('left_text', '').strip()
        left_file = request.files.get('left_file')

        # right: same
        right_text = request.form.get('right_text', '').strip()
        right_file = request.files.get('right_file')

        if left_text:
            left_hash = generate_hash(left_text, algorithm)
        elif left_file and left_file.filename:
            left_hash = generate_hash(left_file.read(), algorithm)

        if right_text:
            right_hash = generate_hash(right_text, algorithm)
        elif right_file and right_file.filename:
            right_hash = generate_hash(right_file.read(), algorithm)

        if left_hash is None or right_hash is None:
            result = "Please provide both left and right inputs (text or file)."
        else:
            match = compare_hashes(left_hash, right_hash)
            result = "MATCH" if match else "MISMATCH"

    return render_template('compare.html',
                           algorithm=algorithm,
                           left_hash=left_hash,
                           right_hash=right_hash,
                           result=result)

# Integrity check: upload file + paste expected hash
@app.route('/integrity', methods=['GET', 'POST'])
def integrity():
    status = None
    actual_hash = None
    algorithm = request.form.get('algorithm', 'sha256')

    if request.method == 'POST':
        algorithm = request.form.get('algorithm', 'sha256')
        expected = request.form.get('expected_hash', '').strip()
        file = request.files.get('file_input')

        if not file or file.filename == '':
            status = "No file uploaded."
        elif not expected:
            status = "Please paste the expected hash."
        else:
            data = file.read()
            ok, actual = verify_file_integrity(data, expected, algorithm)
            actual_hash = actual
            status = "File is authentic ✅" if ok else "File has been modified ❌"

    return render_template('integrity.html',
                           algorithm=algorithm,
                           status=status,
                           actual_hash=actual_hash)

# Batch hashing: multiple files -> table + CSV export
@app.route('/batch', methods=['GET', 'POST'])
def batch():
    results = []
    algorithm = request.form.get('algorithm', 'sha256')
    if request.method == 'POST':
        files = request.files.getlist('files')
        file_streams = []
        for f in files:
            if f and f.filename:
                name = secure_filename(f.filename)
                data = f.read()
                file_streams.append((name, data))
        results = batch_hash_files(file_streams, algorithm)
        # store results in session? For now we render them and provide CSV download button
    return render_template('batch.html', algorithm=algorithm, results=results)

@app.route('/batch_download', methods=['POST'])
def batch_download():
    """
    Expect POST form with csv rows in hidden input OR reconstruct from uploaded files (we'll reconstruct).
    Simpler approach: client posts filenames and hashes as form fields.
    """
    # We'll accept CSV rows from JS form field "csvdata"
    csvdata = request.form.get('csvdata')
    if not csvdata:
        return redirect(url_for('batch'))

    mem = io.BytesIO()
    mem.write(csvdata.encode('utf-8'))
    mem.seek(0)
    return send_file(mem,
                     as_attachment=True,
                     download_name='hashes.csv',
                     mimetype='text/csv')

# small API endpoint (developer mode)
@app.route('/api/hash', methods=['GET'])
def api_hash():
    algo = request.args.get('algo', 'sha256')
    text = request.args.get('text', '')
    if not text:
        return {"error": "Please supply 'text' parameter."}, 400
    result = generate_hash(text, algo)
    return {"algorithm": algo, "hash": result}

if __name__ == '__main__':
    app.run(debug=True)
