import os
import sys
import winshell
from win32com.client import Dispatch


def create_vbs_script(script_path):
    vbs_file = os.path.join(os.path.dirname(script_path), "launch.vbs")
    
    vbs_exists = os.path.exists(vbs_file)
    
    vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "pythonw {script_path}", 0, False'''
    
    # Write the VBS script
    with open(vbs_file, 'w') as f:
        f.write(vbs_content)
    
    # Log whether the VBS file was created or overwritten
    if vbs_exists:
        print("launch.vbs was overwritten.")
    else:
        print("launch.vbs was created.")
    
    return vbs_file


def create_shortcut(vbs_file, icon_path, shortcut_name):
    desktop = winshell.desktop()
    shortcut_path = os.path.join(desktop, f"{shortcut_name}.lnk")
    
    # Check if the shortcut already exists
    shortcut_exists = os.path.exists(shortcut_path)
    
    # If the shortcut already exists, delete it before creating a new one
    if shortcut_exists:
        os.remove(shortcut_path)

    # Create a new shortcut
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.TargetPath = vbs_file
    shortcut.IconLocation = icon_path
    shortcut.WorkingDirectory = os.path.dirname(vbs_file)
    shortcut.save()

    if shortcut_exists:
        print(f"Shortcut '{shortcut_name}' was overwritten on the Desktop.")
    else:
        print(f"Shortcut '{shortcut_name}' was created on the Desktop.")


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    bot_script = os.path.join(current_dir, 'bot.py')
    icon_file = os.path.join(os.path.dirname(current_dir), 'resources', 'bard.ico')
    
    # Check if bot.py and bard.ico exist
    if not os.path.exists(bot_script):
        print("Error: bot.py not found!")
        sys.exit(1)
    
    if not os.path.exists(icon_file):
        print("Error: bard.ico not found!")
        sys.exit(1)

    vbs_file = create_vbs_script(bot_script)

    create_shortcut(vbs_file, icon_file, 'SkibidiBot')

    print("Installer complete! Shortcut and launch.vbs have been set up.")


if __name__ == "__main__":
    main()