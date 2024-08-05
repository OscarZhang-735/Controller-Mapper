@echo off
rmdir .\dist /s /q
rmdir .\build /s /q
pyinstaller main.spec --noconfirm
copy icon.ico .\dist\ControllerMapper
copy icon.png .\dist\ControllerMapper
copy config.json .\dist\ControllerMapper
copy controller.txt .\dist\ControllerMapper
rmdir .\build /s /q