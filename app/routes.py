from flask import (Blueprint, jsonify, Response, redirect, url_for,
                   request, session, send_from_directory, render_template, send_file, abort)
from app.extensions import db, limiter
from app.models import File, GalleryFile, HDRI, Comment, Like, Download
from flask_login import login_required, current_user
import io
import base64
import logging
from werkzeug.utils import secure_filename
import requests
import re
import dns.resolver
from app.compression_utils import compress_file, decompress_file

bp = Blueprint('main', __name__, static_folder='static')
# Configuration du logging
logging.basicConfig(filename='error.log', level=logging.ERROR)

VALID_YEARS = [2022, 2023, 2024, 2025]

def get_location_from_ip(ip_address):
    try:
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=5) # Added timeout
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'fail':
            return 'Unknown Location'
        
        city = data.get('city', 'Unknown')
        region = data.get('regionName', 'Unknown')
        country = data.get('country', 'Unknown')
        location = f"{city}, {region}, {country}"
        
        return location
    
    except requests.RequestException as e:
        print(f"Error retrieving location: {e}")
        return 'Unknown Location'

def to_base32(string):
    return base64.b32encode(string.encode()).decode().rstrip('=')

@bp.route('/')
def index():
    return render_template('home.html')

@bp.route('/works')
def works():
    years_data = {
        2022: {
            'banner_path': 'images_years/2022.jpg',
            'title': 'Starting My 3D Design Journey',
            'description': 'Began exploring the world of 3D design and modeling.',
            'projects_count': 10,
            'skills_count': 5
        },
        2023: {
            'banner_path': 'images_years/2023.jpg',
            'title': 'Advancing Skills',
            'description': 'Refined techniques and explored advanced 3D modeling.',
            'projects_count': 25,
            'skills_count': 15
        },
        2024: {
            'banner_path': 'images_years/2024.jpg',
            'title': 'Current Achievements',
            'description': 'Achieving significant milestones in 3D design.',
            'projects_count': 40,
            'skills_count': 30
        },
        2025: {
            'banner_path': 'images_years/2025.png',
            'title': 'Future Goals',
            'description': 'Looking forward to new milestones and innovations.',
            'projects_count': 50,
            'skills_count': 40
        }
    }
    return render_template('works.html', years_data=years_data)

@bp.route('/resume')
def resume():
    return render_template('resume.html')

@bp.route('/accomplishments')
def accomplishments():
    return render_template('accomplishments.html')

@bp.route('/image/<int:file_id>')
def serve_image(file_id):
    try:
        file = db.session.get(File, file_id)

        if file and file.banner_path:
            image_data = decompress_file(file.banner_path)
            mimetype = file.banner_mimetype or 'image/jpeg'
            return send_file(io.BytesIO(image_data), mimetype=mimetype)

        return "Image not found", 404

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return "An unexpected error occurred", 500

@bp.route('/gallery/<int:year>')
def models_year(year):
    try:
        # Récupérer les fichiers pour l'année spécifiée
        files = File.query.filter_by(year=year).with_entities(File.id, File.file_name).all()
        # Convert to dictionary-like objects for template
        files_data = [{'id': f.id, 'file_name': f.file_name} for f in files]
        
        return render_template('banner.html', year=year, files=files_data)
    
    except Exception as e:
        return str(e), 500

def allowed_file(filename, allowed_extensions):
    """Vérifie si le fichier a une extension autorisée."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    try:
        if 'glb_file' not in request.files:
            return jsonify({"success": False, "message": "No GLB file uploaded"}), 400

        model_name = request.form.get('model_name')
        banner = request.files.get('banner')
        glb_file = request.files['glb_file']
        zip_file = request.files.get('zip_file')
        year = request.form.get('year')
        gallery_files = request.files.getlist('gallery')

        if not model_name or not year or not glb_file or not allowed_file(glb_file.filename, ['glb']):
            return jsonify({"success": False, "message": "Required fields are missing or invalid"}), 400

        if not year.isdigit() or not (1900 <= int(year) <= 2100):
            return jsonify({"success": False, "message": "Invalid year. Please provide a valid year between 1900 and 2100."}), 400

        user_ip = request.remote_addr
        location = get_location_from_ip(user_ip)

        # Read and compress file data
        banner_data = compress_file(banner.read()) if banner and allowed_file(banner.filename, ['png', 'jpg', 'jpeg']) else b''
        glb_data = compress_file(glb_file.read()) if allowed_file(glb_file.filename, ['glb']) else b''
        zip_data = compress_file(zip_file.read()) if zip_file and allowed_file(zip_file.filename, ['zip']) else b''

        # Ensure MIME types are correct
        banner_mimetype = banner.content_type if banner else None
        file_glb_mimetype = 'model/gltf-binary'
        file_zip_mimetype = zip_file.content_type if zip_file else None

        new_file = File(
            file_name=model_name,
            banner_path=banner_data,
            banner_mimetype=banner_mimetype,
            file_path_glb=glb_data,
            file_path_glb_mimetype=file_glb_mimetype,
            file_path_zip=zip_data,
            file_path_zip_mimetype=file_zip_mimetype,
            added_by=current_user.username,
            location=location,
            year=int(year)
        )
        
        db.session.add(new_file)
        db.session.flush() # Flush to get the ID

        # Insert gallery files
        for gallery_file in gallery_files:
            if gallery_file and allowed_file(gallery_file.filename, ['png', 'jpg', 'jpeg']):
                gallery_data = compress_file(gallery_file.read())
                gallery_mimetype = gallery_file.content_type
                new_gallery_image = GalleryFile(
                    file_id=new_file.id,
                    file_path=gallery_data,
                    images_mimetype=gallery_mimetype
                )
                db.session.add(new_gallery_image)

        db.session.commit()

        return jsonify({"success": True, "message": "File uploaded successfully."})

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        db.session.rollback()
        return jsonify({"success": False, "message": "An unexpected error occurred."}), 500

@bp.route('/upload_hdri', methods=['POST'])
@login_required
def upload_hdri():
    try:
        if 'hdri_file' not in request.files:
            return jsonify({"success": False, "message": "No HDRI file uploaded"}), 400

        hdri_name = request.form.get('hdri_name')
        hdri_file = request.files['hdri_file']
        preview_file = request.files.get('preview_file')

        if not hdri_name or not hdri_file or not allowed_file(hdri_file.filename, ['hdr', 'exr']):
            return jsonify({"success": False, "message": "Required fields are missing or invalid"}), 400

        if preview_file and not allowed_file(preview_file.filename, ['png', 'jpg', 'jpeg']):
            return jsonify({"success": False, "message": "Invalid preview file format. Only PNG, JPG, JPEG are allowed."}), 400

        hdri_data = compress_file(hdri_file.read())
        preview_data = compress_file(preview_file.read()) if preview_file else b''

        hdri_mimetype = hdri_file.mimetype or 'image/vnd.radiance'
        if hdri_file.filename.lower().endswith('.exr'):
            hdri_mimetype = 'image/vnd.radiance'
        elif hdri_file.filename.lower().endswith('.hdr'):
            hdri_mimetype = 'image/vnd.radiance'

        preview_mimetype = preview_file.mimetype if preview_file else 'image/jpeg'

        new_hdri = HDRI(
            name=hdri_name,
            file_path=hdri_data,
            file_path_mimetype=hdri_mimetype,
            preview_path=preview_data,
            preview_path_mimetype=preview_mimetype
        )
        
        db.session.add(new_hdri)
        db.session.commit()

        return jsonify({"success": True, "message": "HDRI and preview uploaded successfully."})

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        db.session.rollback()
        return jsonify({"success": False, "message": "An unexpected error occurred."}), 500

@bp.route('/model/<int:model_id>')
def get_model(model_id):
    try:
        logging.info(f"Redirecting to load model page for model_id: {model_id}")
        return redirect(url_for('main.load_model', model_id=model_id))
    except Exception as e:
        logging.error(f"Error in get_model route: {str(e)}")
        return str(e), 500

model_cache = {}

@bp.route('/load_model/<int:model_id>')
def load_model(model_id):
    try:
        if model_id in model_cache:
            file_data = model_cache[model_id]
        else:
            file_result = db.session.get(File, model_id)
            
            if not file_result:
                logging.warning(f"Model not found for model_id: {model_id}")
                return "Model not found", 404
            
            file_data = {
                'id': model_id,
                'name': file_result.file_name,
                'like_count': file_result.like_count,
                'download_count': file_result.download_count,
                'comment_count': file_result.comment_count,
            }
            model_cache[model_id] = file_data

        logging.info(f"Successfully loaded model data for model_id: {model_id}")
        return render_template('hdri_projection_7.html', file=file_data)

    except Exception as e:
        logging.error(f"Error in load_model route for model_id {model_id}: {str(e)}")
        return str(e), 500

@bp.route('/api/model/<int:model_id>')
def serve_model(model_id):
    try:
        config_record = db.session.get(File, model_id)
        if config_record:
            return Response(decompress_file(config_record.file_path_glb), mimetype='model/gltf-binary')
        else:
            return jsonify({"error": "Model not found"}), 404
    except Exception as e:
        logging.error(f"Error serving model: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/hdri')
def get_hdri_list():
    try:
        hdris = HDRI.query.with_entities(HDRI.id).all()
        hdri_list = [{'id': h.id, 'preview_path': f'/api/hdri/preview/{h.id}'} for h in hdris]

        default_hdri_id = hdri_list[0]['id'] if hdri_list else None
        return jsonify({'hdri_list': hdri_list, 'default_hdri_id': default_hdri_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/api/hdri/preview/<int:hdri_id>')
def get_hdri_preview(hdri_id):
    try:
        hdri = db.session.get(HDRI, hdri_id)
        if hdri:
            return Response(decompress_file(hdri.preview_path), mimetype=hdri.preview_path_mimetype)
        else:
            return jsonify({"error": "Preview not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/api/hdri/<int:hdri_id>')
def get_hdri_file(hdri_id):
    try:
        hdri = db.session.get(HDRI, hdri_id)
        if hdri:
            return Response(decompress_file(hdri.file_path), mimetype=hdri.file_path_mimetype)
        else:
            return jsonify({"error": "HDRI not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/api/gallery-images/<int:model_id>', methods=['GET'])
def get_gallery_images(model_id):
    try:
        gallery_files = GalleryFile.query.filter_by(file_id=model_id).all()
        image_data_list = []
        for gf in gallery_files:
            decompressed_data = decompress_file(gf.file_path)
            base64_encoded = base64.b64encode(decompressed_data).decode('utf-8')
            image_data_list.append({
                'data': f"data:{gf.images_mimetype};base64,{base64_encoded}",
                'mime_type': gf.images_mimetype
            })
        return jsonify(image_data_list)
    except Exception as e:
        print(f"Erreur: {e}")
        return jsonify({'error': 'Erreur de chargement des images'}), 500

@bp.route('/upload_page_hdri')
def upload_page_hdri():
    return render_template('upload_hdri.html')


@bp.route('/skills')
def skills():
    return render_template('skills.html')

@bp.route('/gallery')
def gallery():
    return render_template('gallery_iframe.html')

@bp.route('/storyline')
def storyline():
    return render_template('storyline.html')

@bp.route('/download', methods=['POST'])
def download_file():
    email = request.form.get('email')
    file_id = request.form.get('file_id')

    if not email or not file_id:
        return "Email and file_id are required", 400

    if not validate_email(email):
        return "Invalid email format", 400

    try:
        file_record = db.session.get(File, file_id)
        if not file_record:
            abort(404, description="File not found")

        # Record download
        download = Download(email=email, file_id=file_id)
        db.session.add(download)
        file_record.download_count += 1
        db.session.commit()

        return send_file(
            io.BytesIO(decompress_file(file_record.file_path_zip)),
            as_attachment=True,
            download_name=f"{file_record.file_name}.zip",
            mimetype='application/zip'
        )

    except Exception as e:
        return f"Error: {e}", 500

@bp.route('/comment', methods=['POST'])
def add_comment():
    email = request.form.get('email')
    file_id = request.form.get('file_id')
    comment = request.form.get('comment')

    if not email or not file_id or not comment:
        return "Email, file_id, and comment are required", 400

    if not validate_email(email):
        return "Invalid email format", 400

    try:
        new_comment = Comment(email=email, file_id=file_id, comment=comment)
        db.session.add(new_comment)
        
        file_record = db.session.get(File, file_id)
        if file_record:
            file_record.comment_count += 1
            
        db.session.commit()
        return "Comment added successfully", 200
    except Exception as e:
        return f"Error: {e}", 500

@bp.route('/like', methods=['POST'])
def add_like():
    email = request.form.get('email')
    file_id = request.form.get('file_id')

    if not email or not file_id:
        return "Email and file_id are required", 400

    if not validate_email(email):
        return "Invalid email format", 400

    try:
        like = Like(email=email, file_id=file_id)
        db.session.add(like)
        
        file_record = db.session.get(File, file_id)
        if file_record:
            file_record.like_count += 1
            
        db.session.commit()
        return "Like added successfully", 200
    except Exception as e:
        return f"Error: {e}", 500

@bp.route('/comments/<int:file_id>')
def view_comments(file_id):
    try:
        file_record = db.session.get(File, file_id)
        if not file_record:
            return "File not found", 404
        
        comments_list = Comment.query.filter_by(file_id=file_id).order_by(Comment.date.desc()).all()
        return render_template('comments.html', comments=comments_list, file_name=file_record.file_name)

    except Exception as e:
        return f"Error: {e}", 500

def validate_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return False
    
    domain = email.split('@')[1]
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        return False