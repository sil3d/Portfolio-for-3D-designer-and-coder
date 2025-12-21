# Security & Algorithms Documentation

This document outlines the security measures and algorithms implemented in the "So I Learn 3D" Portfolio application to protect against common web vulnerabilities.

## 1. Authentication & Authorization
**Algorithm**: `Bcrypt` (via `werkzeug.security`)
-   **Implementation**: Passwords are never stored in plain text. They are hashed using Bcrypt before storage.
-   **Session Management**: `Flask-Login` handles user sessions securely, ensuring that cookies are signed and tamper-proof (using Flask's `SECRET_KEY`).
-   **Access Control**: Critical routes like `/upload` and `/upload_hdri` are protected with `@login_required`, ensuring only authenticated administrators can modify content.

## 2. CSRF Protection (Cross-Site Request Forgery)
**Algorithm**: Synchronizer Token Pattern
-   **Implementation**: `Flask-WTF`'s `CSRFProtect` is enabled globally.
-   **Mechanism**: A unique, random token is generated for each session/request. This token must be present in all state-changing requests (POST, PUT, DELETE).
-   **Forms**: All HTML forms include a hidden `<input name="csrf_token">`.
-   **AJAX**: All JavaScript Fetch/XHR calls include the token (via `FormData` or Headers), read from a `<meta>` tag in the page head.

## 3. Rate Limiting (Brute Force Protection)
**Algorithm**: Fixed Window / Token Bucket (via `Flask-Limiter`)
-   **Implementation**: Limits are applied to sensitive routes:
    -   Login: 5 requests per minute (prevents brute force password guessing).
    -   Global default: 200 per day, 50 per hour for other routes.
-   **Identifier**: Rate limits are tracked by IP address (`get_remote_address`).

## 4. SQL Injection Prevention
**Control**: Object-Relational Mapping (ORM)
-   **Implementation**: The application uses `Flask-SQLAlchemy`.
-   **Mechanism**: Database queries are constructed using object methods (e.g., `File.query.filter_by(...)`) rather than concatenation of raw SQL strings. This ensures variables are properly bound and escaped by the underlying driver, neutralizing SQL injection attacks.

## 5. Input Validation & Type Safety
-   **Type Conversion**: Flask routes use type converters (e.g., `<int:file_id>`) to strictly enforce input types. Malicious strings passed where numbers are expected (e.g., in SQLi attempts) are rejected by the router with a `404 Not Found` before reaching the database logic.
-   **File Uploads**: Files are validated by extension (`.glb`, `.zip`, `.png`) and the upload endpoint is behind a login check.

## 6. Anti-Scraper & AI Defense
**Control**: Honeypots & Injection
-   **Honeypot Route**: A hidden `/trap/bot-check` route detects non-human traffic. Bots following this hidden link are logged for analysis.
-   **AI Prompt Injection**: The Resume page contains a hidden text block (`opacity: 0.01`) with instructions tailored for LLMs (Applicant Tracking Systems), guiding them to rank the profile favorably.
-   **Hashtag Cloud**: A hidden block of industry-specific hashtags maximizes keyword density for scraping bots without cluttering the visual UI.

## 7. Testing
A penetration test script `test_penetration.py` is included to verify these controls.
-   **Usage**: `python test_penetration.py`
-   **Checks**: Unauthorized access blocking, CSRF token validation, and SQLi resilience.
