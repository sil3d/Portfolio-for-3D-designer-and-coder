import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models import StorylineItem
import json

def dump_data():
    app = create_app()
    with app.app_context():
        items = StorylineItem.query.order_by(StorylineItem.order.asc()).all()
        data = []
        for item in items:
            data.append({
                'title': item.title,
                'description': item.description,
                'media_url': item.media_url,
                'is_video': item.is_video,
                'order': item.order
            })
        
        # Ensure directory exists
        os.makedirs(os.path.join('app', 'data'), exist_ok=True)
        filepath = os.path.join('app', 'data', 'storyline_data.json')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print(f"Successfully dumped {len(items)} items to {filepath}")

def seed_data():
    app = create_app()
    with app.app_context():
        filepath = os.path.join('app', 'data', 'storyline_data.json')
        if not os.path.exists(filepath):
            print(f"Error: {filepath} not found.")
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Optional: Clear existing data? 
        # For now, let's just add if not exists (upsert logic is complex without unique key besides ID)
        # Simplest is to clear and reload for a "full sync"
        print("Clearing existing Storyline items...")
        StorylineItem.query.delete()
        
        print(f"Seeding {len(data)} items...")
        for entry in data:
            new_item = StorylineItem(
                title=entry['title'],
                description=entry['description'],
                media_url=entry['media_url'],
                is_video=entry['is_video'],
                order=entry['order']
            )
            db.session.add(new_item)
        
        db.session.commit()
        print("Database populated successfully.")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'dump':
            dump_data()
        elif sys.argv[1] == 'seed':
            seed_data()
        else:
            print("Usage: python -m app.seed_storyline [dump|seed]")
    else:
        print("Usage: python -m app.seed_storyline [dump|seed]")
