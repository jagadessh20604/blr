[app]
title = Bangalore Food Finder
package.name = bangalorefoodfinder
package.domain = org.foodfinder
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

requirements = python3,kivy,together,pillow

orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 31
android.minapi = 21
android.ndk = 25b
android.sdk = 31
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1 