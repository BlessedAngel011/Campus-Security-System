# OTP Email and Password Reset Setup

The backend sends OTPs through SMTP. Credentials are read from environment variables and must never be committed to GitHub.

Required variables:
- `DB_PASSWORD`
- `ADMIN_TOKEN_SECRET`
- `MAIL_HOST` (default: smtp.gmail.com)
- `MAIL_PORT` (default: 587)
- `MAIL_USERNAME`
- `MAIL_PASSWORD` (for Gmail, use an App Password rather than the normal account password)
- `MAIL_FROM` (normally the same as MAIL_USERNAME)

Student registration email rule: `<student-number>@ufh.ac.za`.
Staff registration accepts their official `@ufh.ac.za` email.

OTP behavior:
- 6 digits
- expires after 10 minutes
- one-time use
- resend limited to once per 60 seconds
- admin OTP is emailed and is no longer returned by the API
- password reset uses a separate OTP purpose
