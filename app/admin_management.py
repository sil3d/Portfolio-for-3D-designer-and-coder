from flask import Blueprint, session, jsonify, redirect, url_for, render_template, request, send_file, current_app
import logging
import io
import os
from app.extensions import db, limiter
from flask_login import login_required
from app.models import File, HDRI, GalleryFile, Download, StorylineItem
from app.utils import compress_file, decompress_file
from sqlalchemy import text

bp = Blueprint('admin', __name__, static_folder='static')

@bp.route('/admin/storyline', methods=['GET', 'POST'])
@login_required
def manage_storyline():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            title = request.form.get('title')
            description = request.form.get('description')
            media_url = request.form.get('media_url')
            is_video = request.form.get('is_video') == 'on'
            order = request.form.get('order', 0)
            
            new_item = StorylineItem(
                title=title,
                description=description,
                media_url=media_url,
                is_video=is_video,
                order=int(order)
            )
            db.session.add(new_item)
            db.session.commit()
            return redirect(url_for('admin.manage_storyline'))
            
        elif action == 'delete':
            item_id = request.form.get('item_id')
            StorylineItem.query.filter_by(id=item_id).delete()
            db.session.commit()
            return redirect(url_for('admin.manage_storyline'))

        elif action == 'update':
            item_id = request.form.get('item_id')
            item = db.session.get(StorylineItem, item_id)
            if item:
                item.title = request.form.get('title')
                item.description = request.form.get('description')
                try:
                    item.order = int(request.form.get('order', 0))
                except ValueError:
                    pass # Keep old order if invalid
                db.session.commit()
            return redirect(url_for('admin.manage_storyline'))

    # Fetch existing items
    storyline_items = StorylineItem.query.order_by(StorylineItem.order.asc(), StorylineItem.date_added.desc()).all()

    # Scan for available media files in static/images
    media_files = []
    base_dir = os.path.join(current_app.static_folder, 'images')
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.mp4', '.webm', '.mkv'}

    # Get set of currently used media URLs
    used_urls = {item.media_url for item in storyline_items}

    for root, dirs, files in os.walk(base_dir):
        for file in files:
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in allowed_extensions:
                # Calculate relative path from static folder
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, current_app.static_folder)
                
                # Use forward slashes for URLs
                url_path = '/static/' + rel_path.replace('\\', '/')
                
                # Skip if already in use
                if url_path in used_urls:
                    continue

                media_files.append({
                    'name': file,
                    'url': url_path,
                    'is_video': file_ext in {'.mp4', '.webm', '.mkv'},
                    'folder': os.path.relpath(root, base_dir).replace('\\', '/')
                })
    
    # Sort files by name
    media_files.sort(key=lambda x: x['name'])

    return render_template('admin/manage_storyline.html', items=storyline_items, media_files=media_files)

def vacuum_database():
    """Shrink the SQLite database file after deletions."""
    try:
        # VACUUM must be run outside a transaction
        connection = db.engine.raw_connection()
        cursor = connection.cursor()
        cursor.execute("VACUUM")
        cursor.close()
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
        
        # Files
        new_banner_file = request.files.get('banner')
        new_glb_file = request.files.get('glb_file')
        
        # URLs
        new_banner_url = request.form.get('banner_url')
        new_glb_url = request.form.get('glb_url')
        new_zip_url = request.form.get('zip_url')

        if new_name:
            file_record.file_name = new_name
        
        if new_year:
            file_record.year = int(new_year)

        # Update URLs if provided
        if new_banner_url:
             file_record.banner_url = new_banner_url
        if new_glb_url:
             file_record.file_path_glb_url = new_glb_url
        if new_zip_url:
             file_record.file_path_zip_url = new_zip_url

        # Check files (override URLs if file uploaded? or clear URL? Logic: File replaces file content. URL replaces URL context.)
        # If user uploads a file, we probably want to prioritize it, but sticking to existing logic.
        if new_banner_file:
            file_record.banner_path = compress_file(new_banner_file.read())
            file_record.banner_mimetype = new_banner_file.mimetype
            # file_record.banner_url = None # Optional: Clear URL if file uploaded

        if new_glb_file:
            file_record.file_path_glb = compress_file(new_glb_file.read())
            file_record.file_path_glb_mimetype = new_glb_file.mimetype
            # file_record.file_path_glb_url = None

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
        # Default to image/jpeg if mimetype is not set
        mimetype = hdri.preview_path_mimetype if hdri.preview_path_mimetype else 'image/jpeg'
        return send_file(
            io.BytesIO(decompress_file(hdri.preview_path)),
            mimetype=mimetype,
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
