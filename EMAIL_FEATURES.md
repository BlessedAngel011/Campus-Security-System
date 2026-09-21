# Email Features

The Campus Security Management System now includes:

- Student email verification with 6-digit codes
- Welcome email after successful verification
- Resend verification code with expiry/rate protection
- Forgot Password using the verified Student email
- 6-digit password reset codes
- Password changed security notification
- Incident submission confirmation emails
- Privacy-aware anonymous report confirmation
- SOS receipt confirmation without repeating precise GPS coordinates
- Incident status update emails (Pending / In Progress / Resolved)
- High-priority and SOS alert emails for Security
- Admin password-reset notification emails
- Admin account enabled/disabled notification emails
- Account page showing full name, student number, email and verification status
- Change Email Address with verification of the new address before replacement

## Mail settings

Use `.env` for credentials. Gmail SMTP port 465/SSL is configured in `.env.example` because that port was confirmed reachable on the development network.

Never commit `.env` to Git.
