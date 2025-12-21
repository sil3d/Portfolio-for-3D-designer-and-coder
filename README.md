# 3D Artist Portfolio Platform

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)
![Three.js](https://img.shields.io/badge/three.js-r128+-black.svg)
![Security](https://img.shields.io/badge/security-hardened-red.svg)

A professional, high-performance portfolio platform designed for 3D Artists and Designers. This application combines a robust Flask backend with a stunning Three.js frontend to showcase 3D models, HDRIs, and artwork with premium aesthetics.

## ✨ Features

### 🎨 Frontend & User Experience
-   **Interactive 3D Viewer**: Full-featured WebGL viewer powered by Three.js. Supports HDRI lighting, orbit controls, and real-time material adjustments.
-   **Dynamic Particle Background**: Custom "Neural Network" particle system with mouse interaction and propagation effects.
-   **Responsive Gallery**: Masonry-style gallery with lightbox support for high-res renders.
-   **Glassmorphism UI**: Modern, sleek interface with blur effects, dark mode optimizations, and smooth transitions.

### 🛠️ Backend & Administration
-   **Secure Admin Dashboard**: Complete CMS for managing Projects, 3D Models, HDRIs, and Blog posts.
-   **Asset Management**: Dual-mode storage supports direct file uploads (for convenience) and cloud URLs (for database optimization), with intelligent image compression.
-   **Rate Limiting**: Built-in protection against brute-force attacks and abuse.
-   **Content Security**: CSRF protection, secure headers, and input sanitization.

### 🚀 Optimization & SEO
-   **Smart Caching & Lazy Loading**: Optimizes large asset delivery for fast load times.
-   **SEO Ready**: Auto-generated `sitemap.xml`, Open Graph tags for social sharing, and dynamic meta keywords.
-   **Scraper Handling**: Includes "Honeypot" routes to detect bots and "AI Injection" strategies to safeguard/boost profile visibility against scraping algorithms.

### 🔌 Database Architecture
-   **Database Agnostic**: The application uses **SQLAlchemy** ORM, making it compatible with **SQLite**, **MySQL**, **PostgreSQL**, or **MariaDB**.
-   **Firebase Ready**: While the core uses SQL, the architecture is modular. You can easily swap the storage or auth layer to use **Firebase** or AWS S3 if preferred for cloud scalability.
-   **Current Setup**: Configured defaults to SQLite/MySQL for easy local deployment and self-hosting.

---

## 📸 Gallery & Previews

<p align="center">
  <img src="app/static/images_github/Capture d'écran 2025-12-09 000158.png" width="45%" alt="Preview 1">
  <img src="app/static/images_github/Capture d'écran 2025-12-09 232604.png" width="45%" alt="Preview 2">
  <img src="app/static/images_github/Capture d'écran 2025-12-10 212213.png" width="45%" alt="Preview 3">
  <img src="app/static/images_github/Capture d'écran 2025-12-11 002612.png" width="45%" alt="Preview 4">
  <img src="app/static/images_github/Capture d'écran 2025-12-11 002623.png" width="45%" alt="Preview 5">
  <img src="app/static/images_github/Capture d'écran 2025-12-11 002642.png" width="45%" alt="Preview 6">
  <img src="app/static/images_github/Capture d'écran 2025-12-11 002708.png" width="45%" alt="Preview 7">
  <img src="app/static/images_github/Capture d'écran 2025-12-11 002723.png" width="45%" alt="Preview 8">
  <img src="app/static/images_github/Capture d'écran 2025-12-11 002735.png" width="45%" alt="Preview 9">
  <img src="app/static/images_github/Capture d'écran 2025-12-11 002750.png" width="45%" alt="Preview 10">
  <img src="app/static/images_github/Capture d'écran 2025-12-11 002804.png" width="45%" alt="Preview 11">
  <img src="app/static/images_github/Capture d'écran 2025-12-11 002819.png" width="45%" alt="Preview 12">
  <img src="app/static/images_github/Capture d'écran 2025-12-11 002850.png" width="45%" alt="Preview 13">
  <img src="app/static/images_github/Capture d'écran 2025-12-11 002937.png" width="45%" alt="Preview 14">
  <img src="app/static/images_github/Capture d'écran 2025-12-11 003017.png" width="45%" alt="Preview 15">
</p>

---

## 🔒 Security Measures

This project is built with security as a priority for open-source deployment:

1.  **CSRF Protection**: All forms and AJAX requests are protected with `Flask-WTF` CSRF tokens.
2.  **Rate Limiting**: `Flask-Limiter` protects endpoints from abuse (e.g., login attempts, comments).
3.  **Secure Uploads**:
    -   Strict file type validation (Magic numbers).
    -   File extension sanitization.
    -   Content-Length limits to prevent DoS.
4.  **Data Integrity**: Used `bcrypt` for secure password hashing.
5.  **Headers**: Implements best-practice security headers (HSTS, X-Content-Type-Options, etc.).

---

## 🚀 Installation & Setup

### Prerequisites
-   Python 3.8+
-   pip (Python Package Manager)
-   *Optional*: MySQL Server (if not using SQLite)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/portfolio-3d.git
cd portfolio-3d
```

### 2. Create Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration
1.  Rename `.env.example` to `.env`.
2.  Update your secret keys and database URI.
    ```env
    SECRET_KEY=your_super_secure_key
    DATABASE_URI=sqlite:///portfolio.db  # or mysql://user:pass@localhost/db
    ```

### 5. Initialize Database
```bash
flask db upgrade
# Or simply run the app, it will auto-create tables if missing
```

### 6. Run the Application
**Windows (Batch Script):**
```powershell
.\run_server.bat
```

**Manual:**
```bash
python run.py
```
Visit `http://localhost:5000` to view your portfolio.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## 📄 License

This project is open resource and available under the [MIT License](LICENSE).