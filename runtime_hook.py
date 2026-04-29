import os
import sys

# When running as a frozen (PyInstaller) app, add the extraction directory
# to the DLL search path so Windows can find bundled DLLs.
if getattr(sys, 'frozen', False):
    os.add_dll_directory(sys._MEIPASS)
