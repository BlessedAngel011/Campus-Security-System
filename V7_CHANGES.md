# v7 changes

- Password policy is now consistently at least 8 characters for normal registration, password reset, and admin-created security officer temporary passwords.
- Security-officer mobile sessions poll assigned emergencies every 5 seconds while the app process is running.
- A newly assigned SOS triggers an urgent in-app popup; on Android it also vibrates for about 3 seconds and plays the device alarm tone for up to about 8 seconds.
- Existing closest-officer assignment remains unchanged.

## Important background-delivery note
The urgent phone alert in this version works while the Kivy application process is running. Guaranteed delivery when Android has fully stopped/killed the app requires a push-notification service such as Firebase Cloud Messaging (FCM), plus server-side device-token registration. Do not describe the current polling alert as guaranteed background push.
