from flask import (Blueprint, jsonify, Response, redirect, url_for,
                   request, session, send_from_directory, render_template, send_file, abort, current_app)
import os
from app.extensions import db, limiter
from app.models import File, GalleryFile, HDRI, Comment, Like, Download, StorylineItem
from flask_login import login_required, current_user
import io
import base64
import logging
from werkzeug.utils import secure_filename
import requests
import re
import dns.resolver
import os
from app.utils import get_location_from_ip, allowed_file, to_base32, compress_file, decompress_file

# Create blueprint
bp = Blueprint('main', __name__)

def convert_gdrive_to_direct_url(url):
    """Convert Google Drive sharing URL to direct download URL"""
    if not url:
        return None
    # Extract file ID from various Google Drive URL formats
    # Format 1: https://drive.google.com/file/d/FILE_ID/view?usp=sharing
    # Format 2: https://drive.google.com/open?id=FILE_ID
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if not match:
        match = re.search(r'id=([a-zA-Z0-9_-]+)', url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url  # Return original if not a Google Drive URL

def proxy_external_file(url, mimetype=None):
    """Fetch an external file and return it as a Response (proxying through server).
    Handles Google Drive's virus scan warning for large files."""
    try:
        direct_url = convert_gdrive_to_direct_url(url)
        
        # Use a session to handle cookies (needed for Google Drive confirmation)
        session = requests.Session()
        resp = session.get(direct_url, timeout=60, stream=True)
        
        # Check if Google Drive is asking for confirmation (large file warning)
        if 'drive.google.com' in direct_url and b'confirm=' not in resp.content[:1000]:
            # Check if content is HTML (confirmation page)
            content_type = resp.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                # Extract the confirmation token from the response
                html_content = resp.content.decode('utf-8', errors='ignore')
                
                # Look for the confirm parameter in the download link
                confirm_match = re.search(r'confirm=([0-9A-Za-z_-]+)', html_content)
                if confirm_match:
                    confirm_token = confirm_match.group(1)
                    # Retry with confirmation token
                    confirmed_url = f"{direct_url}&confirm={confirm_token}"
                    resp = session.get(confirmed_url, timeout=60, stream=True)
                else:
                    # Try adding confirm=t (works for some files)
                    confirmed_url = f"{direct_url}&confirm=t"
                    resp = session.get(confirmed_url, timeout=60, stream=True)
        
        if resp.status_code == 200:
            # Check if we still got HTML instead of the file
            response_content_type = resp.headers.get('Content-Type', '')
            if 'text/html' in response_content_type:
                logging.error(f"Google Drive returned HTML instead of file for {url}")
                return jsonify({"error": "Failed to download file from Google Drive - file may require authentication"}), 403
            
            content_type = mimetype or response_content_type or 'application/octet-stream'
            return Response(resp.content, mimetype=content_type)
        else:
            return jsonify({"error": f"Failed to fetch file: {resp.status_code}"}), resp.status_code
    except Exception as e:
        logging.error(f"Error proxying file from {url}: {e}")
        return jsonify({"error": "Failed to fetch external file"}), 500

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

        if file:
            if file.banner_url:
                return redirect(file.banner_url)
            elif file.banner_path:
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



@bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    try:
        model_name = request.form.get('model_name')
        year = request.form.get('year')
        
        if not model_name or not year:
             return jsonify({"success": False, "message": "Model Name and Year are required"}), 400

        # URLs
        banner_url = request.form.get('banner_url')
        glb_url = request.form.get('glb_url')
        zip_url = request.form.get('zip_url')

        # Files
        banner_file = request.files.get('banner')
        glb_file = request.files.get('glb_file')
        zip_file = request.files.get('zip_file')
        gallery_files = request.files.getlist('gallery')

        # Data placeholders
        banner_data = None
        banner_mimetype = None
        glb_data = None
        glb_mimetype = None
        zip_data = None
        zip_mimetype = None

        # Logic: GLB - Support both URL and File (URL preferred if both?)
        # If URL is present, we use it. If not, we check for file.
        if not glb_url and not (glb_file and glb_file.filename):
             return jsonify({"success": False, "message": "GLB Model (File or URL) is required"}), 400
        
        # Process GLB File if provided (and no URL or if we want to allow replacing?)
        # Let's say if File is provided, we store it. If URL is provided, we store it.
        if glb_file and glb_file.filename:
             if not allowed_file(glb_file.filename, ['glb']):
                 return jsonify({"success": False, "message": "Invalid GLB file"}), 400
             glb_data = compress_file(glb_file.read())
             glb_mimetype = glb_file.mimetype

        # Logic: Banner
        if banner_url:
            pass # Use URL
        elif banner_file and banner_file.filename:
             banner_data = compress_file(banner_file.read())
             banner_mimetype = banner_file.mimetype

        # Logic: Zip
        if zip_file and zip_file.filename:
             zip_data = compress_file(zip_file.read())
             zip_mimetype = zip_file.mimetype

        new_file = File(
            file_name=model_name,
            year=int(year),
            banner_path=banner_data,
            banner_mimetype=banner_mimetype,
            file_path_glb=glb_data,
            file_path_glb_mimetype=glb_mimetype,
            file_path_zip=zip_data,
            file_path_zip_mimetype=zip_mimetype,
            banner_url=banner_url,
            file_path_glb_url=glb_url,
            file_path_zip_url=zip_url,
            added_by=current_user.username,
            location='Unknown' 
        )

        db.session.add(new_file)
        db.session.flush() # Get ID

        # Gallery Images (keeping as file uploads for now, could act similarly)
        if gallery_files:
            for file in gallery_files:
                if file and file.filename:
                    gallery_data = compress_file(file.read())
                    gallery_mimetype = file.mimetype
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
        hdri_name = request.form.get('hdri_name')
        # Check for URL or File
        hdri_url = request.form.get('hdri_url')
        preview_url = request.form.get('preview_url')
        
        hdri_file = request.files.get('hdri_file')
        preview_file = request.files.get('preview_file')

        if not hdri_name:
             return jsonify({"success": False, "message": "HDRI Name is required"}), 400

        hdri_data = None
        hdri_mimetype = None
        preview_data = None
        preview_mimetype = None

        # Logic for HDRI: URL OR File
        if not hdri_url and not (hdri_file and hdri_file.filename):
             return jsonify({"success": False, "message": "HDRI File or URL is required"}), 400
        
        if hdri_file and hdri_file.filename:
             if not allowed_file(hdri_file.filename, ['hdr', 'exr']):
                  return jsonify({"success": False, "message": "Invalid HDRI file type"}), 400
             hdri_data = compress_file(hdri_file.read())
             hdri_mimetype = hdri_file.mimetype

        # Logic for Preview: URL OR File
        if not preview_url and not (preview_file and preview_file.filename):
             return jsonify({"success": False, "message": "Preview Image or URL is required"}), 400
             
        if preview_file and preview_file.filename:
             preview_data = compress_file(preview_file.read())
             preview_mimetype = preview_file.mimetype

        new_hdri = HDRI(
            name=hdri_name,
            file_path=hdri_data,
            file_path_mimetype=hdri_mimetype,
            preview_path=preview_data,
            preview_path_mimetype=preview_mimetype,
            file_path_url=hdri_url,
            preview_path_url=preview_url
        )
        
        db.session.add(new_hdri)
        db.session.commit()

        return jsonify({"success": True, "message": "HDRI added successfully."})

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
            if config_record.file_path_glb_url:
                # Proxy the file to avoid CORS issues with Google Drive
                response = proxy_external_file(config_record.file_path_glb_url, 'model/gltf-binary')
                # Add cache headers if proxying succeeded
                if isinstance(response, Response):
                    # Cache for 0 seconds (revalidate immediately) to fix corruption issues
                    response.headers['Cache-Control'] = 'public, max-age=0' 
                return response
            elif config_record.file_path_glb:
                response = Response(decompress_file(config_record.file_path_glb), mimetype='model/gltf-binary')
                # Cache for 0 seconds
                response.headers['Cache-Control'] = 'public, max-age=0'
                return response
            else:
                 return jsonify({"error": "Model source not found"}), 404
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
            if hdri.preview_path_url:
                # Proxy the file to avoid CORS issues
                return proxy_external_file(hdri.preview_path_url, hdri.preview_path_mimetype or 'image/jpeg')
            elif hdri.preview_path:
                return Response(decompress_file(hdri.preview_path), mimetype=hdri.preview_path_mimetype)
            else:
                 return jsonify({"error": "Preview content not found"}), 404
        else:
            return jsonify({"error": "Preview not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/api/hdri/<int:hdri_id>')
def get_hdri_file(hdri_id):
    try:
        hdri = db.session.get(HDRI, hdri_id)
        if hdri:
             if hdri.file_path_url:
                # Proxy the file to avoid CORS issues
                return proxy_external_file(hdri.file_path_url, hdri.file_path_mimetype or 'application/octet-stream')
             elif hdri.file_path:
                return Response(decompress_file(hdri.file_path), mimetype=hdri.file_path_mimetype)
             else:
                return jsonify({"error": "HDRI content not found"}), 404
        else:
            return jsonify({"error": "HDRI not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/api/gallery-images/<int:model_id>', methods=['GET'])
def get_gallery_images(model_id):
    try:
        # Fetch just the IDs and Mimetypes to keep the payload light
        gallery_files = GalleryFile.query.filter_by(file_id=model_id).with_entities(GalleryFile.id, GalleryFile.images_mimetype).all()
        image_list = []
        for gf in gallery_files:
            image_list.append({
                'url': url_for('main.serve_gallery_image', image_id=gf.id),
                'mime_type': gf.images_mimetype or 'image/jpeg'
            })
        return jsonify(image_list)
    except Exception as e:
        logging.error(f"Error loading gallery list: {e}")
        return jsonify({'error': 'Erreur de chargement des images'}), 500

@bp.route('/gallery-image/<int:image_id>')
def serve_gallery_image(image_id):
    try:
        image = db.session.get(GalleryFile, image_id)
        if hasattr(image, 'file_path') and image.file_path:
            decompressed_data = decompress_file(image.file_path)
            # Cache for 1 month
            response = Response(decompressed_data, mimetype=image.images_mimetype or 'image/jpeg')
            response.headers['Cache-Control'] = 'public, max-age=2592000'
            return response
        return "Image not found", 404
    except Exception as e:
        logging.error(f"Error serving gallery image {image_id}: {e}")
        return "Error", 500

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
    items = StorylineItem.query.order_by(StorylineItem.order.asc(), StorylineItem.date_added.desc()).all()
    return render_template('storyline.html', items=items)

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

        if file_record.file_path_zip_url:
            return redirect(file_record.file_path_zip_url)

        if not file_record.file_path_zip:
             return "File content not found", 404

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

@bp.route('/trap/bot-check')
def bot_trap():
    """Honeypot route for scrapers. Humans won't click this."""
    try:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        agent = request.headers.get('User-Agent', 'Unknown')
        # Log to console/file
        print(f"\n[SECURITY ALERT] SCRAPER DETECTED at /trap/bot-check")
        print(f"IP: {ip}")
        print(f"User-Agent: {agent}\n")
        logging.warning(f"SCRAPER TRAPPED: IP={ip}, UA={agent}")
        return "System Status: Nominal", 200 # Return 200 to keep them engaged/confused? Or 403.
    except Exception:
        return "Error", 500

@bp.route('/sitemap.xml', methods=['GET'])
def sitemap():
    """Generate sitemap.xml dynamically."""
    from flask import make_response
    pages = []
    # Static routes
    for rule in current_app.url_map.iter_rules():
        if "GET" in rule.methods and len(rule.arguments) == 0:
            if not rule.rule.startswith('/trap') and not rule.rule.startswith('/admin'): # Exclude trap/admin
                 pages.append(f"https://princegildasmk.up.railway.app{rule.rule}")
    
    sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""
    for page in pages:
        sitemap_xml += f"""  <url>
    <loc>{page}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
"""
    sitemap_xml += "</urlset>"
    
    response = make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"
    return response

@bp.route('/api/scenes', methods=['GET'])
def get_scenes():
    """Dynamically list all GLB scenes in the static/scene3D directory."""
    try:
        app_dir = os.path.dirname(os.path.abspath(__file__))
        scenes_dir = os.path.join(app_dir, 'static', 'scene3D')
        
        scenes = []
        if os.path.exists(scenes_dir):
            files = [f for f in os.listdir(scenes_dir) if f.lower().endswith('.glb')]
            # Sort for consistent order
            files.sort() 
            
            # Add cache busting with file modification time
            for f in files:
                file_path = os.path.join(scenes_dir, f)
                # Get file modification timestamp for cache busting
                mtime = int(os.path.getmtime(file_path))
                scene_url = f"/static/scene3D/{f}?v={mtime}"
                scenes.append(scene_url)
        
        return jsonify(scenes)
    except Exception as e:
        logging.error(f"Error listing scenes: {e}")
        return jsonify({"error": str(e)}), 500