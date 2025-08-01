"""
Copyright 2024 Netflix Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Module which contains the functionality to compile the python application into its platform-specific executable and
installer
"""
import platform
import os
import shutil
import subprocess
import importlib.util
import sys
import xml.etree.ElementTree as ET
from types import ModuleType
from typing import List


def get_current_folder() -> str:
    """ Get the current folder of this script

    Returns: The current folder of this script

    """
    return os.path.dirname(os.path.realpath(__file__))


def get_packages_folder() -> str:
    """ Get the src folder of this project

    Returns: The src folder of this project

    """
    return os.path.join(get_current_folder(), "packages")


def get_python_package_folder() -> str:
    """ Get the python package folder of this project

    Returns: The python package folder of this project

    """
    return os.path.join(get_packages_folder(), "open_vp_cal", "src", "open_vp_cal")


def import_module_from_filepath(filepath: str) -> ModuleType:
    """ Import a module from a given filepath

    Args:
        filepath: The filepath to the module to import

    Returns: The imported module

    """
    spec = importlib.util.spec_from_file_location("module.name", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_version_from_python_package() -> str:
    """ Get the version number from the python package

    Returns: The version number from the python package

    """
    python_folder = get_python_package_folder()
    init_file = os.path.join(python_folder, "__init__.py")
    init_module = import_module_from_filepath(init_file)
    return init_module.__version__


def get_python_package_resource_folder() -> str:
    """ Get the python package resource folder of this project

    Returns: The python package resource folder of this project

    """
    return os.path.join(get_python_package_folder(), "resources")


def get_additional_data_from_resources() -> List[str]:
    """ Get a list of additional data flags for the --add-data command of the pyinstaller

    Returns: A list of additional data flags for the --add-data command of the pyinstaller

    """
    add_data = []
    platform_sep = get_additional_data_seperator()
    target_folder = os.path.join(".", "open_vp_cal", "resources", ".")
    resources_folder = get_python_package_resource_folder()
    resources = os.listdir(resources_folder)
    for resource in resources:
        input_file = os.path.join(resources_folder, resource)
        if os.path.isdir(input_file):
            continue
        add_data.append(f"{input_file}{platform_sep}{target_folder}")
    return add_data


def get_additional_data_seperator() -> str:
    """ Get the path seperator used by pyinstaller for the platform we are running on

    Returns: The path seperator used by pyinstaller for the platform we are running on

    """
    if platform.system() == 'Windows':
        return ";"
    return ":"


def add_key_value_to_plist(plist_path: str, key_name: str, bool_value: bool) -> None:
    """ Adds a boolean value to the XML file, plist of the app when compiled on osx to force dak mode

    Args:
        plist_path: The path to the plist file
        key_name: The name of the key to add
        bool_value: The value of the key to add
    """
    # Parse the existing XML file
    tree = ET.parse(plist_path)
    root = tree.getroot()

    # Assuming root is a 'plist' element, 'dict' will be the first child
    dict_element = root[0]

    # Now we can add a new key and boolean pair to the dict
    # We'll create a new 'key' element, and then a new 'true' or 'false' element immediately after it

    key_element = ET.SubElement(dict_element, 'key')
    key_element.text = key_name  # The name of your key

    if bool_value:
        ET.SubElement(dict_element, 'true')
    else:
        ET.SubElement(dict_element, 'false')

    # Now the new key/value pair has been added to the XML data in memory
    # We can write the data back out to the Info.plist file
    tree.write(plist_path)

def get_iscc_app_vars(new_version: str, icon_path:str) -> dict[str, str]:
    """ Updates the version in the ISS file which is used to define the build process for the installer on windows

    Args:
        filename: The filename of the .iss filepath
        new_version: The new version we want to update too
        icon_path: The path to the icon file

    Returns: A dictionary of the variables to be used in the .iss file
    """
    return {
        "MyAppVersion" : new_version,
        "MyAppIconPath" : icon_path,
        "MyRepoPath" : get_current_folder(),
    }

def create_windows_installer(iss_file_path: str, iss_vars: dict[str, str]) -> int:
    """ Based on the given .iss file path, we run the inno setup compiler to create the window's installer

    Args:
        iss_file_path: The path to the .iss file to use to create the installer

    Returns: The return code of the inno setup compiler

    """
    # Path to your Inno Setup Compiler - adjust if necessary
    inno_compiler_path = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

    # Create the command
    command = f'"{inno_compiler_path}" "{iss_file_path}" ' + " ".join([f"-D{key}={value}" for key, value in iss_vars.items()])

    # Execute the command
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    # Print output in real time
    while True:
        output = process.stdout.readline()
        if output == b'' and process.poll() is not None:
            break
        if output:
            print(output.strip().decode('utf-8'))

    # Wait for the process to finish and get the return code.
    return_code = process.wait()
    return return_code


def check_python_is_64_bit() -> bool:
    """ Checks the version of python we have installed is 64 bit

    Returns: True if python is 64 bit, False if not

    """
    return sys.maxsize > 2 ** 32


def check_python_version() -> bool:
    """ Checks the version of python we have installed is 3.11

    Returns: True if python is 3.11, False if not

    """
    major_minor_version = '.'.join(platform.python_version().split('.')[:2])
    return '3.11' == major_minor_version


def is_git_installed() -> bool:
    """ Checks if git is installed

    Returns: True if git is installed, False if not

    """
    try:
        # The "stdout" and "stderr" arguments will make subprocess capture the output and error
        # The "shell" argument is set to True to run the command in the shell
        subprocess.check_output("git --version", stderr=subprocess.STDOUT, shell=True)
        return True
    except Exception:
        return False

def is_pkgconfig_installed() -> bool:
    """ Checks if pkg-config is installed on platforms which are not windows

    Returns: True if pkg-config is installed, False if not

    """
    # Check if not running on Windows
    if platform.system() != 'Windows':
        try:
            # Check if pkg-config is available
            subprocess.run(['pkg-config', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except FileNotFoundError:
            return False
    return True


def main() -> int:
    """ The main function which is called when this script is run

    Returns: The return code of the process

    """
    check_dependencies()

    debug = False
    app_name = "OpenVPCal"
    version = get_version_from_python_package()
    icon_file_path = os.path.join(get_python_package_resource_folder(), "icon.ico")
    paths = get_python_package_folder()
    additional_data = get_additional_data_from_resources()
    entry_script = os.path.join(paths, "main.py")
    platform_sep = get_additional_data_seperator()

    additional_python_modules = {
        "spg": os.path.join(get_packages_folder(), "spg", "src", "spg"),
        "stageassets": os.path.join(get_packages_folder(), "stageassets", "src", "stageassets"),
        "spg_icvfxpatterns": os.path.join(get_packages_folder(), "spg_icvfxpatterns", "src", "spg_icvfxpatterns"),
    }

    if debug:
        cmds = ["pyinstaller", "--debug", "all"]

    else:
        cmds = ["pyinstaller"]

    if platform.system() != 'Windows':
        cmds.append("-w")

    cmds.extend(
        ["--icon", icon_file_path, "--name", app_name, "--noconfirm", "--clean", "--onedir", "--paths", paths]
    )

    for folder_name, additional_module in additional_python_modules.items():
        cmds.append("--add-data")
        cmds.append(f"{additional_module}{platform_sep}{folder_name}")

    for add_data in additional_data:
        cmds.append("--add-data")
        cmds.append(add_data)

    cmds.append(entry_script)
    process = subprocess.Popen(cmds, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    print(process.stdout.read())

    # Wait for the process to finish and get the return code.
    return_code = process.wait()
    if platform.system() == 'Darwin':
        certificate_name = os.getenv("CODE_SIGNING_CERTIFICATE", "")
        if certificate_name:
            return_code = osx_sign_app_and_build_dmg(
                app_name, certificate_name, version)
        else:
            print("WARNING - No CODE_SIGNING_CERTIFICATE environment variable set. Skipping code signing.")

    if platform.system() == 'Windows':
        return_code = build_windows_installer([], version, icon_file_path)

    print('Return code:', return_code)
    return return_code


def build_windows_installer(manual_paths, version, icon_path) -> int:
    """ Builds the window's installer and ensures the manual files are copied to the distribution folder

    Args:
        manual_paths: The third party library paths we need to include
        version: The version of the app we are building so we update the installer compilation instructions
        icon_path: The path to icon file

    Returns: The return code of the process

    """
    current_script_directory = get_current_folder()
    for manual_path in manual_paths:
        distribution_folder = os.path.join(current_script_directory, "dist", "OpenVPCal")
        target_file = os.path.join(
            distribution_folder,
            os.path.basename(manual_path)
        )
        shutil.copy(manual_path, target_file)

    iss_file_name = os.path.join(current_script_directory, "OpenVPCal.iss")

    iss_vars = get_iscc_app_vars(version, icon_path)

    return_code = create_windows_installer(
        iss_file_name,
        iss_vars
    )
    return return_code

def remove_ds_store(root_dir):
    for dir_path, dir_names, filenames in os.walk(root_dir):
        if '.DS_Store' in filenames:
            ds_store_path = os.path.join(dir_path, '.DS_Store')
            try:
                os.remove(ds_store_path)
                print(f'Successfully deleted: {ds_store_path}')
            except Exception as e:
                print(f'Failed to delete {ds_store_path}: {e}')

def osx_sign_app_and_build_dmg(app_name: str, certificate_name: str, version: str) -> int:
    """ Signs the app and builds the dmg for osx

    Args:
        app_name: The app name
        certificate_name: The name of the certificate to sign the app
        version: The version number we are releasing

    """
    arch = "universal"
    if platform.processor() == "arm":
        arch = "arm"
    current_script_directory = get_current_folder()
    app_path = os.path.join(current_script_directory, "dist/OpenVPCal.app")
    dmg_path = os.path.join(current_script_directory, f"dist/OpenVPCal-{version}-{arch}.dmg")

    remove_ds_store(app_path)

    # Ensure we pick up the system theme
    pinfo_file_path = os.path.join(app_path, "Contents", "Info.plist")
    add_key_value_to_plist(pinfo_file_path, "NSRequiresAquaSystemAppearance", False)

    # Sign The .App
    # Resign The App As We Changed The pList
    app_path_executable = os.path.join(app_path, "Contents", "MacOS", app_name)
    print("Re Signing The App")

    process = subprocess.Popen(["codesign", "--deep", "--force", "--sign", certificate_name, app_path_executable],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    print(process.stdout.read())
    # Wait for the process to finish
    process.wait()

    print("Creating The DMG")
    process = subprocess.Popen(["hdiutil", "create", "-srcfolder", app_path, dmg_path],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    print(process.stdout.read())
    # Wait for the process to finish and get the return code.
    process.wait()

    # Code Sign The DMG also
    print("Signing The DMG")
    process = subprocess.Popen(["codesign", "--sign", certificate_name, dmg_path],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    print(process.stdout.read())
    # Wait for the process to finish and get the return code.
    return_code = process.wait()
    return return_code


def check_dependencies() -> None:
    """ Checks the dependencies of this script are met before it runs
    """
    if not check_python_is_64_bit():
        raise RuntimeError("Python must be 64 bit")
    if not check_python_version():
        raise RuntimeError("Python must be 3.11")
    if not is_git_installed():
        raise RuntimeError("Git must be installed")
    if not is_pkgconfig_installed():
        raise RuntimeError("pkg-config must be installed")


if __name__ == "__main__":
    main()
