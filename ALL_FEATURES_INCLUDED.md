# Integrated Feature Upgrade

This build preserves the existing Student, Security, Admin, PWA, anonymous-reporting and email features and adds the requested roadmap in one package:

1. Profile v2 database fields: first name, last name, student/staff number, phone number, email, role and password; existing full_name/student_number retained for backward compatibility.
2. GPS SOS with latitude/longitude storage plus manual location fallback.
3. Dedicated emergency_alerts lifecycle: ACTIVE → ASSIGNED → RESPONDING → RESOLVED.
4. Security officer records with AVAILABLE / BUSY / OFF_DUTY state.
5. Optional officer GPS and Haversine nearest-officer distance calculation; Security Control remains responsible for assignment.
6. Incident evidence upload metadata and secure generated filenames.
7. In-app notification centre and unread count context.
8. Campus GIS map view using Leaflet/OpenStreetMap plus campus_locations table.
9. Admin analytics views for type, location, priority, incident status and emergency status.
10. Audit/security log table and logging hooks for new critical workflows plus incident/status changes.

Run `init_db.py` once before starting the upgraded app. Existing tables/data are migrated rather than dropped.
