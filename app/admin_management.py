from flask import Blueprint, session, jsonify, redirect, url_for, render_template, request, send_file
import logging
import io
from app.extensions import db, limiter
from flask_login import login_required
from app.models import File, HDRI, GalleryFile, Download
from app.compression_utils import compress_file, decompress_file
from sqlalchemy import text

bp = Blueprint('admin', __name__, static_folder='static')

def vacuum_database():
    """Shrink the SQLite database file after deletions."""
    try:
        # VACUUM must be run outside a transaction
        connection = db.engine.raw_connection()
        connection.execute("VACUUM")
        connection.close()
    except Exception as e:
        logging.warning(f"Could not vacuum database: {e}")

# Custom login_required removed, using Flask-Login's

@bp.route('/update_file', methods=['POST'])
@login_required
def update_file():
    file_id = request.form.get('file_id')

    if not file_id:
        return jsonify({"message": "File ID is required", "success": False}), 400

    try:
        file_record = db.session.get(File, file_id)
        if not file_record:
            return jsonify({"message": "File not found", "success": False}), 404

        new_name = request.form.get('file_name')
        new_year = request.form.get('year')
        new_banner_file = request.files.get('banner')
        new_glb_file = request.files.get('glb_file')

        if new_name:
            file_record.file_name = new_name
        
        if new_year:
            file_record.year = int(new_year)

        if new_banner_file:
            file_record.banner_path = compress_file(new_banner_file.read())
            file_record.banner_mimetype = new_banner_file.mimetype

        if new_glb_file:
            file_record.file_path_glb = compress_file(new_glb_file.read())
            file_record.file_path_glb_mimetype = new_glb_file.mimetype

        db.session.commit()
        return jsonify({"message": "File updated successfully.", "success": True}), 200

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        db.session.rollback()
        return jsonify({"message": "An unexpected error occurred.", "success": False}), 500

@login_required
def delete_file(file_id):
    try:
        # Cascade delete handled manually or by DB FKs. 
        # SQLAlchemy cascade is better but let's do manual to be safe if DB schema isn't strict.
        GalleryFile.query.filter_by(file_id=file_id).delete()
        Download.query.filter_by(file_id=file_id).delete()
        # Comments and Likes might also need deletion if no cascade
        
        File.query.filter_by(id=file_id).delete()
        db.session.commit()
        vacuum_database()  # Shrink DB after delete
    except Exception as e:
        print(f"An error occurred: {e}")
        db.session.rollback()

@login_required
def update_hdri(hdri_id):
    try:
        hdri = db.session.get(HDRI, hdri_id)
        if hdri:
            name = request.form.get('name')
            preview_file = request.files.get('preview')
            
            if name:
                hdri.name = name
            
            if preview_file:
                hdri.preview_path = compress_file(preview_file.read())
                hdri.preview_path_mimetype = preview_file.mimetype
            
            db.session.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
        db.session.rollback()

@login_required
def delete_hdri(hdri_id):
    try:
        HDRI.query.filter_by(id=hdri_id).delete()
        db.session.commit()
        vacuum_database()  # Shrink DB after delete
    except Exception as e:
        print(f"An error occurred: {e}")

@login_required
def upload_gallery_image(file_id, file):
    try:
        image_data = compress_file(file.read())
        image_mimetype = file.mimetype
        
        new_gallery = GalleryFile(
            file_id=file_id,
            file_path=image_data,
            images_mimetype=image_mimetype
        )
        db.session.add(new_gallery)
        db.session.commit()
    except Exception as e:
        print(f"An error occurred: {e}")

@login_required
def delete_gallery_image(gallery_id):
    try:
        GalleryFile.query.filter_by(id=gallery_id).delete()
        db.session.commit()
        vacuum_database()  # Shrink DB after delete
    except Exception as e:
        print(f"An error occurred: {e}")

@bp.route('/preview_hdri/<int:hdri_id>')
@login_required
def preview_hdri(hdri_id):
    hdri = db.session.get(HDRI, hdri_id)
    if hdri:
        return send_file(
            io.BytesIO(decompress_file(hdri.preview_path)),
            mimetype=hdri.preview_path_mimetype,
            as_attachment=False
        )
    return "Preview not found", 404

@bp.route('/manage_all', methods=['GET', 'POST'])
@login_required
def manage_all():
    if request.method == 'POST':
        # Handle each action type independently
        if 'delete_file' in request.form:
            delete_file(request.form['file_id'])
        elif 'delete_hdri' in request.form:
            delete_hdri(request.form['hdri_id'])
        elif 'delete_gallery' in request.form:
            delete_gallery_image(request.form['gallery_id'])
        elif 'delete_download' in request.form:
            delete_download(request.form['download_id'])
        elif 'upload_gallery' in request.form:
            file = request.files.get('gallery_image')
            if file and file.filename != '':
                upload_gallery_image(request.form['file_id'], file)
        elif 'update_hdri' in request.form:
            update_hdri(request.form['hdri_id'])
        # Note: update_file is handled by its own dedicated route /update_file
        
        return redirect(url_for('admin.manage_all'))

    # GET
    files = File.query.all()
    hdri_items = HDRI.query.all()
    gallery_files = GalleryFile.query.all()
    downloads = Download.query.all()

    return render_template('admin/manage_all.html', 
                           files=files, 
                           hdri_items=hdri_items, 
                           gallery_files=gallery_files, 
                           downloads=downloads)

@bp.route('/image/<int:file_id>', methods=['GET'])
@login_required
def image(file_id):
    file_record = db.session.get(File, file_id)
    if file_record:
        return send_file(
            io.BytesIO(decompress_file(file_record.banner_path)),
            mimetype=file_record.banner_mimetype,
            as_attachment=False
        )
    return "Image not found", 404

@bp.route('/gallery_image/<int:gallery_id>', methods=['GET'])
@login_required
@limiter.exempt
def gallery_image(gallery_id):
    image_data = db.session.get(GalleryFile, gallery_id)
    if image_data:
        return send_file(
            io.BytesIO(decompress_file(image_data.file_path)),
            mimetype=image_data.images_mimetype,
            as_attachment=False
        )
    return "Image not found", 404

@login_required
def delete_download(download_id):
    try:
        Download.query.filter_by(id=download_id).delete()
        db.session.commit()
        vacuum_database()  # Shrink DB after delete
    except Exception as e:
        print(f"An error occurred: {e}")
