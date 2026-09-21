# Integrated workflow notes

This build keeps the existing Student, Security, Admin and email features and connects the newer modules into shared workflows.

## Incident workflow
Student profile -> incident report -> priority -> evidence -> Security in-app notification -> Security status change -> Student in-app + email update -> analytics + audit log.

## SOS workflow
Student GPS/manual fallback -> incident record + dedicated emergency record -> Security in-app + email alert -> available officer assignment -> Student/officer notification -> assigned officer accepts -> RESPONDING -> RESOLVED -> linked incident status is synchronized -> officer becomes AVAILABLE again -> audit trail.

## Privacy
Anonymous reports retain the internal user relationship but operational identity fields remain anonymous. Student campus-map views are limited to that student's own GPS-enabled reports and emergencies. Security/Admin map views can show operational records.

## Important integration rules
- `incidents.status` remains the student-facing report status.
- `emergency_alerts.status` controls the SOS lifecycle: ACTIVE, ASSIGNED, RESPONDING, RESOLVED.
- Emergency transitions synchronize the linked incident to In Progress / Resolved.
- Security Officer accounts have a `security_officers` record; newly created/promoted Security accounts are synchronized automatically.
- High-priority incidents use both email alerts and in-app Security notifications.
- Evidence is attached to the same incident ID used by My Reports and Security views.
