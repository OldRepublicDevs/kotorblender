=== Results: 62 passed, 0 failed ===
PS C:\GitHub\kotorblender\test> make build
make: *** No rule to make target `build'.  Stop.
PS C:\GitHub\kotorblender\test> make build
make: *** No rule to make target `build'.  Stop.
PS C:\GitHub\kotorblender\test> make
make: *** No targets specified and no makefile found.  Stop.
PS C:\GitHub\kotorblender\test> cd ..
PS C:\GitHub\kotorblender> make build
C:/FPC/3.2.2/bin/i386-Win32/make wheel-download
make[1]: Entering directory `C:/GitHub/kotorblender'
python3 helper_scripts/makefile_fs.py clean-whl io_scene_kotor/wheels
Python was not found; run without arguments to install from the Microsoft Store, or disable this shortcut from Settings > Apps > Advanced app settings > App execution aliases.
make[1]: *** [wheel-download] Error 9009
make[1]: Leaving directory `C:/GitHub/kotorblender'
make: *** [build] Error 2
PS C:\GitHub\kotorblender> make
C:/FPC/3.2.2/bin/i386-Win32/make wheel-download
make[1]: Entering directory `C:/GitHub/kotorblender'
python3 helper_scripts/makefile_fs.py clean-whl io_scene_kotor/wheels
Python was not found; run without arguments to install from the Microsoft Store, or disable this shortcut from Settings > Apps > Advanced app settings > App execution aliases.
make[1]: *** [wheel-download] Error 9009
make[1]: Leaving directory `C:/GitHub/kotorblender'
make: *** [build] Error 2

please fix. rerun/fix until functional. Do not stop until done. Completion criteria:
- io_scene_kotor built with the make file and zipped
- pykotor included as a wheel and properly synced with this shit so everytime a build happens pykotor is strictly rrequired, fast failing when it's not available.
