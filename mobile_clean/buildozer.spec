[app]
title = UFH Campus Security
package.name = ufhcampussecurity
package.domain = za.ac.ufh
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,webp,json,atlas,ttf
version = 1.0.1
requirements = python3,kivy==2.3.1,requests,python-dotenv,plyer
orientation = portrait
fullscreen = 0

android.api = 35
android.minapi = 23
android.ndk_api = 23
android.accept_sdk_license = True
android.allow_cleartext = True
android.permissions = android.permission.INTERNET,android.permission.ACCESS_FINE_LOCATION,android.permission.ACCESS_COARSE_LOCATION,android.permission.READ_MEDIA_IMAGES
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
