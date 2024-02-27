![OpenVpCal_Full_Logo.png](src%2Fopen_vp_cal%2Fresources%2FOpenVpCal_Full_Logo.png)

# OpenVPCal
The full user guide for OpenVPCal can be found here [UserGuide](https://github.com/Netflix-Skunkworks/OpenVPCal/blob/main/User_Guide_OpenVPCal.pdf).

# Table of Contents
1. [OpenVPCal](#openvpcal)
2. [Installation](#installation)
3. [User Guide](#user-guide)
4. [Developer Guide](#developer-guide)
5. [License](#license)

# Supported Platforms
Windows - :white_check_mark: \
OSX - :white_check_mark: \
Linux - :warning: (Supported But Untested) 

## Installation

### Binaries
For most users the easiest way to install OpenVPCal is to download the latest release from the [Release](https://github.com/Netflix-Skunkworks/OpenVPCal/releases/),
and download the pre built installer for your platform.

### From Source
#### Install Dependencies
Ensure the following dependencies are installed on your system:

    git
    git lfs
    Python-64-bit=3.11.6
    pkg-config
    autoconf
    automake
    autoconf-archive

OpenVPCal provides a system for building the following dependencies using vcpkg, however can be picked up from your existing studio
production or development environment.
    
    OpenImageIO=2.4.11    
    OpenColourIO=2.3.1

The following dependencies to OpenImageIO are critical to be included in its compilation:

    OpenEXR    
    freetype

#### Build From Source    
1. Clone the repository _(Note: Repo uses a large git lfs store, on windows, consider using GIT_LFS_SKIP_SMUDGE=1 to initially clone, and git lfs pull)_
2. Ensure you have the dependencies installed
3. run the "build.bat" or "build.sh" depending on your platform

This may take some time but the build script will perform the following:
1. Remove any existing virtual environments
2. Remove any existing distributions
3. Create a new virtual environment
4. Install the requirements from requirements.txt
5. Install vcpkg, compile and install the dependencies for OIIO
6. Build the executable for OpenVPCal and create the installer for the given platforms

### Developer Setup
Ensure the dependencies are installed and follow the steps below:
1. Add the src folder to the PYTHONPATH environment variable
2. Add the compiled dependencies to the PYTHONPATH with the platform specific replacements: 


    {VCPKG_ROOT}/vcpkg/installed/x64-{PLATFORM}/lib/python3.10/site-packages

3. (Optional) Alternatively if you already have a working environment feel free to use the paths from your existing
environment.

### Why Not PyPi?
OpenVPCal is not currently available on PyPi, this is due to the reliance on OpenImageIO and its many dependencies.
Once/If OpenImageIO is available on PyPi, OpenVPCal can easily be made available on PyPi.

Given there are many different ways studios manage their environments and compile their dependencies we leave this open 
but provide a simple way to build the application from source.

## User Guide
## Developer Guide
## License




