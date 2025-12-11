from flask import render_template, Blueprint
from app.models import Video

bp = Blueprint("youtube_videos", __name__, static_folder='static')

def get_videos_from_db():
    return Video.query.all()

@bp.route('/youtube_videos')
def youtube_videos():
    videos = get_videos_from_db()
    return render_template('youtube/youtube_videos.html', videos=videos)
