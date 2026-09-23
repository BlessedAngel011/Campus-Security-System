UFH CAMPUS SECURITY - CLEAN MOBILE APPLICATION
===============================================

This is the shared Android application for:
- Students
- Staff members
- Security officers

The role returned by Spring Boot decides which dashboard opens after login.
Students and staff see the user safety dashboard. Security officers see the
security operations dashboard. A saved session keeps the user logged in.

MAIN FEATURES
-------------
STUDENTS AND STAFF
- Register a student/staff account
- Log in once and restore the saved session
- Large SOS button requiring 3 presses within 5 seconds
- Automatically send personal details and live GPS with an SOS
- Report incidents and select a campus location
- View personal reports
- View notifications
- Save and call personal emergency contacts

SECURITY OFFICERS
- Use the same login screen and application
- Set Available, Busy or Off Duty
- Share live GPS location
- View assigned emergency alerts
- See the user's identity, phone number, GPS and distance
- Open an emergency location in Google Maps
- Acknowledge, respond to and complete emergency assignments
- Review and update incidents
- Upload evidence
- View and mark notifications as read

UFH BRANDING
------------
The interface uses UFH colours, the official UFH logo and campus photographs
from the official UFH website. The pictures are loaded from the university
website and therefore need an internet connection.

RUN ON WINDOWS FIRST
--------------------
1. Start the Spring Boot backend.
2. In this mobile_clean folder create and activate a Python virtual environment.
3. Install the requirements:

   python -m pip install -r requirements.txt

4. Run:

   python main.py

ANDROID BACKEND ADDRESS
-----------------------
The Android phone cannot use localhost to reach Spring Boot on the computer.
Run ipconfig in Windows and find the Wi-Fi IPv4 address. Then change
mobile_config.json before building the APK. Example:

{
  "backend_url": "http://192.168.1.105:8080"
}

Use the real IPv4 address of the backend computer. The phone and computer must
be on the same Wi-Fi network. application.properties already contains:

server.address=0.0.0.0

BUILD THE APK
-------------
Buildozer must be run in Linux or WSL Ubuntu, not directly in Windows.

From this folder in WSL:

   buildozer -v android debug

The completed APK will be placed in the bin folder.

IMPORTANT
---------
Spring Boot and MySQL must be running while using the application. For use
outside the local Wi-Fi network, deploy the Spring Boot backend to an internet
server with HTTPS and put that public URL in mobile_config.json.
