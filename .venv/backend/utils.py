import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app, url_for

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

#默认空白图片URL
DEFAULT_IMAGE_URL = "https://via.placeholder.com/200x200/cccccc/999999?text=No+Image"


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file):
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{ext}"

        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(upload_path)

        return url_for('static', filename=f'uploads/{unique_filename}', _external=True)

    return DEFAULT_IMAGE_URL