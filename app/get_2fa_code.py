from app import create_app
from app.models import TwoFactor, Admin
from app.extensions import db

app = create_app()
with app.app_context():
    # Get latest code
    latest = TwoFactor.query.order_by(TwoFactor.id.desc()).first()
    if latest:
        print(f"LATEST_CODE:{latest.verification_code}")
    else:
        print("NO_CODE_FOUND")
