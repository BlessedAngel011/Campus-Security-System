CAMPUS SECURITY MOBILE APP - STAGE 2

Folders:
1. mobile: Open this folder in VS Code.
2. backend: Open this folder in IntelliJ IDEA.

MOBILE SETUP
1. Copy .env.example to .env.
2. While testing on the same Windows computer, use:
   BACKEND_URL=http://localhost:8080
3. When using a physical phone, replace YOUR_COMPUTER_IP with the computer's
   IPv4 address. The phone and computer must use the same Wi-Fi network.
4. In PowerShell install the requirements with:
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
5. Start the app with:
   .\.venv\Scripts\python.exe main.py

BACKEND SETUP
1. Open the backend folder in IntelliJ IDEA.
2. Check src/main/resources/application.properties for your MySQL username,
   password and database name.
3. Run CampusSecuritySystemApplication.

IMPORTANT OFFICER REQUIREMENT
The security_officers.employee_number value must be the same as the officer's
users.student_staff_number value. This links the officer login account to the
security officer profile.

HOW STAGE 2 WORKS
- Student/staff signs in once and presses the large Emergency SOS button
  3 times within 5 seconds.
- If all 3 presses are not completed in time, activation resets automatically
  and no emergency is sent. This reduces accidental false alerts.
- No form is shown and the user does not enter any information.
- The app automatically captures the phone GPS location and sends the alert,
  while Spring Boot links it to the authenticated user's personal details.
- Spring Boot stores it in emergency_alerts and assigns the nearest AVAILABLE
  officer who has a recent officer_locations entry.
- The officer signs into the same app, sets themselves AVAILABLE, opens
  Emergency Alerts, and updates the alert status.

COMPLETED STUDENT/STAFF UI
- Emergency SOS: requires 3 presses within 5 seconds, then sends GPS and the
  logged-in user's account details automatically.
- Report an Incident: incident type, database campus location, severity and
  description are saved through Spring Boot.
- My Reports: displays the signed-in user's report history and current status.
- Emergency Contacts: provides tap-to-call UFH Alice Campus Security, GBV,
  Police, Ambulance and mobile emergency numbers.
- Personal Emergency Contacts: users can save trusted contacts locally on
  their device, view them, call them and clear the saved list.
- Notifications: displays user notifications and allows them to be marked read.

LOCATION SETUP
Run database_user_locations.sql once in MySQL Workbench. The mobile incident
form calls GET /api/locations and fills its location list from these database
records. If the screen displays permission denied, update the complete backend,
especially SessionAuthenticationFilter.java, and restart Spring Boot.

COMPLETED SECURITY-OFFICER UI
- Availability: Available, Busy and Off Duty.
- GPS: shares the officer's current location when they become available and
  supports a manual location refresh.
- Assigned Alerts: shows assignment/alert numbers, emergency type, user name,
  student/staff number, phone, GPS, distance, description and current status.
- Response workflow: Accept/Acknowledge, Responding and Resolved/Completed.
- Maps: opens the emergency coordinates in Google Maps.
- Incident Reports: displays all reports, reporter details, location, severity
  and status; officers can update status and upload evidence.
- Officer Notifications: displays alert notifications and marks them as read.

GPS NOTE
Live GPS is available in an Android build. A Windows desktop usually has no GPS
provider, so the desktop app will show a clear GPS unavailable message.
