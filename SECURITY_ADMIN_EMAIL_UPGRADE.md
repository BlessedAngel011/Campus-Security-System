# Security/Admin Email Upgrade

This version extends the working email system to Security Officer and Admin accounts.

- Admin Add User now requires an email address.
- Admin Manage Users displays and can update account email addresses.
- Admin-managed email addresses are marked verified.
- Forgot Password now supports active verified Student, Security Officer and Admin accounts.
- High-priority incident and SOS alerts are sent to every active, verified Security Officer account with an email address.
- Optional SECURITY_ALERT_EMAILS values in .env are still supported and combined with Security Officer account emails.
- Duplicate email protection remains enforced by the database.
