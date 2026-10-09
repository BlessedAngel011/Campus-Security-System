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
from kivy.utils import platform
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
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen

if platform == "android":
    try:
        from android.permissions import Permission, check_permission, request_permissions
    except Exception:
        Permission = None
        check_permission = None
        request_permissions = None
else:
    Permission = None
    check_permission = None
    request_permissions = None

try:
    if platform == "android":
        from jnius import PythonJavaClass, java_method, autoclass

        AndroidLooper = autoclass("android.os.Looper")
        AndroidLocationManager = autoclass("android.location.LocationManager")
        AndroidContext = autoclass("android.content.Context")
        AndroidPythonActivity = autoclass(
            "org.kivy.android.PythonActivity"
        )

        class NativeAndroidLocationListener(PythonJavaClass):
            __javainterfaces__ = [
                "android/location/LocationListener"
            ]

            def __init__(self, callback):
                super().__init__()
                self.callback = callback

            @java_method("(Landroid/location/Location;)V")
            def onLocationChanged(self, location):
                self.callback(location)

            @java_method(
                "(Ljava/util/List;)V",
                name="onLocationChanged"
            )
            def onLocationChangedList(self, locations):
                if locations is None:
                    return

                try:
                    size = locations.size()
                    if size <= 0:
                        return

                    location = locations.get(size - 1)
                    self.callback(location)
                except Exception:
                    return

            @java_method("(Ljava/lang/String;)V")
            def onProviderEnabled(self, provider):
                pass

            @java_method("(Ljava/lang/String;)V")
            def onProviderDisabled(self, provider):
                pass

except Exception:
    NativeAndroidLocationListener = None
    AndroidLooper = None
    AndroidLocationManager = None
    AndroidContext = None
    AndroidPythonActivity = None
if platform == "android":
    try:
        from jnius import autoclass, PythonJavaClass, java_method

        PythonActivity = autoclass(
            "org.kivy.android.PythonActivity"
        )
        Context = autoclass(
            "android.content.Context"
        )
        LocationManager = autoclass(
            "android.location.LocationManager"
        )
        Looper = autoclass(
            "android.os.Looper"
        )

        NATIVE_GPS_AVAILABLE = True

        # Native Android services used for urgent SOS assignment alerts.
        AndroidVibrator = autoclass("android.os.Vibrator")
        AndroidRingtoneManager = autoclass("android.media.RingtoneManager")

    except Exception as e:
        print("ANDROID GPS IMPORT ERROR:", repr(e))
        PythonActivity = None
        Context = None
        LocationManager = None
        Looper = None
        PythonJavaClass = None
        java_method = None
        NATIVE_GPS_AVAILABLE = False
else:
    PythonActivity = None
    Context = None
    LocationManager = None
    Looper = None
    PythonJavaClass = None
    java_method = None
    NATIVE_GPS_AVAILABLE = False
    AndroidVibrator = None
    AndroidRingtoneManager = None


if platform != "android":
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

if platform != "android":
    Window.size = (390, 760)

if platform == "android":
    Window.softinput_mode = "below_target"
Window.clearcolor = (0.94, 0.96, 0.98, 1)

if platform == "android" and NATIVE_GPS_AVAILABLE:

    class NativeLocationListener(PythonJavaClass):
        """
        Native Android LocationListener.

        This is used only as a fallback when a recent last-known
        location is not available.
        """

        __javainterfaces__ = [
            "android/location/LocationListener"
        ]

        def __init__(self, callback):
            super().__init__()
            self.callback = callback

        @java_method("(Landroid/location/Location;)V")
        def onLocationChanged(self, location):
            try:
                latitude = location.getLatitude()
                longitude = location.getLongitude()

                Clock.schedule_once(
                    lambda _dt,
                    lat=float(latitude),
                    lon=float(longitude):
                    self.callback(lat, lon),
                    0
                )
            except Exception:
                pass

        @java_method("(Ljava/lang/String;)V")
        def onProviderEnabled(self, provider):
            pass

        @java_method("(Ljava/lang/String;)V")
        def onProviderDisabled(self, provider):
            pass

        @java_method(
            "(Ljava/lang/String;ILandroid/os/Bundle;)V"
        )
        def onStatusChanged(
            self,
            provider,
            status,
            extras
        ):
            pass


class NativeGPS:
    """Reliable Android location helper for SOS and officer positioning."""

    def __init__(self):
        self.location_manager = None
        self.listener = None

        if not NATIVE_GPS_AVAILABLE:
            return

        try:
            activity = PythonActivity.mActivity
            self.location_manager = activity.getSystemService(
                Context.LOCATION_SERVICE
            )
        except Exception:
            self.location_manager = None

    def get_location(self, callback):
        """Return the best recent location, otherwise request a fresh one."""
        if self.location_manager is None:
            raise RuntimeError("Android location service is unavailable.")

        providers = (
            LocationManager.GPS_PROVIDER,
            LocationManager.NETWORK_PROVIDER,
            LocationManager.PASSIVE_PROVIDER,
        )

        # Prefer the newest cached fix. This makes SOS much faster when the
        # phone has recently obtained a location from Maps or Android itself.
        known_locations = []
        for provider in providers:
            location = self._last_known(provider)
            if location is not None:
                known_locations.append(location)

        if known_locations:
            try:
                location = max(known_locations, key=lambda item: item.getTime())
            except Exception:
                location = known_locations[0]

            latitude = float(location.getLatitude())
            longitude = float(location.getLongitude())
            Clock.schedule_once(
                lambda _dt, lat=latitude, lon=longitude: callback(lat, lon),
                0
            )
            return

        # No cached fix: listen to both network and GPS. Network location is
        # often returned much faster indoors, while GPS provides a precise fix
        # when satellites are available.
        self.listener = NativeLocationListener(callback)
        started = False
        errors = []

        for provider in (
            LocationManager.NETWORK_PROVIDER,
            LocationManager.GPS_PROVIDER,
        ):
            try:
                if self.location_manager.isProviderEnabled(provider):
                    self.location_manager.requestLocationUpdates(
                        provider,
                        1000,
                        0.0,
                        self.listener,
                        Looper.getMainLooper()
                    )
                    started = True
            except Exception as error:
                errors.append(str(error))

        if not started:
            self.listener = None
            detail = "; ".join(errors)
            if detail:
                raise RuntimeError(
                    f"Location providers could not be started: {detail}"
                )
            raise RuntimeError(
                "Phone Location is turned off. Enable Location/GPS and try again."
            )

    def _last_known(self, provider):
        try:
            return self.location_manager.getLastKnownLocation(provider)
        except Exception:
            return None

    def stop(self):
        if self.location_manager is not None and self.listener is not None:
            try:
                self.location_manager.removeUpdates(self.listener)
            except Exception:
                pass
        self.listener = None


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
        email: str,
        personal_email: str,
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
                "email": email,
                "personalEmail": personal_email,
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

    def verify_email(self, email: str, code: str) -> dict[str, Any]:
        response = requests.post(f"{self.backend_url}/api/users/verify-email", data={"email": email, "code": code}, timeout=REQUEST_TIMEOUT)
        self._raise_for_error(response)
        return response.json()

    def resend_verification(self, email: str) -> dict[str, Any]:
        response = requests.post(f"{self.backend_url}/api/users/resend-verification", data={"email": email}, timeout=REQUEST_TIMEOUT)
        self._raise_for_error(response)
        return response.json()

    def forgot_password(self, email: str) -> dict[str, Any]:
        response = requests.post(f"{self.backend_url}/api/users/forgot-password", data={"email": email}, timeout=REQUEST_TIMEOUT)
        self._raise_for_error(response)
        return response.json()

    def reset_password(self, email: str, code: str, new_password: str) -> dict[str, Any]:
        response = requests.post(f"{self.backend_url}/api/users/reset-password", data={"email": email, "code": code, "newPassword": new_password}, timeout=REQUEST_TIMEOUT)
        self._raise_for_error(response)
        return response.json()

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

    def update_emergency_location(self, emergency_id: int, latitude: float, longitude: float) -> dict[str, Any]:
        response = requests.put(
            f"{self.backend_url}/api/emergency/{emergency_id}/location",
            headers=self.authorization_headers(),
            params={"latitude": latitude, "longitude": longitude},
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
            f"{self.backend_url}/api/incidents/officer/unresolved",

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

    def resolve_incident(
        self, incident_id: int, validity: str, review: str
    ) -> dict[str, Any]:
        response = requests.put(
            f"{self.backend_url}/api/incidents/{incident_id}/resolve",
            headers=self.authorization_headers(),
            params={"validity": validity, "review": review},
            timeout=REQUEST_TIMEOUT
        )
        self._raise_for_error(response)
        return response.json()

    def resolve_emergency_review(
        self, emergency_id: int, false_alert: bool, review: str
    ) -> dict[str, Any]:
        response = requests.put(
            f"{self.backend_url}/api/emergency/{emergency_id}/resolve-review",
            headers=self.authorization_headers(),
            params={"falseAlert": str(false_alert).lower(), "review": review},
            timeout=REQUEST_TIMEOUT
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
        email = self.ids.register_email.text.strip().lower()
        personal_email = self.ids.register_personal_email.text.strip().lower()

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
            email,
            personal_email,
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

        if not personal_email.endswith("@gmail.com"):
            self.status_message = "Enter a valid personal Gmail address."
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
                email,
                personal_email,
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
        email: str,
        personal_email: str,
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
                email=email,
                personal_email=personal_email,
                password=password,
                role_name=role_name,
                campus_id=campus_id
            )

            Clock.schedule_once(
                lambda _dt:
                self._registration_success(
                    student_staff_number, email, personal_email
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
        student_staff_number: str,
        email: str,
        personal_email: str
    ) -> None:

        self.loading = False
        self.status_message = ""

        self.ids.register_number.text = ""
        self.ids.register_first_name.text = ""
        self.ids.register_last_name.text = ""
        self.ids.register_phone.text = ""
        self.ids.register_email.text = ""
        self.ids.register_personal_email.text = ""
        self.ids.register_password.text = ""
        self.ids.register_confirm_password.text = ""
        self.ids.register_role.text = "Student"
        self.ids.register_campus.text = "Alice Campus"

        app = App.get_running_app()
        login_screen = app.root.get_screen("login")

        login_screen.ids.login_number.text = (
            student_staff_number
        )

        verify_screen = app.root.get_screen("verify_email")
        verify_screen.email = email
        verify_screen.status_message = f"A 6-digit OTP was sent to {personal_email}."
        app.root.transition.direction = "left"
        app.root.current = "verify_email"

    def _registration_failed(
        self,
        message: str
    ) -> None:

        self.loading = False
        self.status_message = message


class VerifyEmailScreen(Screen):
    email = StringProperty("")
    status_message = StringProperty("")
    loading = BooleanProperty(False)

    def verify(self):
        code = self.ids.verify_code.text.strip()
        if len(code) != 6: self.status_message = "Enter the 6-digit OTP."; return
        self.loading = True
        threading.Thread(target=self._verify, args=(code,), daemon=True).start()
    def _verify(self, code):
        try:
            App.get_running_app().api.verify_email(self.email, code)
            Clock.schedule_once(lambda _dt: self._done(), 0)
        except Exception as e:
            Clock.schedule_once(lambda _dt, m=str(e): self._fail(m), 0)
    def _done(self):
        self.loading=False; self.ids.verify_code.text=""
        login=App.get_running_app().root.get_screen("login")
        login.status_message="Email verified successfully. You may now sign in."
        App.get_running_app().root.current="login"
    def _fail(self,m): self.loading=False; self.status_message=m
    def resend(self):
        try:
            App.get_running_app().api.resend_verification(self.email); self.status_message="A new OTP was sent."
        except Exception as e: self.status_message=str(e)

class ForgotPasswordScreen(Screen):
    status_message = StringProperty("")
    code_sent = BooleanProperty(False)
    def send_code(self):
        email=self.ids.reset_email.text.strip().lower()
        if not email.endswith("@gmail.com"): self.status_message="Enter your registered personal Gmail address."; return
        try:
            App.get_running_app().api.forgot_password(email); self.code_sent=True
            self.status_message="If the email is registered, a reset OTP has been sent."
        except Exception as e: self.status_message=str(e)
    def reset(self):
        email=self.ids.reset_email.text.strip().lower(); code=self.ids.reset_code.text.strip()
        pw=self.ids.reset_password.text; confirm=self.ids.reset_confirm.text
        if len(code)!=6: self.status_message="Enter the 6-digit OTP."; return
        if len(pw)<8: self.status_message="Password must contain at least 8 characters."; return
        if pw!=confirm: self.status_message="Passwords do not match."; return
        try:
            App.get_running_app().api.reset_password(email,code,pw)
            login=App.get_running_app().root.get_screen("login"); login.status_message="Password reset successfully. Sign in with your new password."
            self.ids.reset_code.text=""; self.ids.reset_password.text=""; self.ids.reset_confirm.text=""
            App.get_running_app().root.current="login"
        except Exception as e: self.status_message=str(e)

class UserDashboardScreen(Screen):
    welcome_text = StringProperty("Welcome")
    sos_suspended = BooleanProperty(False)
    account_type = StringProperty("User")
    sos_loading = BooleanProperty(False)
    sos_status = StringProperty("")
    sos_button_text = StringProperty("EMERGENCY\nSOS")
    sos_tap_count = 0
    _sos_tap_reset_event = None
    _sos_latitude = None
    _sos_longitude = None
    _sos_request_started = False
    _sos_location_timeout_event = None

    def on_pre_enter(self, *args) -> None:
        threading.Thread(target=self._refresh_sos_access, daemon=True).start()

    def _refresh_sos_access(self) -> None:
        try:
            user = App.get_running_app().api.get_current_user()
            Clock.schedule_once(lambda _dt, u=user: self._apply_sos_access(u), 0)
        except Exception:
            pass

    def _apply_sos_access(self, user) -> None:
        App.get_running_app().current_user = user
        self.sos_suspended = not bool(user.get("emergencyButtonEnabled", True))
        if self.sos_suspended:
            self.sos_button_text = "SOS SUSPENDED"
            self.sos_status = "Emergency SOS access is suspended. Contact Campus Security/Admin."
        elif self.sos_button_text == "SOS SUSPENDED":
            self.sos_button_text = "EMERGENCY\nSOS"
            self.sos_status = ""

    def open_feature(self, feature_name: str) -> None:
        """Open a student/staff dashboard feature without terminating the app."""
        screens = {
            "Report an Incident": "report_incident",
            "My Reports": "my_reports",
            "Emergency Contacts": "emergency_contacts",
            "Notifications": "user_notifications",
        }
        screen_name = screens.get(feature_name)
        if not screen_name:
            self.sos_status = f"{feature_name} is unavailable."
            return
        app = App.get_running_app()
        app.root.transition.direction = "left"
        app.root.current = screen_name

    def emergency_button_pressed(self) -> None:
        """Require three presses within five seconds before activating SOS."""
        if self.sos_suspended:
            self.sos_status = "Emergency SOS access is suspended. Contact Campus Security/Admin."
            return
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

        self.sos_loading = True
        self._sos_request_started = False
        self._sos_latitude = None
        self._sos_longitude = None
        self.sos_status = "Getting your location and sending SOS..."
        self.sos_button_text = "GETTING LOCATION..."

        if platform != "android" or not NATIVE_GPS_AVAILABLE:
            self._sos_failed(
                "Emergency GPS requires the Android app with location permission enabled."
            )
            return

        self._ensure_sos_location_permission()

    def _ensure_sos_location_permission(self) -> None:
        """Request Android location permission before accessing GPS."""
        if check_permission is None or Permission is None:
            self._start_native_sos_location()
            return

        fine = Permission.ACCESS_FINE_LOCATION
        coarse = Permission.ACCESS_COARSE_LOCATION
        if check_permission(fine) or check_permission(coarse):
            self._start_native_sos_location()
            return

        if request_permissions is None:
            self._sos_failed("Android location permission API is unavailable.")
            return

        request_permissions([fine, coarse], self._on_sos_permissions_result)

    def _on_sos_permissions_result(self, permissions, grants) -> None:
        granted = any(bool(value) for value in grants) if grants else False
        if not granted:
            self._sos_failed(
                "Location permission was denied. Enable Location for UFH Campus Security in Android settings."
            )
            return
        Clock.schedule_once(lambda _dt: self._start_native_sos_location(), 0)

    def _start_native_sos_location(self) -> None:
        """Start native Android GPS for the emergency SOS."""
        if not self.sos_loading:
            return

        try:
            self.sos_status = "Getting your current GPS/network location..."
            self.native_sos_gps = NativeGPS()
            self.native_sos_gps.get_location(self._on_sos_location)

            if self._sos_location_timeout_event is not None:
                self._sos_location_timeout_event.cancel()
            self._sos_location_timeout_event = Clock.schedule_once(
                self._sos_location_timed_out, 12
            )
        except Exception as error:
            self._sos_failed(
                f"Could not get your GPS location: {error}"
            )

    def _sos_location_timed_out(self, _dt) -> None:
        """Stop waiting if Android cannot provide a location fix."""
        self._sos_location_timeout_event = None
        if not self.sos_loading or self._sos_request_started:
            return
        self._sos_failed(
            "Could not get your location within 12 seconds. "
            "Make sure Phone Location is ON, allow location permission, "
            "and try again near a window or outdoors."
        )

    def _on_sos_location(
        self,
        latitude: float,
        longitude: float
    ) -> None:
        """Receive native Android GPS coordinates and start the SOS request."""
        if self._sos_request_started:
            return

        if self._sos_location_timeout_event is not None:
            self._sos_location_timeout_event.cancel()
            self._sos_location_timeout_event = None

        try:
            latitude = float(latitude)
            longitude = float(longitude)

            if not (
                -90 <= latitude <= 90
                and -180 <= longitude <= 180
            ):
                self._sos_failed(
                    "The phone returned invalid GPS coordinates."
                )
                return

            self._sos_latitude = latitude
            self._sos_longitude = longitude
            self._sos_request_started = True

            if hasattr(self, "native_sos_gps"):
                self.native_sos_gps.stop()

            self.sos_status = "Location found. Sending emergency alert..."
            self.sos_button_text = "SENDING SOS..."

            threading.Thread(
                target=self._send_sos_request,
                daemon=True
            ).start()
        except Exception as error:
            self._sos_failed(str(error))

    def _send_sos_request(self) -> None:
        """Send GPS to the backend; the session identifies the registered user."""
        try:
            result = App.get_running_app().api.create_emergency(
                self._sos_latitude,
                self._sos_longitude,
                "GENERAL_EMERGENCY",
                "Emergency SOS from the mobile application."
            )
            emergency_id = result.get("emergencyId", "")
            Clock.schedule_once(
                lambda _dt, alert_id=emergency_id: self._sos_sent(alert_id),
                0
            )
        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error): self._sos_failed(message),
                0
            )

    def _sos_sent(self, emergency_id) -> None:
        """Display successful SOS confirmation."""
        self.sos_loading = False
        self._sos_request_started = False
        self.sos_button_text = "EMERGENCY\nSOS"
        self.sos_status = f"SOS sent successfully. Alert #{emergency_id}"
        self.active_emergency_id = int(emergency_id) if str(emergency_id).isdigit() else None
        if getattr(self, "_live_location_event", None) is not None:
            self._live_location_event.cancel()
        if self.active_emergency_id is not None:
            self._live_location_event = Clock.schedule_interval(self._share_active_emergency_location, 15)
        App.get_running_app().show_message(
            "Emergency Alert Sent",
            "Your current location and registered account details were sent "
            "to Campus Security."
        )

    def _share_active_emergency_location(self, _dt) -> None:
        """Refresh the active SOS location while the app remains open."""
        emergency_id = getattr(self, "active_emergency_id", None)
        if not emergency_id or platform != "android" or not NATIVE_GPS_AVAILABLE:
            return
        try:
            tracker = NativeGPS()
            self._active_location_tracker = tracker
            tracker.get_location(self._on_active_emergency_location)
        except Exception:
            pass

    def _on_active_emergency_location(self, latitude: float, longitude: float) -> None:
        emergency_id = getattr(self, "active_emergency_id", None)
        if not emergency_id:
            return
        try:
            latitude, longitude = float(latitude), float(longitude)
            if hasattr(self, "_active_location_tracker"):
                self._active_location_tracker.stop()
            threading.Thread(
                target=self._send_active_emergency_location,
                args=(emergency_id, latitude, longitude), daemon=True
            ).start()
        except Exception:
            pass

    def _send_active_emergency_location(self, emergency_id: int, latitude: float, longitude: float) -> None:
        try:
            App.get_running_app().api.update_emergency_location(
                emergency_id, latitude, longitude
            )
        except Exception:
            pass

    def _sos_failed(self, message: str) -> None:
        """Reset the SOS interface after an error."""
        if self._sos_location_timeout_event is not None:
            self._sos_location_timeout_event.cancel()
            self._sos_location_timeout_event = None

        try:
            if hasattr(self, "native_sos_gps"):
                self.native_sos_gps.stop()
        except Exception:
            pass

        self.sos_loading = False
        self._sos_request_started = False
        self.sos_button_text = "EMERGENCY\nSOS"
        self.sos_status = str(message)


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
    active_emergency_count = StringProperty("Assigned Emergencies")

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
        if not NATIVE_GPS_AVAILABLE:
            self.status_message = (
                "Native Android GPS is unavailable."
            )
            return

        self.status_message = (
            "Capturing officer GPS location..."
        )

        try:
            self.native_gps = NativeGPS()

            self.native_gps.get_location(
                self._on_officer_location
            )

        except Exception as error:
            self.status_message = (
                f"Could not get GPS location: {error}"
            )

    def _on_officer_location(
        self,
        latitude: float,
        longitude: float
    ) -> None:
        self.status_message = "Officer GPS location captured."

        try:
            latitude = float(latitude)
            longitude = float(longitude)

            if not (
                -90 <= latitude <= 90
                and -180 <= longitude <= 180
            ):
                self.status_message = (
                    "Invalid GPS coordinates received."
                )
                return

            self.officer_latitude = latitude
            self.officer_longitude = longitude

            self.status_message = (
                f"GPS location captured: "
                f"{latitude:.6f}, {longitude:.6f}"
            )

            threading.Thread(
                target=self._send_officer_location,
                args=(latitude, longitude),
                daemon=True
            ).start()

        except Exception as error:
            self.status_message = (
                f"Could not process GPS location: {error}"
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
            "Assigned Emergencies": "officer_alerts",
            "Incident Reports": "officer_incidents",
            "Notifications": "officer_notifications"
        }
        screen_name = screens.get(feature_name)
        if not screen_name:
            return
        app = App.get_running_app()
        app.root.transition.direction = "left"
        app.root.current = screen_name
class ReportIncidentScreen(Screen):
    location_values = ListProperty(["Loading locations..."])
    status_message = StringProperty("")
    loading = BooleanProperty(False)

    def on_pre_enter(self, *args):
        self.status_message = ""
        self.load_locations()

    def load_locations(self):
        def worker():
            try:
                locations = App.get_running_app().api.get_locations()

                if not locations:
                    raise Exception("No campus locations were returned.")

                values = []

                for location in locations:
                    if isinstance(location, dict):
                        name = (
                            location.get("name")
                            or location.get("locationName")
                            or location.get("campusName")
                            or location.get("description")
                        )
                    else:
                        name = str(location)

                    if name:
                        values.append(str(name))

                if not values:
                    raise Exception("No valid campus locations were found.")

                Clock.schedule_once(
                    lambda _dt, items=values:
                    self._set_locations(items),
                    0
                )

            except Exception as error:
                Clock.schedule_once(
                    lambda _dt, message=str(error):
                    self._location_error(message),
                    0
                )

        threading.Thread(
            target=worker,
            daemon=True
        ).start()

    def _set_locations(self, values):
        self.location_values = values

        if "report_location" in self.ids:
            self.ids.report_location.text = values[0]

        self.status_message = ""

    def _location_error(self, message):
        self.location_values = ["Location unavailable"]

        if "report_location" in self.ids:
            self.ids.report_location.text = "Location unavailable"

        self.status_message = (
            f"Could not load campus locations: {message}"
        )

    def submit_report(self):
        if self.loading:
            return

        incident_type = self.ids.report_type.text.strip()
        location = self.ids.report_location.text.strip()
        severity = self.ids.report_severity.text.strip()
        description = self.ids.report_description.text.strip()

        if not incident_type:
            self.status_message = "Please select an incident type."
            return

        if not location or location in (
            "Loading locations...",
            "Location unavailable"
        ):
            self.status_message = "Please select a campus location."
            return

        if not severity:
            self.status_message = "Please select the incident severity."
            return

        if not description:
            self.status_message = "Please describe what happened."
            return

        if len(description) < 5:
            self.status_message = (
                "Please provide a little more detail about the incident."
            )
            return

        self.loading = True
        self.status_message = "Submitting incident report..."

        threading.Thread(
            target=self._submit_report,
            args=(
                incident_type,
                location,
                severity,
                description
            ),
            daemon=True
        ).start()

    def _submit_report(
        self,
        incident_type,
        location,
        severity,
        description
    ):
        try:
            result = App.get_running_app().api.create_incident(
                incident_type,
                location,
                severity,
                description
            )

            Clock.schedule_once(
                lambda _dt, response=result:
                self._report_submitted(response),
                0
            )

        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error):
                self._report_failed(message),
                0
            )

    def _report_submitted(self, result):
        self.loading = False

        incident_id = ""

        if isinstance(result, dict):
            incident_id = (
                result.get("incidentId")
                or result.get("id")
                or result.get("reportId")
                or ""
            )

        if incident_id:
            self.status_message = (
                f"Incident reported successfully. "
                f"Report #{incident_id}"
            )
        else:
            self.status_message = (
                "Incident reported successfully."
            )

        self.ids.report_description.text = ""

        App.get_running_app().show_message(
            "Incident Reported",
            "Your incident report was submitted successfully."
        )

    def _report_failed(self, message):
        self.loading = False
        self.status_message = (
            f"Could not submit incident report: {message}"
        )
class MyReportsScreen(Screen):
    reports_text = StringProperty("")
    status_message = StringProperty("")

    def on_pre_enter(self, *args):
        self.refresh_reports()

    def refresh_reports(self):
        self.status_message = "Loading your reports..."

        threading.Thread(
            target=self._load_reports,
            daemon=True
        ).start()

    def _load_reports(self):
        try:
            reports = App.get_running_app().api.get_my_reports()

            Clock.schedule_once(
                lambda _dt, items=reports:
                self._display_reports(items),
                0
            )

        except Exception as error:
            Clock.schedule_once(
                lambda _dt, message=str(error):
                self._reports_error(message),
                0
            )

    def _display_reports(self, reports):
        if not reports:
            self.reports_text = (
                "You have not submitted any incident reports yet."
            )
            self.status_message = ""
            return

        lines = []

        for index, report in enumerate(reports, start=1):
            if not isinstance(report, dict):
                continue

            report_id = (
                report.get("incidentId")
                or report.get("id")
                or report.get("reportId")
                or index
            )

            incident_type = (
                report.get("incidentType")
                or report.get("type")
                or "Unknown"
            )

            location = (
                report.get("locationName")
                or report.get("location")
                or "Unknown"
            )

            severity = (
                report.get("severity")
                or "Unknown"
            )

            description = (
                report.get("description")
                or "No description"
            )

            status = (
                report.get("status")
                or "Unknown"
            )

            date_reported = (
                report.get("dateReported")
                or report.get("createdAt")
                or report.get("reportedAt")
                or "Unknown"
            )

            lines.append(
                f"Report #{report_id}\n"
                f"Incident: {incident_type}\n"
                f"Location: {location}\n"
                f"Severity: {severity}\n"
                f"Status: {status}\n"
                f"Date: {date_reported}\n"
                f"Description: {description}\n"
                f"{'-' * 45}\n"
            )

        self.reports_text = "\n".join(lines)
        self.status_message = ""

    def _reports_error(self, message):
        self.status_message = (
            f"Could not load your reports: {message}"
        )
        self.reports_text = ""

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

    def _on_location(
        self,
        latitude: float,
        longitude: float
    ) -> None:
        try:
            self.latitude = float(latitude)
            self.longitude = float(longitude)

            if not (
                -90 <= self.latitude <= 90
                and -180 <= self.longitude <= 180
            ):
                self.status_message = (
                    "The phone returned invalid GPS coordinates."
                )
                return

            if hasattr(self, "native_gps"):
                self.native_gps.stop()

            self.location_text = (
                f"Location captured: "
                f"{self.latitude:.6f}, "
                f"{self.longitude:.6f}"
            )

            self.status_message = (
                "GPS location captured successfully."
            )

            Clock.schedule_once(
                lambda _dt: self._show_location(),
                0
            )

        except Exception as error:
            self.status_message = (
                f"Could not process GPS location: {error}"
            )


    def _show_location(self) -> None:
        self.location_text = (
            f"GPS: {self.latitude:.6f}, "
            f"{self.longitude:.6f}"
        )

        self.status_message = (
            "Location captured. You can send the alert."
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
    alerts_text = StringProperty("Loading assigned emergencies...")
    status_message = StringProperty("")
    loading = BooleanProperty(False)
    case_values = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.alerts_by_label = {}
        self.selected_alert = None

    def on_pre_enter(self, *args) -> None:
        self.refresh_alerts()

    def refresh_alerts(self) -> None:
        if self.loading:
            return
        self.loading = True
        self.status_message = "Loading your assigned emergencies..."
        threading.Thread(target=self._load_alerts, daemon=True).start()

    def _load_alerts(self) -> None:
        try:
            alerts = App.get_running_app().api.get_available_emergencies()
            Clock.schedule_once(lambda _dt, items=alerts: self._render_alerts(items), 0)
        except Exception as error:
            Clock.schedule_once(lambda _dt, m=str(error): self._request_failed(m), 0)

    def _render_alerts(self, alerts) -> None:
        self.loading = False
        self.status_message = ""
        box = self.ids.emergency_case_list
        box.clear_widgets()
        self.alerts_by_label = {}
        self.case_values = []
        if not alerts:
            self.alerts_text = "No active emergencies are currently assigned to you."
            self.ids.selected_emergency.text = "No emergency selected."
            self.selected_alert = None
            return
        self.alerts_text = "Tap an emergency below to view the person, accept it, respond, or close it."
        for alert in alerts:
            user = alert.get("user") or {}
            name = f"{user.get('firstName','')} {user.get('lastName','')}".strip() or "Unknown user"
            etype = str(alert.get("emergencyType") or "Emergency").replace("_", " ").title()
            status = str(alert.get("alertStatus") or "SENT").replace("_", " ")
            number = user.get("studentStaffNumber") or "Not supplied"
            phone = user.get("phoneNumber") or "Not supplied"
            lat, lon = alert.get("latitude"), alert.get("longitude")
            gps = f"{lat}, {lon}" if lat is not None and lon is not None else "Not available"
            text = (f"SOS #{alert.get('emergencyId')}  •  {etype}\n"
                    f"{name}  |  {number}\n"
                    f"Phone: {phone}\n"
                    f"Status: {status}\n"
                    f"Latest location: {gps}")
            btn = Button(text=text, size_hint_y=None, height=205, halign="left", valign="middle",
                         font_size="15sp", padding=(18, 14), background_normal="",
                         background_color=(1,1,1,1), color=(0.04,0.15,0.27,1))
            btn.bind(size=lambda w, _v: setattr(w, "text_size", (max(w.width-36,1), max(w.height-24,1))))
            btn.bind(on_release=lambda _b, item=alert: self.select_alert(item))
            box.add_widget(btn)

    def select_alert(self, alert) -> None:
        self.selected_alert = alert
        user = alert.get("user") or {}
        name = f"{user.get('firstName','')} {user.get('lastName','')}".strip() or "Unknown user"
        created = str(alert.get("createdAt") or "").replace("T", " ")[:19]
        lat, lon = alert.get("latitude"), alert.get("longitude")
        self.ids.selected_emergency.text = (
            f"Selected SOS #{alert.get('emergencyId')}\n"
            f"Person: {name}\n"
            f"Student/staff no.: {user.get('studentStaffNumber') or 'Not supplied'}\n"
            f"Phone: {user.get('phoneNumber') or 'Not supplied'}\n"
            f"Email: {user.get('email') or 'Not supplied'}\n"
            f"Sent: {created or 'Not supplied'}\n"
            f"Latest GPS: {lat}, {lon}\n"
            f"Description: {alert.get('description') or 'Emergency SOS'}"
        )
        self.status_message = "Emergency selected."

    def get_selected_alert(self):
        if not self.selected_alert:
            self.status_message = "Select an assigned emergency first."
            return None
        return self.selected_alert

    def accept_emergency(self) -> None:
        alert = self.get_selected_alert()
        if not alert: return
        self._start_status_update(alert, "ACKNOWLEDGED")

    def start_responding(self) -> None:
        alert = self.get_selected_alert()
        if not alert: return
        self._start_status_update(alert, "RESPONDING")

    def _start_status_update(self, alert, status) -> None:
        self.loading = True
        self.status_message = "Updating emergency..."
        threading.Thread(target=self._status_request,
                         args=(int(alert["emergencyId"]), status), daemon=True).start()

    def _status_request(self, emergency_id, status) -> None:
        try:
            App.get_running_app().api.update_emergency_status(emergency_id, status)
            Clock.schedule_once(lambda _dt: self._status_updated(status), 0)
        except Exception as error:
            Clock.schedule_once(lambda _dt, m=str(error): self._request_failed(m), 0)

    def _status_updated(self, status) -> None:
        self.loading = False
        self.status_message = f"Emergency updated to {status.replace('_',' ')}."
        self.refresh_alerts()

    def resolve_emergency(self) -> None:
        alert = self.get_selected_alert()
        if not alert: return
        validity = self.ids.emergency_validity.text
        review = self.ids.emergency_review.text.strip()
        if validity not in ("GENUINE_EMERGENCY", "FALSE_EMERGENCY"):
            self.status_message = "Choose Genuine Emergency or False Emergency."
            return
        if len(review) < 10:
            self.status_message = "Write a short officer review of at least 10 characters."
            return
        self.loading = True
        threading.Thread(target=self._resolve_request,
                         args=(int(alert["emergencyId"]), validity == "FALSE_EMERGENCY", review),
                         daemon=True).start()

    def _resolve_request(self, emergency_id, false_alert, review) -> None:
        try:
            App.get_running_app().api.resolve_emergency_review(emergency_id, false_alert, review)
            Clock.schedule_once(lambda _dt: self._resolved(false_alert), 0)
        except Exception as error:
            Clock.schedule_once(lambda _dt, m=str(error): self._request_failed(m), 0)

    def _resolved(self, false_alert) -> None:
        self.loading = False
        self.selected_alert = None
        self.ids.emergency_review.text = ""
        self.ids.emergency_validity.text = "Select emergency validity"
        self.status_message = "Emergency closed as FALSE." if false_alert else "Emergency closed as GENUINE."
        self.refresh_alerts()

    def open_map(self) -> None:
        alert = self.get_selected_alert()
        if not alert: return
        lat, lon = alert.get("latitude"), alert.get("longitude")
        if lat is None or lon is None:
            self.status_message = "No GPS location is available for this emergency."
            return
        webbrowser.open(f"https://www.google.com/maps/search/?api=1&query={lat},{lon}")
        self.status_message = "Opening the latest emergency location in Maps."

    def _request_failed(self, message) -> None:
        self.loading = False
        self.status_message = message


class OfficerIncidentsScreen(Screen):
    incidents_text = StringProperty("Loading incident cases...")
    status_message = StringProperty("")
    loading = BooleanProperty(False)
    selected_incident = None

    def on_pre_enter(self, *args) -> None:
        self.refresh_incidents()

    def refresh_incidents(self) -> None:
        if self.loading:
            return
        self.loading = True
        self.status_message = "Loading incident cases..."
        threading.Thread(target=self._load_incidents, daemon=True).start()

    def _load_incidents(self) -> None:
        try:
            incidents = App.get_running_app().api.get_officer_incidents()
            active = [i for i in incidents if i.get("incidentStatus") not in ("RESOLVED", "CLOSED")]
            Clock.schedule_once(lambda _dt, items=active: self._render_incidents(items), 0)
        except Exception as error:
            Clock.schedule_once(lambda _dt, m=str(error): self._request_failed(m), 0)

    def _render_incidents(self, incidents) -> None:
        self.loading = False
        self.status_message = ""
        box = self.ids.incident_case_list
        box.clear_widgets()
        if not incidents:
            self.incidents_text = "No unresolved incident reports."
            return
        self.incidents_text = "Tap a case below to select it."
        for incident in incidents:
            user = incident.get("user") or {}
            loc = incident.get("location") or {}
            officer = incident.get("assignedOfficer") or {}
            assigned = "Unassigned"
            if officer:
                assigned = f"{officer.get('firstName','')} {officer.get('lastName','')}".strip() or "Assigned"
            text = (
                f"{incident.get('incidentType') or 'Incident'} — {loc.get('locationName') or 'Unknown location'}\n"
                f"{incident.get('severity') or 'MEDIUM'} | {str(incident.get('incidentStatus') or 'REPORTED').replace('_',' ')}\n"
                f"Reported by: {user.get('firstName','')} {user.get('lastName','')}\n"
                f"Assigned: {assigned}"
            )
            btn = Button(
                text=text, size_hint_y=None, height=180,
                halign="left", valign="middle", font_size="16sp",
                padding=(18, 14), background_normal="",
                background_color=(1, 1, 1, 1), color=(0.04, 0.15, 0.27, 1)
            )
            btn.bind(size=lambda widget, _value: setattr(
                widget, "text_size", (max(widget.width - 36, 1), max(widget.height - 24, 1))
            ))
            btn.bind(on_release=lambda _b, item=incident: self.select_incident(item))
            box.add_widget(btn)

    def select_incident(self, incident) -> None:
        self.selected_incident = incident
        loc = incident.get("location") or {}
        officer = incident.get("assignedOfficer") or {}
        assigned = "Unassigned" if not officer else f"{officer.get('firstName','')} {officer.get('lastName','')}".strip()
        self.ids.selected_case.text = (
            f"Selected: {incident.get('incidentType') or 'Incident'} at {loc.get('locationName') or 'Unknown'}\n"
            f"Status: {str(incident.get('incidentStatus') or 'REPORTED').replace('_',' ')} | Assigned: {assigned}\n"
            f"{incident.get('description') or 'No description'}"
        )
        self.status_message = "Case selected."

    def update_incident(self) -> None:
        if not self.selected_incident:
            self.status_message = "Select a case first."
            return

        status = self.ids.officer_incident_status.text
        incident_id = int(self.selected_incident["incidentId"])

        if status == "RESOLVED":
            validity = self.ids.case_validity.text
            review = self.ids.officer_review.text.strip()
            if validity not in ("GENUINE", "FALSE_REPORT"):
                self.status_message = "Choose whether the case was GENUINE or FALSE / FAKE."
                return
            if len(review) < 10:
                self.status_message = "Write a short officer review of at least 10 characters."
                return
            self.loading = True
            threading.Thread(
                target=self._resolve_request,
                args=(incident_id, validity, review),
                daemon=True
            ).start()
            return

        self.loading = True
        threading.Thread(
            target=self._update_request, args=(incident_id, status), daemon=True
        ).start()

    def _update_request(self, incident_id, status) -> None:
        try:
            App.get_running_app().api.update_incident_status(incident_id, status)
            Clock.schedule_once(lambda _dt: self._updated(f"Case updated to {status.replace('_',' ')}. You are now assigned to it."), 0)
        except Exception as error:
            Clock.schedule_once(lambda _dt, m=str(error): self._request_failed(m), 0)

    def _resolve_request(self, incident_id, validity, review) -> None:
        try:
            App.get_running_app().api.resolve_incident(incident_id, validity, review)
            Clock.schedule_once(lambda _dt: self._updated("Case resolved and officer review saved."), 0)
        except Exception as error:
            Clock.schedule_once(lambda _dt, m=str(error): self._request_failed(m), 0)

    def _updated(self, message) -> None:
        self.loading = False
        self.status_message = message
        self.selected_incident = None
        self.ids.officer_review.text = ""
        self.refresh_incidents()

    def _request_failed(self, message) -> None:
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
                    f"{str(item.get('notificationType') or 'Notification').replace('_', ' ').title()} - {read_text}\n"
                    f"{item.get('message')}\n"
                    f"{str(item.get('createdAt', '')).replace('T', ' ')[:16]}"
                )
                notification_id = item.get("notificationId")
                if notification_id is not None and not item.get("read"):
                    try:
                        App.get_running_app().api.mark_officer_notification_read(
                            int(notification_id)
                        )
                    except Exception:
                        pass
            text = "\n\n--------------------\n\n".join(lines)
            Clock.schedule_once(
                lambda _dt: self._loaded(text or "No notifications found."), 0

            )
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

        # Officer emergency watcher. It checks for newly assigned SOS cases while
        # the app process is running and raises a loud/vibrating phone alert.
        self._officer_emergency_watch = None
        self._known_emergency_ids = set()
        self._emergency_poll_busy = False

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
            self.start_officer_emergency_watch()
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

    def start_officer_emergency_watch(self) -> None:
        if self._officer_emergency_watch is not None:
            return
        # Prime immediately, then check frequently enough for an emergency app.
        self._poll_officer_emergencies(0)
        self._officer_emergency_watch = Clock.schedule_interval(
            self._poll_officer_emergencies, 5
        )

    def stop_officer_emergency_watch(self) -> None:
        if self._officer_emergency_watch is not None:
            self._officer_emergency_watch.cancel()
            self._officer_emergency_watch = None
        self._known_emergency_ids.clear()
        self._emergency_poll_busy = False

    def _poll_officer_emergencies(self, _dt) -> None:
        if self._emergency_poll_busy or not self.api.session_token:
            return
        role_name = self.extract_role_name(self.current_user)
        if role_name not in {"security officer", "security_officer", "security"}:
            return
        self._emergency_poll_busy = True
        threading.Thread(target=self._fetch_officer_emergencies_for_alert, daemon=True).start()

    def _fetch_officer_emergencies_for_alert(self) -> None:
        try:
            alerts = self.api.get_available_emergencies()
            current_ids = {
                int(item.get("emergencyId"))
                for item in alerts
                if str(item.get("emergencyId", "")).isdigit()
            }
            new_ids = current_ids - self._known_emergency_ids
            first_check = not self._known_emergency_ids
            self._known_emergency_ids = current_ids
            Clock.schedule_once(
                lambda _dt, count=len(current_ids): self._update_emergency_badge(count), 0
            )
            # On first login, vibrate for active assignments too so an officer cannot
            # silently miss an SOS that arrived before the dashboard opened. No popup
            # is shown, so multiple emergencies never block access to the app.
            if new_ids or (first_check and current_ids):
                newest = max(new_ids or current_ids)
                Clock.schedule_once(
                    lambda _dt, eid=newest: self.raise_urgent_emergency_alert(eid), 0
                )
        except Exception:
            pass
        finally:
            self._emergency_poll_busy = False

    def _update_emergency_badge(self, count: int) -> None:
        try:
            dashboard = self.root.get_screen("officer_dashboard")
            dashboard.active_emergency_count = (
                f"Assigned Emergencies ({count})" if count else "Assigned Emergencies"
            )
        except Exception:
            pass

    def raise_urgent_emergency_alert(self, emergency_id: int) -> None:
        # Non-blocking SOS alert: vibrate the officer's Android phone, but never
        # open a popup. This keeps the app usable when several emergencies arrive.
        if platform == "android":
            try:
                activity = PythonActivity.mActivity
                vibrator = activity.getSystemService(Context.VIBRATOR_SERVICE)
                if vibrator is not None:
                    # Distinct emergency vibration pattern: vibrate/pause/vibrate.
                    vibrator.vibrate(3000)
                    Clock.schedule_once(
                        lambda _dt, v=vibrator: v.vibrate(2000), 3.6
                    )
            except Exception as error:
                print("URGENT SOS VIBRATION ERROR:", repr(error))

        try:
            dashboard = self.root.get_screen("officer_dashboard")
            dashboard.status_message = (
                f"New emergency #{emergency_id} assigned. Open Assigned Emergencies."
            )
        except Exception:
            pass

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
        self.stop_officer_emergency_watch()
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
