[app]
title = Pergamino Precios
package.name = pergaminoprecios
package.domain = com.pergamino.precios
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0
requirements = python3,kivy==2.3.0,kivymd==1.2.0,requests,urllib3,charset-normalizer,idna,certifi
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2

[app:android]
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license_agreement = True
android.ant = auto
android.build_tools_version = 33.0.2
android.sdk_path = /usr/local/lib/android/sdk
p4a.branch = master
p4a.bootstrap = sdl2
p4a.setup_py = False
