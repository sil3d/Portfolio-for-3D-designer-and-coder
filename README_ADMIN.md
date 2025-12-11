# Admin & Configuration Guide

This guide covers the administrative setup, including secure login, email configuration, and content management.

## 1. Environment Configuration (`.env`)

The application relies on a `.env` file for sensitive information. **Do not share this file.**

1.  Copy `.env.example` to a new file named `.env`.
2.  Fill in the following details:

### Database
Update `DB_PASSWORD` and the `SQLALCHEMY_DATABASE_URI` with your MySQL root password.

### Security
- `SECRET_KEY`: Random string for session security.
- `LOGIN_SECRET_KEY`: Another random string used for admin login verification.

### Email (SMTP) Setup
The app uses Gmail SMTP to send 2FA codes and contact form messages. logic uses **Google App Passwords**, not your regular password.

**How to get a Google App Password:**
1.  Go to your [Google Account Security page](https://myaccount.google.com/security).
2.  Enable **2-Step Verification** if not already enabled.
3.  Search for **"App Passwords"** in the search bar or look under the 2-Step Verification section.
4.  Create a new App Password:
    - **App**: Mail
    - **Device**: Windows Computer (or custom name)
5.  Copy the 16-character code generated.
6.  Paste it into your `.env` file:
    ```ini
    SMTP_USER=your_email@gmail.com
    SMTP_PASSWORD=your_16_char_code_here  # Remove spaces
    ```

## 2. Creating an Admin User
Run this command from the project root directory:

```powershell
python -m app.register_admin_user
```

make sure to use you real email because the admin will be sent a 2FA code.
*Follow the prompts to set your Admin Email and Password.*

> **Note:** If you get a "Module not found" error, make sure you are in the root folder (`portfolio`) and use `python -m app...` instead of `python app/...`.

## 3. Accessing the Admin Panel
1.  Start the server (`.\run_server.bat`).
2.  Navigate to: [http://localhost:5000/admin/login](http://localhost:5000/admin/login)
3.  Log in with your Admin credentials.
4.  Enter the 2FA code sent to your email.

## 4. Managing Content
- **Upload Model**: Add new GLB files with banners.
- **Upload HDRI**: Add HDR environment maps.
- **Manage Files**: Edit or delete existing content.
