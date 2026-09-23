import os
import json
import importlib
import mimetypes
import threading
import webbrowser
from typing import Any

import requests
from dotenv import load_dotenv

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import (
    BooleanProperty,
    StringProperty,
    ListProperty
)
from kivy.storage.jsonstore import JsonStore
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen

try:
    from plyer import gps
except ImportError:
    gps = None


load_dotenv()

# Desktop uses localhost by default. Before building the Android APK, change
# backend_url in mobile_config.json to the Wi-Fi IPv4 address of the computer
# running Spring Boot, for example http://192.168.1.105:8080.
_config_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "mobile_config.json"
)
_configured_backend = "http://localhost:8080"
try:
    with open(_config_path, "r", encoding="utf-8") as config_file:
        _configured_backend = json.load(config_file).get(
            "backend_url", _configured_backend
        )
except (OSError, ValueError, TypeError):
    pass

BACKEND_URL = os.getenv(
    "BACKEND_URL", _configured_backend
).rstrip("/")

REQUEST_TIMEOUT = 15

Window.size = (390, 760)
Window.clearcolor = (0.94, 0.96, 0.98, 1)


class ApiClient:
    def __init__(self, backend_url: str):
        self.backend_url = backend_url
        self.session_token = ""

    def login(
        self,
        student_staff_number: str,
        password: str
    ) -> dict[str, Any]:

        response = requests.post(
            f"{self.backend_url}/api/users/login",
            data={
                "email": student_staff_number,
                "password": password,
                "deviceId": "campus-security-mobile",
                "ipAddress": ""
            },
            timeout=REQUEST_TIMEOUT
        )

        self._raise_for_error(response)

        try:
            result = response.json()
        except ValueError as error:
            raise ValueError(
                "The backend returned an invalid login response."
            ) from error

        session_token = result.get("sessionToken")

        if not session_token:
            raise ValueError(
                "The backend did not return a session token."
            )

        self.session_token = session_token
        return result

    def register(
        self,
        student_staff_number: str,
        first_name: str,
        last_name: str,
        phone_number: str,
        password: str,
        role_name: str,
        campus_id: int
    ) -> dict[str, Any]:


        response = requests.post(
            f"{self.backend_url}/api/users/register",
            data={
                "studentStaffNumber": student_staff_number,
                "firstName": first_name,
                "lastName": last_name,
                "phoneNumber": phone_number,
                "password": password,
                "roleName": role_name,
                "campusId": campus_id
            },
            timeout=REQUEST_TIMEOUT
        )

        self._raise_for_error(response)

        try:
            return response.json()
        except ValueError:
            return {
                "message": "User registered successfully."
            }

    def get_current_user(self) -> dict[str, Any]:
        if not self.session_token:
            raise ValueError("No saved login session was found.")

        response = requests.get(
            f"{self.backend_url}/api/users/me",
            headers=self.authorization_headers(),
            timeout=REQUEST_TIMEOUT
        )

        self._raise_for_error(response)

        try:
            return response.json()
        except ValueError as error:
            raise ValueError(
                "The backend returned invalid user information."
            ) from error

    def logout(self) -> None:
        if not self.session_token:
            return

        response = requests.post(
            f"{self.backend_url}/api/users/logout",
            headers=self.authorization_headers(),
            timeout=REQUEST_TIMEOUT
        )

        self._raise_for_error(response)
        self.session_token = ""


    def authorization_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.session_token}"
        }

    def create_emergency(
        self,
        latitude: float,
        longitude: float,
        emergency_type: str,
        description: str
    ) -> dict[str, Any]:
        response = requests.post(
            f"{self.backend_url}/api/emergency/alert",
            headers=self.authorization_headers(),
            data={
                "latitude": latitude,
                "longitude": longitude,
                "emergencyType": emergency_type,
                "description": description
            },
            timeout=REQUEST_TIMEOUT
        )
        self._raise_for_error(response)
        return response.json()

    def officer_profile(self) -> dict[str, Any]:
        response = requests.get(
            f"{self.backend_url}/api/officers/me",
            headers=self.authorization_headers(),
            timeout=REQUEST_TIMEOUT
        )

        self._raise_for_error(response)

        try:
            return response.json()
        except ValueError as error:
            raise ValueError(
                "The backend returned invalid officer information."
            ) from error

    def get_available_emergencies(
        self
    ) -> list[dict[str, Any]]:

        response = requests.get(
            f"{self.backend_url}/api/emergency/officer/available",
            headers=self.authorization_headers(),
            timeout=REQUEST_TIMEOUT
        )

        self._raise_for_error(response)

        try:
            return response.json()
        except ValueError as error:
            raise ValueError(
                "The backend returned invalid emergency information."
            ) from error


    def set_officer_availability(self, status: str) -> dict[str, Any]:
        response = requests.put(
            f"{self.backend_url}/api/officers/me/availability",
            headers=self.authorization_headers(),
            params={"status": status},
            timeout=REQUEST_TIMEOUT
        )
        self._raise_for_error(response)
        return response.json()

    def update_officer_location(
        self, latitude: float, longitude: float
    ) -> dict[str, Any]:
        response = requests.post(
            f"{self.backend_url}/api/officers/me/location",
            headers=self.authorization_headers(),
            data={"latitude": latitude, "longitude": longitude},
            timeout=REQUEST_TIMEOUT
        )
        self._raise_for_error(response)
        return response.json()

    def officer_assignments(self) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.backend_url}/api/officers/me/assignments",
            headers=self.authorization_headers(),
            timeout=REQUEST_TIMEOUT
        )
        self._raise_for_error(response)
        return response.json()

    def update_assignment_status(
        self, assignment_id: int, status: str
    ) -> dict[str, Any]:
        response = requests.put(
            f"{self.backend_url}/api/officers/me/assignments/"
            f"{assignment_id}/status",
            headers=self.authorization_headers(),
            params={"status": status},
            timeout=REQUEST_TIMEOUT
        )
        self._raise_for_error(response)
        return response.json()

    def get_officer_incidents(self) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.backend_url}/api/incidents/officer/all",

            headers=self.authorization_headers(),
            timeout=REQUEST_TIMEOUT
        )
        self._raise_for_error(response)
        return response.json()

    def update_incident_status(
        self, incident_id: int, status: str
    ) -> dict[str, Any]:
        response = requests.put(
            f"{self.backend_url}/api/incidents/{incident_id}/status",
            headers=self.authorization_headers(),
            params={"status": status},
            timeout=REQUEST_TIMEOUT
        )
        self._raise_for_error(response)
        return response.json()

    def upload_incident_evidence(
        self, incident_id: int, file_path: str
    ) -> dict[str, Any]:
        with open(file_path, "rb") as evidence_file:
            content_type = (
                mimetypes.guess_type(file_path)[0]
                or "application/octet-stream"
            )
            response = requests.post(
                f"{self.backend_url}/api/incidents/{incident_id}/evidence",
                headers=self.authorization_headers(),
                files={"file": (
                    os.path.basename(file_path),
                    evidence_file,
                    content_type
                )},
                timeout=30
            )
        self._raise_for_error(response)
        return response.json()

    def get_officer_notifications(self) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.backend_url}/api/notifications/officer/my-notifications",
            headers=self.authorization_headers(),
            timeout=REQUEST_TIMEOUT
        )
        self._raise_for_error(response)
        return response.json()

    def mark_officer_notification_read(
        self, notification_id: int
    ) -> dict[str, Any]:
        response = requests.put(
            f"{self.backend_url}/api/notifications/officer/"
            f"{notification_id}/read",
            headers=self.authorization_headers(),

            timeout=REQUEST_TIMEOUT
        )
        self._raise_for_error(response)
        return response.json()

    def update_emergency_status(
        self, emergency_id: int, status: str
    ) -> dict[str, Any]:
        response = requests.put(
            f"{self.backend_url}/api/emergency/{emergency_id}/status",
            headers=self.authorization_headers(),
            params={"status": status},
            timeout=REQUEST_TIMEOUT
        )
        self._raise_for_error(response)
        return response.json()

    def get_locations(self) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.backend_url}/api/locations",
            headers=self.authorization_headers(),
            timeout=REQUEST_TIMEOUT
        )
        self._raise_for_error(response)
        return response.json()

    def create_incident(
        self,
        location_id: int,
        incident_type: str,
        description: str,
        severity: str
    ) -> dict[str, Any]:
        response = requests.post(
            f"{self.backend_url}/api/incidents",
            headers=self.authorization_headers(),
            data={
                "locationId": location_id,
                "incidentType": incident_type,
                "description": description,
                "severity": severity
            },
            timeout=REQUEST_TIMEOUT
        )
        self._raise_for_error(response)
        return response.json()

    def get_my_reports(self) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.backend_url}/api/incidents/my-reports",
            headers=self.authorization_headers(),
            timeout=REQUEST_TIMEOUT
        )
        self._raise_for_error(response)
        return response.json()


    def get_notifications(self) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.backend_url}/api/notifications/my-notifications",
            headers=self.authorization_headers(),
            timeout=REQUEST_TIMEOUT
        )
        self._raise_for_error(response)
        return response.json()

    def mark_notification_read(self, notification_id: int) -> dict[str, Any]:
        response = requests.put(
            f"{self.backend_url}/api/notifications/{notification_id}/read",
            headers=self.authorization_headers(),
            timeout=REQUEST_TIMEOUT
        )
        self._raise_for_error(response)
        return response.json()

    @staticmethod
    def _raise_for_error(
        response: requests.Response
    ) -> None:

        if response.ok:
            return

        message = ""

        try:
            response_body = response.json()

            if isinstance(response_body, dict):
                message = (
                    response_body.get("message")
                    or response_body.get("error")
                    or ""
                )

            elif isinstance(response_body, str):
                message = response_body

        except ValueError:
            message = response.text.strip()

        if not message:
            if response.status_code == 401:
                message = (
                    "Invalid login information or expired session."
                )

            elif response.status_code == 403:
                message = (
                    "You do not have permission to perform "
                    "this action."

                )

            elif response.status_code == 409:
                message = (
                    "This student/staff number is already registered."
                )

            else:
                message = (
                    f"The server returned error "
                    f"{response.status_code}."
                )

        raise ValueError(message)


class LoginScreen(Screen):
    loading = BooleanProperty(False)
    status_message = StringProperty("")

    def submit_login(self) -> None:
        if self.loading:
            return

        student_staff_number = (
            self.ids.login_number.text.strip()
        )

        password = self.ids.login_password.text

        self.status_message = ""

        if not student_staff_number:
            self.status_message = (
                "Enter your student/staff number."
            )
            return

        if not password:
            self.status_message = "Enter your password."
            return

        self.loading = True
        self.status_message = "Signing in..."

        threading.Thread(
            target=self._login_request,
            args=(student_staff_number, password),
            daemon=True
        ).start()

    def _login_request(
        self,
        student_staff_number: str,
        password: str

    ) -> None:

        app = App.get_running_app()

        try:
            login_response = app.api.login(
                student_staff_number,
                password
            )

            user = {
                "userId": login_response.get("userId"),
                "role": login_response.get("role"),
                "campusId": login_response.get("campusId"),
                "studentStaffNumber": login_response.get(
                    "studentStaffNumber"
                ),
                "firstName": login_response.get("firstName"),
                "lastName": login_response.get("lastName"),
                "email": login_response.get("email")
            }

            app.save_session(
                app.api.session_token,
                user
            )

            Clock.schedule_once(
                lambda _dt: self._login_success(user),
                0
            )

        except requests.exceptions.ConnectionError:
            Clock.schedule_once(
                lambda _dt: self._login_failed(
                    "Cannot reach the security server. "
                    "Make sure Spring Boot is running."
                ),
                0
            )

        except requests.exceptions.Timeout:
            Clock.schedule_once(
                lambda _dt: self._login_failed(
                    "The server took too long to respond."
                ),
                0
            )

        except requests.exceptions.ChunkedEncodingError:
            Clock.schedule_once(
                lambda _dt: self._login_failed(
                    "The backend ended the response unexpectedly."
                ),
                0

            )

        except (
            requests.exceptions.RequestException,
            ValueError
        ) as error:
            Clock.schedule_once(
                lambda _dt, message=str(error):
                self._login_failed(message),
                0
            )

        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error):
                self._login_failed(
                    f"Login failed: {message}"
                ),
                0
            )

    def _login_success(
        self,
        user: dict[str, Any]
    ) -> None:

        self.loading = False
        self.status_message = ""
        self.ids.login_password.text = ""

        app = App.get_running_app()
        app.open_user_dashboard(user)

    def _login_failed(self, message: str) -> None:
        self.loading = False
        self.status_message = message


class RegisterScreen(Screen):
    loading = BooleanProperty(False)
    status_message = StringProperty("")

    def submit_registration(self) -> None:
        if self.loading:
            return

        student_staff_number = (
            self.ids.register_number.text.strip()
        )

        first_name = (
            self.ids.register_first_name.text.strip()
        )

        last_name = (

            self.ids.register_last_name.text.strip()
        )

        phone_number = (
            self.ids.register_phone.text.strip()
        )

        password = self.ids.register_password.text

        confirm_password = (
            self.ids.register_confirm_password.text
        )

        role_text = self.ids.register_role.text
        campus_text = self.ids.register_campus.text

        self.status_message = ""

        if not all([
            student_staff_number,
            first_name,
            last_name,
            phone_number,
            password,
            confirm_password
        ]):
            self.status_message = (
                "Complete all required fields."
            )
            return

        if role_text not in {"Student", "Staff"}:
            self.status_message = (
                "Select Student or Staff."
            )
            return

        if len(password) < 8:
            self.status_message = (
                "The password must contain at least 8 characters."
            )
            return

        if password != confirm_password:
            self.status_message = (
                "The passwords do not match."
            )
            return

        campus_ids = {
            "Alice Campus": 1,
            "East London Campus": 2,
            "Bhisho Campus": 3
        }

        campus_id = campus_ids.get(campus_text)

        if campus_id is None:
            self.status_message = "Select a valid campus."
            return

        self.loading = True
        self.status_message = "Registering user..."

        threading.Thread(
            target=self._registration_request,
            args=(
                student_staff_number,
                first_name,
                last_name,
                phone_number,
                password,
                role_text.lower(),
                campus_id
            ),
            daemon=True
        ).start()

    def _registration_request(
        self,
        student_staff_number: str,
        first_name: str,
        last_name: str,
        phone_number: str,
        password: str,
        role_name: str,
        campus_id: int
    ) -> None:

        app = App.get_running_app()

        try:
            app.api.register(
                student_staff_number=student_staff_number,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                password=password,
                role_name=role_name,
                campus_id=campus_id
            )

            Clock.schedule_once(
                lambda _dt:
                self._registration_success(
                    student_staff_number
                ),
                0
            )

        except requests.exceptions.ConnectionError:
            Clock.schedule_once(
                lambda _dt:
                self._registration_failed(
                    "Cannot reach the security server. "
                    "Make sure Spring Boot is running."
                ),
                0
            )

        except requests.exceptions.Timeout:
            Clock.schedule_once(
                lambda _dt:
                self._registration_failed(
                    "The server took too long to respond."
                ),
                0
            )

        except (
            requests.exceptions.RequestException,
            ValueError
        ) as error:
            Clock.schedule_once(
                lambda _dt, message=str(error):
                self._registration_failed(message),
                0
            )

        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error):
                self._registration_failed(
                    f"Registration failed: {message}"
                ),
                0
            )

    def _registration_success(
        self,
        student_staff_number: str
    ) -> None:

        self.loading = False
        self.status_message = ""

        self.ids.register_number.text = ""
        self.ids.register_first_name.text = ""
        self.ids.register_last_name.text = ""
        self.ids.register_phone.text = ""
        self.ids.register_password.text = ""
        self.ids.register_confirm_password.text = ""
        self.ids.register_role.text = "Student"
        self.ids.register_campus.text = "Alice Campus"

        app = App.get_running_app()
        login_screen = app.root.get_screen("login")

        login_screen.ids.login_number.text = (
            student_staff_number
        )

        login_screen.status_message = (
            "User registered successfully. You may now sign in."
        )

        app.root.transition.direction = "right"
        app.root.current = "login"

    def _registration_failed(
        self,
        message: str
    ) -> None:

        self.loading = False
        self.status_message = message


class UserDashboardScreen(Screen):
    welcome_text = StringProperty("Welcome")
    account_type = StringProperty("User")
    sos_loading = BooleanProperty(False)
    sos_status = StringProperty("")
    sos_button_text = StringProperty("EMERGENCY\nSOS")
    sos_tap_count = 0
    _sos_tap_reset_event = None
    _sos_latitude = None
    _sos_longitude = None
    _sos_request_started = False

    def emergency_button_pressed(self) -> None:
        """Require three presses within five seconds before activating SOS."""
        if self.sos_loading:
            return

        if self._sos_tap_reset_event is not None:
            self._sos_tap_reset_event.cancel()

        self.sos_tap_count += 1

        if self.sos_tap_count < 3:
            presses_left = 3 - self.sos_tap_count
            press_word = "PRESS" if presses_left == 1 else "PRESSES"
            self.sos_button_text = (
                f"{presses_left} MORE {press_word}\nTO SEND SOS"
            )
            self.sos_status = (
                f"Press the emergency button {presses_left} more "
                f"time{'s' if presses_left != 1 else ''} within 5 seconds."
            )

            self._sos_tap_reset_event = Clock.schedule_once(
                self._reset_sos_taps, 5
            )
            return

        self.sos_tap_count = 0
        self._sos_tap_reset_event = None
        self.sos_button_text = "ACTIVATING SOS..."
        self.send_sos()

    def _reset_sos_taps(self, _dt) -> None:
        self.sos_tap_count = 0
        self._sos_tap_reset_event = None
        self.sos_button_text = "EMERGENCY\nSOS"
        self.sos_status = "SOS was not activated. Press 3 times to send an alert."

    def send_sos(self) -> None:
        """Capture GPS and send the emergency without opening a form."""
        if self.sos_loading:
            return

        if gps is None:
            self.sos_status = "GPS support is unavailable. Install plyer first."
            return

        self.sos_loading = True
        self._sos_request_started = False
        self.sos_status = "Getting your location and sending SOS..."
        self.sos_button_text = "GETTING LOCATION..."

        # Dynamically request Android permissions. Using importlib prevents
        # VS Code on Windows from reporting android.permissions as missing.
        if os.name != "nt":
            try:
                android_permissions = importlib.import_module(
                    "android.permissions"
                )
                android_permissions.request_permissions([
                    android_permissions.Permission.ACCESS_FINE_LOCATION,
                    android_permissions.Permission.ACCESS_COARSE_LOCATION
                ])
            except (ImportError, AttributeError):
                pass

        try:
            gps.configure(
                on_location=self._on_sos_location,
                on_status=self._on_sos_gps_status
            )
            gps.start(minTime=500, minDistance=0)
        except Exception:
            self.sos_loading = False
            self.sos_button_text = "EMERGENCY\nSOS"
            self.sos_status = (
                "GPS is unavailable on this computer. "

                "Live SOS location works on the Android phone build."
            )

    def _on_sos_location(self, **location) -> None:
        if self._sos_request_started:
            return
        self._sos_request_started = True

        try:
            self._sos_latitude = float(location["lat"])
            self._sos_longitude = float(location["lon"])
            gps.stop()
        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error): self._sos_failed(message), 0
            )
            return

        threading.Thread(
            target=self._send_sos_request,
            daemon=True
        ).start()

    def _on_sos_gps_status(self, status_type, status_message) -> None:
        Clock.schedule_once(
            lambda _dt: setattr(self, "sos_status", str(status_message)), 0
        )

    def _send_sos_request(self) -> None:
        try:
            result = App.get_running_app().api.create_emergency(
                self._sos_latitude,
                self._sos_longitude,
                "GENERAL_EMERGENCY",
                "One-tap emergency SOS from the mobile application."
            )
            emergency_id = result.get("emergencyId", "")
            Clock.schedule_once(
                lambda _dt: self._sos_sent(emergency_id), 0
            )
        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error): self._sos_failed(message), 0
            )

    def _sos_sent(self, emergency_id) -> None:
        self.sos_loading = False
        self._sos_request_started = False
        self.sos_button_text = "EMERGENCY\nSOS"
        self.sos_status = f"SOS sent successfully. Alert #{emergency_id}"
        App.get_running_app().show_message(
            "Emergency Alert Sent",
            "Your location and account details were sent to Campus Security."
        )

    def _sos_failed(self, message: str) -> None:
        try:
            gps.stop()
        except Exception:
            pass
        self.sos_loading = False
        self._sos_request_started = False
        self.sos_button_text = "EMERGENCY\nSOS"
        self.sos_status = message

    def open_feature(
        self,
        feature_name: str
    ) -> None:

        screen_names = {
            "Report an Incident": "report_incident",
            "My Reports": "my_reports",
            "Emergency Contacts": "emergency_contacts",
            "Notifications": "user_notifications"
        }
        screen_name = screen_names.get(feature_name)
        if not screen_name:
            return
        app = App.get_running_app()
        app.root.transition.direction = "left"
        app.root.current = screen_name


class ReportIncidentScreen(Screen):
    loading = BooleanProperty(False)
    status_message = StringProperty("")
    location_values = ListProperty([])
    location_ids = {}

    def on_pre_enter(self, *args) -> None:
        if not self.location_values:
            threading.Thread(target=self._load_locations, daemon=True).start()

    def _load_locations(self) -> None:
        try:
            locations = App.get_running_app().api.get_locations()
            mapping = {
                item.get("locationName", f"Location {item.get('locationId')}"):
                item.get("locationId") for item in locations
            }
            Clock.schedule_once(lambda _dt: self._locations_loaded(mapping), 0)
        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error): setattr(
                    self, "status_message", message
                ), 0
            )

    def _locations_loaded(self, mapping: dict) -> None:

        self.location_ids = mapping
        self.location_values = list(mapping.keys())
        if self.location_values:
            self.ids.report_location.text = self.location_values[0]

    def submit_report(self) -> None:
        if self.loading:
            return
        location_id = self.location_ids.get(self.ids.report_location.text)
        incident_type = self.ids.report_type.text
        description = self.ids.report_description.text.strip()
        severity = self.ids.report_severity.text
        if location_id is None:
            self.status_message = "Select a valid campus location."
            return
        if not description:
            self.status_message = "Enter a description of the incident."
            return
        self.loading = True
        self.status_message = "Submitting incident report..."
        threading.Thread(
            target=self._submit_request,
            args=(location_id, incident_type, description, severity),
            daemon=True
        ).start()

    def _submit_request(self, location_id, incident_type, description, severity):
        try:
            result = App.get_running_app().api.create_incident(
                location_id, incident_type, description, severity
            )
            Clock.schedule_once(
                lambda _dt: self._submitted(result.get("incidentId")), 0
            )
        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error): self._failed(message), 0
            )

    def _submitted(self, incident_id) -> None:
        self.loading = False
        self.ids.report_description.text = ""
        self.status_message = f"Report #{incident_id} submitted successfully."

    def _failed(self, message: str) -> None:
        self.loading = False
        self.status_message = message


class MyReportsScreen(Screen):
    reports_text = StringProperty("Loading reports...")
    status_message = StringProperty("")

    def on_pre_enter(self, *args) -> None:
        self.refresh_reports()


    def refresh_reports(self) -> None:
        self.status_message = "Loading reports..."
        threading.Thread(target=self._load_reports, daemon=True).start()

    def _load_reports(self) -> None:
        try:
            reports = App.get_running_app().api.get_my_reports()
            lines = []
            for report in reversed(reports):
                location = report.get("location") or {}
                lines.append(
                    f"REPORT #{report.get('incidentId')}\n"
                    f"Type: {report.get('incidentType')}\n"
                    f"Location: {location.get('locationName', 'Unknown')}\n"
                    f"Status: {str(report.get('incidentStatus', '')).replace('_', ' ').title()}\n"
                    f"Reported: {str(report.get('reportedAt', '')).replace('T', ' ')[:16]}\n"
                    f"Description: {report.get('description')}"
                )
            text = "\n\n--------------------\n\n".join(lines)
            Clock.schedule_once(
                lambda _dt: self._loaded(text or "You have not submitted any reports."), 0
            )
        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error): self._failed(message), 0
            )

    def _loaded(self, text: str) -> None:
        self.reports_text = text
        self.status_message = ""

    def _failed(self, message: str) -> None:
        self.reports_text = "Could not load reports."
        self.status_message = message


class EmergencyContactsScreen(Screen):
    personal_contacts_text = StringProperty("No personal emergency contacts saved.")
    personal_contact_values = ListProperty([])
    personal_contact_numbers = {}
    status_message = StringProperty("")

    def on_pre_enter(self, *args) -> None:
        self.refresh_personal_contacts()

    def call_number(self, number: str) -> None:
        webbrowser.open(f"tel:{number}")

    def save_personal_contact(self) -> None:
        name = self.ids.contact_name.text.strip()
        phone = self.ids.contact_phone.text.strip()

        if not name or not phone:
            self.status_message = "Enter both the contact name and phone number."

            return

        cleaned_phone = "".join(
            character for character in phone
            if character.isdigit() or character == "+"
        )

        if len(cleaned_phone.replace("+", "")) < 7:
            self.status_message = "Enter a valid phone number."
            return

        app = App.get_running_app()
        contacts = []
        if app.contact_store.exists("contacts"):
            contacts = app.contact_store.get("contacts").get("items", [])

        contacts.append({"name": name, "phone": cleaned_phone})
        app.contact_store.put("contacts", items=contacts)

        self.ids.contact_name.text = ""
        self.ids.contact_phone.text = ""
        self.status_message = "Emergency contact saved successfully."
        self.refresh_personal_contacts()

    def refresh_personal_contacts(self) -> None:
        app = App.get_running_app()
        contacts = []
        if app.contact_store.exists("contacts"):
            contacts = app.contact_store.get("contacts").get("items", [])

        if not contacts:
            self.personal_contacts_text = "No personal emergency contacts saved."
            self.personal_contact_values = []
            self.personal_contact_numbers = {}
            if self.ids:
                self.ids.personal_call_number.text = "Select a saved contact"
            return

        self.personal_contact_numbers = {
            f"{contact['name']} | {contact['phone']}": contact["phone"]
            for contact in contacts
        }
        self.personal_contact_values = list(self.personal_contact_numbers.keys())
        self.personal_contacts_text = "\n".join(
            f"{index + 1}. {contact['name']}  |  {contact['phone']}"
            for index, contact in enumerate(contacts)
        )
        self.ids.personal_call_number.text = self.personal_contact_values[0]

    def call_personal_contact(self) -> None:
        selection = self.ids.personal_call_number.text.strip()
        phone = self.personal_contact_numbers.get(selection, "")
        if not phone:
            self.status_message = "Select a saved contact to call."
            return

        self.call_number(phone)

    def clear_personal_contacts(self) -> None:
        app = App.get_running_app()
        if app.contact_store.exists("contacts"):
            app.contact_store.delete("contacts")
        self.status_message = "Personal emergency contacts cleared."
        self.refresh_personal_contacts()


class UserNotificationsScreen(Screen):
    notifications_text = StringProperty("Loading notifications...")
    status_message = StringProperty("")

    def on_pre_enter(self, *args) -> None:
        self.refresh_notifications()

    def refresh_notifications(self) -> None:
        self.status_message = "Loading notifications..."
        threading.Thread(target=self._load_notifications, daemon=True).start()

    def _load_notifications(self) -> None:
        try:
            notifications = App.get_running_app().api.get_notifications()
            lines = []
            for item in notifications:
                read_text = "Read" if item.get("read") else "Unread"
                lines.append(
                    f"NOTIFICATION #{item.get('notificationId')} - {read_text}\n"
                    f"{item.get('message')}\n"
                    f"{str(item.get('createdAt', '')).replace('T', ' ')[:16]}"
                )
            text = "\n\n--------------------\n\n".join(lines)
            Clock.schedule_once(
                lambda _dt: self._loaded(text or "You have no notifications."), 0
            )
        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error): self._failed(message), 0
            )

    def mark_read(self) -> None:
        value = self.ids.notification_id.text.strip()
        if not value.isdigit():
            self.status_message = "Enter a valid notification number."
            return
        threading.Thread(
            target=self._mark_read_request,
            args=(int(value),), daemon=True
        ).start()

    def _mark_read_request(self, notification_id: int) -> None:
        try:
            App.get_running_app().api.mark_notification_read(notification_id)
            Clock.schedule_once(lambda _dt: self.refresh_notifications(), 0)

        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error): self._failed(message), 0
            )

    def _loaded(self, text: str) -> None:
        self.notifications_text = text
        self.status_message = ""

    def _failed(self, message: str) -> None:
        self.status_message = message


class OfficerDashboardScreen(Screen):
    welcome_text = StringProperty(
        "Welcome, Security Officer"
    )
    status_message = StringProperty("")
    duty_status = StringProperty("Off Duty")

    def set_availability(self, status: str) -> None:
        self.status_message = "Updating availability..."
        threading.Thread(
            target=self._availability_request,
            args=(status,), daemon=True
        ).start()

    def _availability_request(self, status: str) -> None:
        try:
            App.get_running_app().api.set_officer_availability(status)
            Clock.schedule_once(
                lambda _dt: self._availability_updated(status), 0
            )
        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error): setattr(
                    self, "status_message", message
                ), 0
            )

    def _availability_updated(self, status: str) -> None:
        self.duty_status = status.replace("_", " ").title()
        self.status_message = f"Officer status: {self.duty_status}"
        if status == "AVAILABLE":
            self.capture_officer_location()

    def capture_officer_location(self) -> None:
        if gps is None:
            self.status_message = "GPS support is unavailable on this device."
            return
        self.status_message = "Capturing officer GPS location..."
        try:
            gps.configure(
                on_location=self._on_officer_location,
                on_status=self._on_officer_gps_status

            )
            gps.start(minTime=1000, minDistance=0)
        except Exception:
            self.status_message = (
                "GPS is unavailable on this computer. "
                "It will work in the Android build."
            )

    def _on_officer_location(self, **location) -> None:
        try:
            latitude = float(location["lat"])
            longitude = float(location["lon"])
            gps.stop()
            threading.Thread(
                target=self._send_officer_location,
                args=(latitude, longitude), daemon=True
            ).start()
        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error): setattr(
                    self, "status_message", message
                ), 0
            )

    def _on_officer_gps_status(self, status_type, status_message) -> None:
        Clock.schedule_once(
            lambda _dt: setattr(self, "status_message", str(status_message)), 0
        )

    def _send_officer_location(self, latitude: float, longitude: float) -> None:
        try:
            App.get_running_app().api.update_officer_location(
                latitude, longitude
            )
            Clock.schedule_once(
                lambda _dt: setattr(
                    self, "status_message",
                    "Available: current GPS location shared."
                ), 0
            )
        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error): setattr(
                    self, "status_message", message
                ), 0
            )

    def open_alerts(self) -> None:
        app = App.get_running_app()
        app.root.transition.direction = "left"
        app.root.current = "officer_alerts"
        app.root.get_screen("officer_alerts").refresh_alerts()

    def open_feature(
        self,

        feature_name: str
    ) -> None:

        screens = {
            "Assigned Alerts": "officer_alerts",
            "Incident Reports": "officer_incidents",
            "Notifications": "officer_notifications"
        }
        screen_name = screens.get(feature_name)
        if not screen_name:
            return
        app = App.get_running_app()
        app.root.transition.direction = "left"
        app.root.current = screen_name


class EmergencyScreen(Screen):
    latitude = None
    longitude = None
    location_text = StringProperty("Location not captured")
    status_message = StringProperty("")
    loading = BooleanProperty(False)

    def reset_form(self) -> None:
        self.status_message = ""
        self.loading = False
        self.latitude = None
        self.longitude = None
        self.location_text = "Location not captured"
        if self.ids:
            self.ids.emergency_type.text = "General Emergency"
            self.ids.emergency_description.text = ""

    def capture_location(self) -> None:
        if gps is None:
            self.status_message = "Install plyer to use GPS: pip install plyer"
            return
        self.status_message = "Getting your GPS location..."
        try:
            gps.configure(on_location=self._on_location,
                          on_status=self._on_gps_status)
            gps.start(minTime=1000, minDistance=0)
        except Exception:
            self.status_message = (
                "GPS is not available on this computer. "
                "Run the mobile build on an Android phone."
            )

    def _on_location(self, **kwargs) -> None:
        self.latitude = float(kwargs["lat"])
        self.longitude = float(kwargs["lon"])
        try:
            gps.stop()
        except Exception:
            pass

        Clock.schedule_once(lambda _dt: self._show_location(), 0)

    def _show_location(self) -> None:
        self.location_text = (
            f"GPS: {self.latitude:.6f}, {self.longitude:.6f}"
        )
        self.status_message = "Location captured. You can send the alert."

    def _on_gps_status(self, status_type, status_message) -> None:
        Clock.schedule_once(
            lambda _dt: setattr(self, "status_message", str(status_message)), 0
        )

    def send_alert(self) -> None:
        if self.loading:
            return
        if self.latitude is None or self.longitude is None:
            self.status_message = "Capture your GPS location first."
            return
        emergency_type = self.ids.emergency_type.text.upper().replace(" ", "_")
        description = self.ids.emergency_description.text.strip()
        self.loading = True
        self.status_message = "Sending emergency alert..."
        threading.Thread(
            target=self._send_request,
            args=(emergency_type, description), daemon=True
        ).start()

    def _send_request(self, emergency_type: str, description: str) -> None:
        try:
            result = App.get_running_app().api.create_emergency(
                self.latitude, self.longitude, emergency_type, description
            )
            emergency_id = result.get("emergencyId", "")
            Clock.schedule_once(
                lambda _dt: self._sent_success(emergency_id), 0
            )
        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error): self._sent_failed(message), 0
            )

    def _sent_success(self, emergency_id) -> None:
        self.loading = False
        self.status_message = f"SOS sent successfully. Alert #{emergency_id}"
        App.get_running_app().show_message(
            "Emergency Alert Sent",
            "Campus security has received your location and emergency alert."
        )

    def _sent_failed(self, message: str) -> None:
        self.loading = False
        self.status_message = message


class OfficerAlertsScreen(Screen):
    alerts_text = StringProperty(
        "Open this page to load available emergency cases."
    )

    status_message = StringProperty("")
    loading = BooleanProperty(False)
    case_values = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.alerts_by_label: dict[str, dict[str, Any]] = {}

    def on_pre_enter(self, *args) -> None:
        self.refresh_alerts()

    def refresh_alerts(self) -> None:
        if self.loading:
            return

        self.loading = True
        self.status_message = "Loading available emergency work..."

        threading.Thread(
            target=self._load_alerts,
            daemon=True
        ).start()

    def _load_alerts(self) -> None:
        try:
            app = App.get_running_app()
            alerts = app.api.get_available_emergencies()

            mapping: dict[str, dict[str, Any]] = {}
            display_blocks: list[str] = []

            for alert in alerts:
                user = alert.get("user") or {}

                emergency_type = str(
                    alert.get("emergencyType")
                    or "Emergency"
                ).replace("_", " ").title()

                first_name = user.get("firstName") or ""
                last_name = user.get("lastName") or ""

                person_name = (
                    f"{first_name} {last_name}"
                ).strip()

                if not person_name:
                    person_name = "Unknown user"

                label = (

                    f"{emergency_type} — {person_name}"
                )

                # Keep dropdown labels unique without asking the
                # officer to type or remember an ID.
                if label in mapping:
                    label = (
                        f"{label} "
                        f"({alert.get('emergencyId')})"
                    )

                mapping[label] = alert

                latitude = alert.get("latitude")
                longitude = alert.get("longitude")

                if (
                    latitude is not None
                    and longitude is not None
                ):
                    gps_text = f"{latitude}, {longitude}"
                else:
                    gps_text = "Location not supplied"

                display_blocks.append(
                    f"{emergency_type}\n"
                    f"User: {person_name}\n"
                    f"Student/staff number: "
                    f"{user.get('studentStaffNumber') or 'Not supplied'}\n"
                    f"Phone: "
                    f"{user.get('phoneNumber') or 'Not supplied'}\n"
                    f"Location: {gps_text}\n"
                    f"Status: "
                    f"{alert.get('alertStatus') or 'SENT'}\n"
                    f"Description: "
                    f"{alert.get('description') or 'None'}"
                )

            if display_blocks:
                display_text = (
                    "\n\n------------------------------\n\n"
                ).join(display_blocks)
            else:
                display_text = (
                    "There are currently no active "
                    "emergency cases."
                )

            Clock.schedule_once(
                lambda _dt: self._alerts_loaded(
                    display_text,
                    mapping
                ),
                0
            )


        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error):
                self._request_failed(message),
                0
            )

    def _alerts_loaded(
        self,
        display_text: str,
        mapping: dict[str, dict[str, Any]]
    ) -> None:
        self.loading = False
        self.status_message = ""
        self.alerts_text = display_text
        self.alerts_by_label = mapping
        self.case_values = list(mapping.keys())

        if self.case_values:
            self.ids.available_alert.text = (
                self.case_values[0]
            )
        else:
            self.ids.available_alert.text = (
                "No active emergency cases"
            )

    def get_selected_alert(
        self
    ) -> dict[str, Any] | None:

        selected_label = (
            self.ids.available_alert.text
        )

        selected_alert = (
            self.alerts_by_label.get(selected_label)
        )

        if not selected_alert:
            self.status_message = (
                "Select an available emergency case."
            )
            return None

        return selected_alert

    def update_status(self) -> None:
        alert = self.get_selected_alert()

        if not alert:
            return

        emergency_id = alert.get("emergencyId")


        if emergency_id is None:
            self.status_message = (
                "The selected case has no emergency ID."
            )
            return

        status = self.ids.alert_status.text

        self.status_message = (
            "Updating emergency case..."
        )

        threading.Thread(
            target=self._update_status_request,
            args=(int(emergency_id), status),
            daemon=True
        ).start()

    def _update_status_request(
        self,
        emergency_id: int,
        status: str
    ) -> None:
        try:
            app = App.get_running_app()

            app.api.update_emergency_status(
                emergency_id,
                status
            )

            Clock.schedule_once(
                lambda _dt:
                self._status_updated(status),
                0
            )

        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error):
                self._request_failed(message),
                0
            )

    def _status_updated(self, status: str) -> None:
        readable_status = (
            status.replace("_", " ").title()
        )

        self.status_message = (
            f"Case updated to {readable_status}."
        )

        self.refresh_alerts()


    def open_map(self) -> None:
        alert = self.get_selected_alert()

        if not alert:
            return

        latitude = alert.get("latitude")
        longitude = alert.get("longitude")

        if latitude is None or longitude is None:
            self.status_message = (
                "This emergency case has no GPS location."
            )
            return

        maps_url = (
            "https://www.google.com/maps/search/"
            "?api=1&query="
            f"{latitude},{longitude}"
        )

        webbrowser.open(maps_url)

        self.status_message = (
            "Opening the user location in Maps..."
        )

    def _request_failed(self, message: str) -> None:
        self.loading = False
        self.status_message = message
  


class OfficerIncidentsScreen(Screen):
    incidents_text = StringProperty(
        "Open this page to load available incident cases."
    )

    status_message = StringProperty("")
    selected_evidence_path = StringProperty("")
    incident_values = ListProperty([])
    loading = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.incidents_by_label: dict[
            str,
            dict[str, Any]
        ] = {}

    def on_pre_enter(self, *args) -> None:
        self.refresh_incidents()

    def refresh_incidents(self) -> None:

        if self.loading:
            return

        self.loading = True
        self.status_message = (
            "Loading available incident cases..."
        )

        threading.Thread(
            target=self._load_incidents,
            daemon=True
        ).start()

    def _load_incidents(self) -> None:
        try:
            app = App.get_running_app()
            incidents = (
                app.api.get_officer_incidents()
            )

            # Closed cases are no longer active work.
            available_incidents = [
                incident
                for incident in incidents
                if incident.get("incidentStatus")
                != "CLOSED"
            ]

            mapping: dict[
                str,
                dict[str, Any]
            ] = {}

            display_blocks: list[str] = []

            for incident in available_incidents:
                user = incident.get("user") or {}
                location = (
                    incident.get("location") or {}
                )

                incident_type = (
                    incident.get("incidentType")
                    or "Incident"
                )

                location_name = (
                    location.get("locationName")
                    or "Unknown location"
                )

                label = (
                    f"{incident_type} — "
                    f"{location_name}"
                )


                # Keep duplicate labels unique internally.
                if label in mapping:
                    label = (
                        f"{label} "
                        f"({incident.get('incidentId')})"
                    )

                mapping[label] = incident

                first_name = (
                    user.get("firstName") or ""
                )

                last_name = (
                    user.get("lastName") or ""
                )

                reporter_name = (
                    f"{first_name} {last_name}"
                ).strip()

                if not reporter_name:
                    reporter_name = "Unknown user"

                status = str(
                    incident.get("incidentStatus")
                    or "REPORTED"
                ).replace("_", " ").title()

                severity = (
                    incident.get("severity")
                    or "MEDIUM"
                )

                display_blocks.append(
                    f"{incident_type}\n"
                    f"Severity: {severity}\n"
                    f"Status: {status}\n"
                    f"Location: {location_name}\n"
                    f"Reported by: {reporter_name}\n"
                    f"Student/staff number: "
                    f"{user.get('studentStaffNumber') or 'Not supplied'}\n"
                    f"Description: "
                    f"{incident.get('description') or 'No description'}"
                )

            if display_blocks:
                display_text = (
                    "\n\n------------------------------\n\n"
                ).join(display_blocks)
            else:
                display_text = (
                    "There are currently no "
                    "available incident cases."

                )

            Clock.schedule_once(
                lambda _dt:
                self._incidents_loaded(
                    display_text,
                    mapping
                ),
                0
            )

        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error):
                self._request_failed(message),
                0
            )

    def _incidents_loaded(
        self,
        display_text: str,
        mapping: dict[str, dict[str, Any]]
    ) -> None:
        self.loading = False
        self.status_message = ""
        self.incidents_text = display_text
        self.incidents_by_label = mapping
        self.incident_values = list(mapping.keys())

        if self.incident_values:
            self.ids.available_incident.text = (
                self.incident_values[0]
            )
        else:
            self.ids.available_incident.text = (
                "No available incident cases"
            )

    def get_selected_incident(
        self
    ) -> dict[str, Any] | None:

        selected_label = (
            self.ids.available_incident.text
        )

        incident = (
            self.incidents_by_label.get(
                selected_label
            )
        )

        if not incident:
            self.status_message = (
                "Select an available incident case."

            )
            return None

        return incident

    def update_incident(self) -> None:
        incident = self.get_selected_incident()

        if not incident:
            return

        incident_id = incident.get("incidentId")

        if incident_id is None:
            self.status_message = (
                "The selected case has no incident ID."
            )
            return

        status = (
            self.ids.officer_incident_status.text
        )

        self.status_message = (
            "Updating incident case..."
        )

        threading.Thread(
            target=self._update_incident_request,
            args=(int(incident_id), status),
            daemon=True
        ).start()

    def _update_incident_request(
        self,
        incident_id: int,
        status: str
    ) -> None:
        try:
            app = App.get_running_app()

            app.api.update_incident_status(
                incident_id,
                status
            )

            Clock.schedule_once(
                lambda _dt:
                self._incident_updated(status),
                0
            )

        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error):

                self._request_failed(message),
                0
            )

    def _incident_updated(
        self,
        status: str
    ) -> None:
        readable_status = (
            status.replace("_", " ").title()
        )

        self.status_message = (
            f"Case updated to {readable_status}."
        )

        self.refresh_incidents()

    def choose_evidence(self) -> None:
        incident = self.get_selected_incident()

        if not incident:
            return

        incident_status = (
            incident.get("incidentStatus")
        )

        if incident_status not in (
            "RESOLVED",
            "CLOSED"
        ):
            self.status_message = (
                "Mark this case as RESOLVED "
                "before adding proof."
            )
            return

        try:
            plyer_module = (
                importlib.import_module("plyer")
            )

            plyer_module.filechooser.open_file(
                on_selection=(
                    self._evidence_selected
                )
            )

        except Exception:
            self.status_message = (
                "File selection is unavailable "
                "on this device."
            )

    def _evidence_selected(
        self,
        selection
    ) -> None:
        if not selection:
            return

        self.selected_evidence_path = (
            selection[0]
        )

        # Upload immediately after selection.
        self.upload_evidence()

    def upload_evidence(self) -> None:
        incident = self.get_selected_incident()

        if not incident:
            return

        incident_id = incident.get("incidentId")

        if (
            incident_id is None
            or not self.selected_evidence_path
        ):
            self.status_message = (
                "Select a solved case and "
                "its proof file."
            )
            return

        self.status_message = (
            "Uploading proof of solved case..."
        )

        threading.Thread(
            target=self._upload_evidence_request,
            args=(
                int(incident_id),
                self.selected_evidence_path
            ),
            daemon=True
        ).start()

    def _upload_evidence_request(
        self,
        incident_id: int,
        path: str
    ) -> None:
        try:
            app = App.get_running_app()

            app.api.upload_incident_evidence(
                incident_id,

                path
            )

            Clock.schedule_once(
                lambda _dt:
                self._evidence_uploaded(),
                0
            )

        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error):
                self._request_failed(message),
                0
            )

    def _evidence_uploaded(self) -> None:
        self.selected_evidence_path = ""

        self.status_message = (
            "Proof of solved case "
            "uploaded successfully."
        )

    def _request_failed(
        self,
        message: str
    ) -> None:
        self.loading = False
        self.status_message = message

class OfficerNotificationsScreen(Screen):
    notifications_text = StringProperty("Loading notifications...")
    status_message = StringProperty("")

    def on_pre_enter(self, *args) -> None:
        self.refresh_notifications()

    def refresh_notifications(self) -> None:
        threading.Thread(target=self._load_notifications, daemon=True).start()

    def _load_notifications(self) -> None:
        try:
            items = App.get_running_app().api.get_officer_notifications()
            lines = []
            for item in items:
                read_text = "Read" if item.get("read") else "Unread"
                lines.append(
                    f"NOTIFICATION #{item.get('notificationId')} - {read_text}\n"
                    f"{item.get('message')}\n"
                    f"{str(item.get('createdAt', '')).replace('T', ' ')[:16]}"
                )
            text = "\n\n--------------------\n\n".join(lines)
            Clock.schedule_once(
                lambda _dt: self._loaded(text or "No notifications found."), 0

            )
        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error): self._failed(message), 0
            )

    def mark_read(self) -> None:
        value = self.ids.officer_notification_id.text.strip()
        if not value.isdigit():
            self.status_message = "Enter a valid notification number."
            return
        threading.Thread(
            target=self._mark_read_request,
            args=(int(value),), daemon=True
        ).start()

    def _mark_read_request(self, notification_id: int) -> None:
        try:
            App.get_running_app().api.mark_officer_notification_read(
                notification_id
            )
            Clock.schedule_once(lambda _dt: self.refresh_notifications(), 0)
        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error): self._failed(message), 0
            )

    def _loaded(self, text: str) -> None:
        self.notifications_text = text
        self.status_message = ""

    def _failed(self, message: str) -> None:
        self.status_message = message


class CampusSecurityApp(App):
    current_user: dict[str, Any] = {}

    def build(self):
        self.title = "UFH Campus Security"
        self.api = ApiClient(BACKEND_URL)

        session_file = os.path.join(
            self.user_data_dir,
            "user_session.json"
        )

        self.session_store = JsonStore(session_file)

        contacts_file = os.path.join(
            self.user_data_dir,
            "personal_emergency_contacts.json"
        )
        self.contact_store = JsonStore(contacts_file)

        return Builder.load_file(
            "campus_security.kv"
        )

    def on_start(self) -> None:
        self.restore_saved_session()

    def save_session(
        self,
        session_token: str,
        user: dict[str, Any]
    ) -> None:

        self.session_store.put(
            "login",
            session_token=session_token,
            user=user
        )

    def restore_saved_session(self) -> None:
        if not self.session_store.exists("login"):
            return

        saved_session = self.session_store.get("login")

        session_token = saved_session.get(
            "session_token",
            ""
        )

        saved_user = saved_session.get(
            "user",
            {}
        )

        if not session_token:
            self.clear_saved_session()
            return

        self.api.session_token = session_token

        login_screen = self.root.get_screen("login")
        login_screen.loading = True
        login_screen.status_message = (
            "Restoring your session..."
        )

        threading.Thread(
            target=self._validate_saved_session,
            args=(saved_user,),
            daemon=True
        ).start()

    def _validate_saved_session(
        self,

        saved_user: dict[str, Any]
    ) -> None:

        try:
            current_user = self.api.get_current_user()

            Clock.schedule_once(
                lambda _dt:
                self._saved_session_success(
                    current_user or saved_user
                ),
                0
            )

        except requests.exceptions.ConnectionError:
            # The backend may temporarily be offline. Keep the
            # saved session but return to login for now.
            Clock.schedule_once(
                lambda _dt:
                self._saved_session_connection_failed(),
                0
            )

        except Exception:
            self.clear_saved_session()

            Clock.schedule_once(
                lambda _dt:
                self._saved_session_invalid(),
                0
            )

    def _saved_session_success(
        self,
        user: dict[str, Any]
    ) -> None:

        login_screen = self.root.get_screen("login")
        login_screen.loading = False
        login_screen.status_message = ""

        self.save_session(
            self.api.session_token,
            user
        )

        self.open_user_dashboard(user)

    def _saved_session_connection_failed(self) -> None:
        login_screen = self.root.get_screen("login")

        login_screen.loading = False
        login_screen.status_message = (
            "Cannot reach the security server."
        )


    def _saved_session_invalid(self) -> None:
        login_screen = self.root.get_screen("login")

        login_screen.loading = False
        login_screen.status_message = (
            "Your saved session expired. Please sign in again."
        )

    def clear_saved_session(self) -> None:
        if self.session_store.exists("login"):
            self.session_store.delete("login")

    def open_user_dashboard(
        self,
        user: dict[str, Any]
    ) -> None:

        self.current_user = user

        first_name = (
            user.get("firstName")
            or "User"
        )

        role_name = self.extract_role_name(user)

        if role_name in {
            "security officer",
            "security_officer",
            "security"
        }:
            officer_dashboard = self.root.get_screen(
                "officer_dashboard"
            )

            officer_dashboard.welcome_text = (
                f"Welcome, Officer {first_name}"
            )

            self.root.transition.direction = "left"
            self.root.current = "officer_dashboard"
            return

        if role_name in {"student", "staff"}:
            user_dashboard = self.root.get_screen(
                "user_dashboard"
            )

            user_dashboard.welcome_text = (
                f"Welcome, {first_name}"
            )

            user_dashboard.account_type = (
                role_name.title()

            )

            self.root.transition.direction = "left"
            self.root.current = "user_dashboard"
            return

        self.api.session_token = ""
        self.current_user = {}
        self.clear_saved_session()

        login_screen = self.root.get_screen("login")
        login_screen.loading = False
        login_screen.status_message = (
            "This account cannot use the mobile application."
        )

        self.root.current = "login"

    @staticmethod
    def extract_role_name(
        user: dict[str, Any]
    ) -> str:

        role = user.get("role")

        if isinstance(role, str):
            return role.strip().lower()

        if isinstance(role, dict):
            role_name = (
                role.get("roleName")
                or role.get("name")
                or role.get("authority")
                or ""
            )

            return str(role_name).strip().lower()

        role_name = (
            user.get("roleName")
            or user.get("userRole")
            or ""
        )

        return str(role_name).strip().lower()

    def logout(self) -> None:
        threading.Thread(
            target=self._logout_request,
            daemon=True
        ).start()

    def _logout_request(self) -> None:
        try:
            self.api.logout()

        except Exception:
            self.api.session_token = ""

        self.clear_saved_session()

        Clock.schedule_once(
            self._finish_logout,
            0
        )

    def _finish_logout(self, _dt) -> None:
        self.current_user = {}
        self.api.session_token = ""

        login_screen = self.root.get_screen("login")

        login_screen.ids.login_password.text = ""
        login_screen.status_message = ""

        self.root.transition.direction = "right"
        self.root.current = "login"

    def show_message(
        self,
        title: str,
        message: str
    ) -> None:

        message_label = Label(
            text=message,
            halign="center",
            valign="middle",
            color=(0.08, 0.16, 0.25, 1)
        )

        message_label.bind(
            size=lambda widget, size:
            setattr(widget, "text_size", size)
        )

        popup = Popup(
            title=title,
            content=message_label,
            size_hint=(0.84, None),
            height=220,
            auto_dismiss=True
        )

        popup.open()


if __name__ == "__main__":
    CampusSecurityApp().run()

