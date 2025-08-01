![OpenVpCal_Full_Logo.png](packages%2Fopen_vp_cal%2Fsrc%2Fopen_vp_cal%2Fresources%2FOpenVpCal_Full_Logo.png)

# OpenVPCal
OpenVPCal is an open-source calibration tool for In-Camera Visual Effects pipelines. 

It is written in Python3, and consists of a number of packages for different levels of integration.

Most end-users will utilize the precompiled application which consists of a PySide UI and CLI, however the source code 
can be used for direct integration into existing software/pipelines, as well as a base to build new applications on top of.

OpenVPCal calibration library creates a series of colour space corrections to be applied to the content-to-LED pipeline, 
which aims to correct the resulting image based on the observer camera in use. 

The calibration can be exported as an OpencolourIO Config and/or "Display-to-Display" 3D LUT.

OpenVpCal was originally introduced at SIGGRAPH 2022, with a [paper](https://history.siggraph.org/learning/open-source-in-camera-visual-effects-calibration-workflow-by-payne-and-giardiello/) and a [presentation](https://dl.acm.org/doi/10.1145/3532836.3536265). 

Please visit the links for more context and background information on this project.

For any questions or issues, please submit issues on the github repository

## Contact Information
For more enquires please contact

[openvpcal@netflix.com](mailto:openvpcal@netflix.com)

The full user guide for OpenVPCal can be found below. 
## Quick Start - Tutorial Video
A quick start tutorial video can be found below

[![Tutorial Video - Quick Start](https://img.youtube.com/vi/ORrTdUGl0JI/0.jpg)](https://www.youtube.com/watch?v=ORrTdUGl0JI)

# Table of Contents

- [OpenVPCal](#openvpcal)
- [Installation](#installation)
  - [Supported Platforms](#supported-platforms)
  - [Binaries](#binaries)
  - [From Source](#from-source)
  - [Developer Setup](#developer-setup)
  - [Why Not PyPi?](#why-not-pypi)
  - [Additional Requirements](#additional-requirements)
  - [Hardware Requirements](#hardware-requirements)
- [Quick Start Guide](#quick-start-guide)
- [User Guide](#user-guide)
  - [Basic Glossary](#basic-glossary)
  - [Create new project/Load existing project](#create-new-projectload-existing-project)
  - [Project Layout](#project-layout)
  - [Add Wall(s)](#add-walls)
  - [Patch Generation](#patch-generation)
  - [Camera / Lens Info](#camera--lens-info)
  - [Shoot](#shoot)
  - [Load and Set Calibration Plates](#load-and-set-calibration-plates)
  - [Analyse](#analyse)
  - [Analysis Validation](#analysis-validation)
  - [Analyse Layout](#analyse-layout)
  - [Calibration Settings Widget](#calibration-settings-widget)
  - [Calibration Matrix widget](#calibration-matrix-widget)
  - [IPT-DeltaE Analysis Widget](#ipt-deltae-analysis-widget)
  - [Calibrate](#calibrate)
  - [Calibration Use Cases](#calibration-use-cases) 
  - [Validation](#validation)
  - [SPG Test patterns](#spg-test-patterns)
- [Developer Guide](#developer-guide)
- [Changelog](#changelog)
- [Acknowledgements](#acknowledgements)

# Installation


## Supported Platforms

Windows - :white_check_mark: \
OSX - :white_check_mark: \
Linux - :warning: (Supported But Untested)


## Binaries
For most users the easiest way to install OpenVPCal is to download the latest release from the [Release](https://github.com/Netflix-Skunkworks/OpenVPCal/releases/),
and download the pre built installer for your platform.

## From Source
#### Install Dependencies
Ensure the following dependencies are installed on your system:

    git
    git lfs
    Python-64-bit=3.11.6
    pkg-config
    autoconf
    automake
    autoconf-archive
    graphviz


#### Build From Source    
1. Clone the repository _(Note: Repo uses a large git lfs store, on windows, consider using GIT_LFS_SKIP_SMUDGE=1 to initially clone, and git lfs pull)_
2. Ensure you have the dependencies installed
3. run the "build.bat" or "build.sh" depending on your platform

This may take some time but the build script will perform the following:
1. Remove any existing virtual environments
2. Remove any existing distributions
3. Create a new virtual environment
4. Install the requirements from requirements.txt
5. Build the executable for OpenVPCal and create the installer for the given platforms

### Developer Setup
    uv venv && uv sync


## Why Not PyPi?
OpenVPCal is not currently available on PyPi, given OpenImageIO is now available via whl and pypi this will now be possible in future


## Additional Requirements


* A generic image processing software to debayer RAW calibration plates and convert them to Linear EXRs (eg Assimilate, Davinci, Baselight, colourfront, Mistika etc.) or camera manufacturers reference software for RED (REDCINEX), ARRI (ART), SONY (RAW VIEWER) that can be used directly from within OpenVPCal, see below for more information.


## Hardware Requirements

* LED Panels (at least 4x4) or a Display
* Image Processor (for LED Panel)
* Media Playback system
* Camera with and a medium-wide lens


# Quick Start Guide

Please use this guide for high-level instructions. For detailed information on the process, see the full User Guide below.


<table>
  <tr>
   <td colspan="2" ><strong><code>SETUP</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>1. CREATE PROJECT</code>
   </td>
   <td>Open OpenVPCal and create a new project, select a new folder where the project files will live.
   </td>
  </tr>
  <tr>
   <td><code>2. SET UP TARGET LED WALL(s)</code>
   </td>
   <td>With “Add LED Wall”, create as many LED walls per camera as you need to calibrate. Use a naming convention that will make sense to recognise each wall correctly. In the “LED Settings” widget, set up the target walls’ settings according to the specs of your LED wall. 
   </td>
  </tr>
  <tr>
   <td><code>3. EXPORT CALIBRATION PATCHES</code>
   </td>
   <td>Export the calibration patches in the format of preference for your media player. You can change the default settings in the “Patch Generation” section, in the “Project Settings” widget. EXR files will be exported <strong>Linear at the Target Colour Space </strong>(e.g. if you selected Rec2020 as the target colour space of the calibration, the EXR will be Linear Rec2020). Any other format will be exported as with the EOTF applied and in Target Colour space (e.g. if you selected ST2084-Rec2020, the patches will be exported like that).
   </td>
  </tr>
  <tr>
   <td><code>4. LOAD PATCHES ON YOUR MEDIA PLAYER</code>
   </td>
   <td>Load the calibration patches on your media player, and <strong>bypass any colour transform</strong>, as the calibration patches are already at the target colour space. If you have exported EXRs, ensure only to apply the required EOTF transform (eg. from Linear Rec 2020 to ST2084-Rec2020, <strong>do not apply transforms that will modify the colour of the charts from the target primaries</strong>. Make sure the patches play correctly, with no frame blending or loop playback. 
   </td>
  </tr>
  <tr>
   <td><code>5. SET UP YOUR CAMERA</code>
   </td>
   <td>Set up the camera in front of the wall, and make sure both the wall and the camera are warmed up and at operating temperature. Switch off any part of the wall that is not in use or any additional light source in the stage.
   </td>
  </tr>
  <tr>
   <td><code>6. SHOOT PATCHES</code>
   </td>
   <td>Follow the instructions on the Start patch (the first patch of the sequence). Shoot more than 1 frame per patch. Check that the camera is well exposed and aligned to the wall. Shoot RAW where possible.
   </td>
  </tr>
  <tr>
   <td colspan="2" >CALIBRATE
   </td>
  </tr>
  <tr>
   <td><code>6. PRE-PROCESS PLATE (OPTIONAL) </code>
   </td>
   <td>OpenVpCal accepts a variety of input files, such as DPX, TIFF, MOV, in conventional camera or display colour spaces, Linear EXR in ACES or conventional camera or display colour spaces, or SONY RAW, ARRIRAW or RED RAW in their respective file formats and colour spaces. If your camera records in a non-supported format, you will be required to pre-process your camera plate to be either Linear/AP0 (ACES 2065-1) or Linear/Camera Native. We recommend Linear/AP0 (default for the tool). The tool accepts custom Input Device Transforms (IDTs) for non-conventional input colour spaces.
   </td>
  </tr>
  <tr>
   <td><code>7. LOAD PLATE FILE ON WALL WIDGET</code>
   </td>
   <td>In OpenVpCal, right-click on the LED WALL and select “Load Plate”. Select the folder where the camera plate is. 
   </td>
  </tr>
  <tr>
   <td><code>8. CHECK ROI and PATCH SEPARATION</code>
   </td>
   <td>OpenVpCal automatically detects the separation between frames and auto detects the ROI in the plate. Check that the ROI is correct and use the frame navigation buttons to check that the frame separation is accurate. 
   </td>
  </tr>
  <tr>
   <td><code>9. PLATE SETTINGS</code>
   </td>
   <td>In the “Plate Settings” widget, set up the “Plate Settings” and select the additional options you might require for your calibration. 
   </td>
  </tr>
  <tr>
   <td><code>10. ANALYSE </code>
   </td>
   <td>Click “Analyse” to allow the tool to perform an accurate analysis of your patches and derive the status of the wall. The tool will suggest whether the wall needs to be calibrated or not and will recommend calibration settings. You can analyse multiple walls at the same time.
   </td>
  </tr>
  <tr>
   <td><code>11. CHECK STATUS AND CALIBRATION SETTINGS</code>
   </td>
   <td>If the analysis is successful, check the patch swatches in the viewer to make sure that every frame is aligned (reference outside, plate inside). Analyse the plotting to determine if the suggested calibration recommendations are in line with your expectations. The colour checker patches might not be visualised if the colour checker detection failed. This is not going to affect the calibration. If the analysis wasn’t successful, reshoot the plates following the suggested corrections. 
   </td>
  </tr>
  <tr>
   <td><code>12. CALIBRATE</code>
   </td>
   <td>When happy to proceed, click “Calibrate”. You can always change the calibration settings and hit “Calibrate” again at any time. You can calibrate multiple walls at the same time.
   </td>
  </tr>
  <tr>
   <td><code>13. CHECK CALIBRATION</code>
   </td>
   <td>Check the results of the calibration by enabling “Preview Calibration” in the viewer. You should see a good improvement!
   </td>
  </tr>
  <tr>
   <td><code>14. EXPORT</code>
   </td>
   <td>If you are happy, export your calibration transforms by hitting the “Export” button. 
   </td>
  </tr>
    <tr>
   <td><code>15. VERIFY</code>
   </td>
   <td>Load the calibration on your media player and shoot the calibration patches again. Run the analysis and check if your LED wall accuracy improved!
   </td>
  </tr>
</table>



# User Guide

This user guide only covers the use of OpenVPCal via the provided UI. A different developer guide is available for implementers who aim to integrate the Python API directly.

We provide a “Sample Project” for you to test the functionalities of the software. 


### Basic Glossary

There are a few terms used in this guide & in the UI which must be understood and correctly set. These colour spaces have different functions within the application: 

* **Reference**: the reference colour space in which every calculation is performed. For now, this is fixed to be ACES 2065-1.
* **Input**: the colour space in which the camera plate is when imported. This defaults to ACES 2065-1.
* **Target**: the target colour space of the calibration
* **Screen**: the colour space of the screen/LED wall intended to be calibrated, as seen by the camera used to shoot the calibration patches
* **Camera Native**: the native colour space of the camera used to capture the plates

#### Create new project/Load existing project

At the start of the application, the user can decide to “Create a New project” or “Load Existing Project”.

If selecting a new project, the user will be prompted to select a folder in which to save the project and its ancillary and export files. 

<img src="docs/source/images/image19.png" alt="image_tooltip" width="20%" height="20%">
<img src="docs/source/images/image35.png" alt="image_tooltip" width="31%" height="20%">

### Project Layout

Once the project is loaded, the application will automatically open the “Project Layout”.


<img src="docs/source/images/image1.png" alt="image_tooltip" width="50%" height="50%">


A series of widgets and buttons are presented to the user:


##### STAGE VIEW


<table>
  <tr>
   <td colspan="2" ><strong><code>LED WALL BIN</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>Add LED WALL </code>
   </td>
   <td>Add a new wall to the LED WALL BIN. A string text editor will pop-up to allow the user to input the LED WALL name
   </td>
  </tr>
  <tr>
   <td><code>REMOVE LED WALL</code>
   </td>
   <td>Remove the selected LED WALL from the LED WALL BIN
   </td>
  </tr>
  <tr>
   <td><code>(contextual menu) Add LED WALL </code>
   </td>
   <td>Same as above
   </td>
  </tr>
  <tr>
   <td><code>(contextual menu) Copy LED WALL </code>
   </td>
   <td>Copy the selected LED wall.  A string text editor will pop-up to allow the user to input the new LED WALL name.
   </td>
  </tr>
  <tr>
   <td><code>(contextual menu) Remove LED WALL </code>
   </td>
   <td>Same as above
   </td>
  </tr>
  <tr>
   <td><code>(contextual menu) Load Plate Sequence</code>
   </td>
   <td>Select from one of the file formats to load and the folder in which the camera plate file resides 
   </td>
  </tr>
  <tr>
   <td><code>(contextual menu) Add Verification Wall</code>
   </td>
   <td>Adds an led wall which is linked to the selected LED wall, allowing a sequence to be loaded after the calibration has been applied to assess the success 
   </td>
  </tr>
</table>


For information on the “Colour Space Analysis CIE Gamut” widget, please see below in the “Analyse”, “Diagnostic Widgets” section.  


##### IMAGE SELECTION

The image selection widget allows a viewer to the user to preview the calibration plate loaded for each wall. This widget allows the ability to select the ROI (Region of Interest) that the software will use to measure the values for each patch. The ROI is marked by a red rectangle that the user can drag and modify as required. Selecting the centre of the ROI, allows it to be positionally dragged into place, whilst drag selecting the corners allows for resizing of the ROI. \
 \
Right-clicking offers a context menu which resets the ROI should you make a mistake.


<img src="docs/source/images/image27.png" alt="image_tooltip" width="50%" height="50%">



##### EXECUTION


<table>
  <tr>
   <td colspan="2" ><strong><code>ANALYSE, CALIBRATE, EXPORT ACTION BUTTONS</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>ANALYSE</code>
   </td>
   <td>This action starts the analysis of the selected LED WALL(s)
   </td>
  </tr>
  <tr>
   <td><code>CALIBRATE</code>
   </td>
   <td>This action starts the calibration of the selected LED WALL(s)
   </td>
  </tr>
  <tr>
   <td><code>EXPORT</code>
   </td>
   <td>This action exports the calibration of the selected LED WALL(s)
   </td>
  </tr>
</table>



##### TIMELINE


<table>
  <tr>
   <td colspan="2" ><strong><code>NAVIGATION</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>START FRAME</code>
   </td>
   <td>The first frame of the loaded plate sequence
   </td>
  </tr>
  <tr>
   <td><code>END FRAME</code>
   </td>
   <td>The last frame of the loaded plate sequence
   </td>
  </tr>
  <tr>
   <td><code>CURRENT FRAME</code>
   </td>
   <td>Current frame where the playhead is located on the plate sequence
   </td>
  </tr>
  <tr>
   <td><code>PLAYHEAD</code>
   </td>
   <td>The playhead to change the current frame
   </td>
  </tr>
  <tr>
   <td><code>GO TO START</code>
   </td>
   <td>A shortcut button to move the playhead to the start of the plate sequence
   </td>
  </tr>
  <tr>
   <td><code>PREVIOUS PATCH</code>
   </td>
   <td>A shortcut to move the playhead to the previous patch in the sequence
   </td>
  </tr>
  <tr>
   <td><code>PREVIOUS FRAME</code>
   </td>
   <td>A shortcut to move the playhead to the previous frame in the sequence
   </td>
  </tr>
  <tr>
   <td><code>NEXT FRAME</code>
   </td>
   <td>A shortcut to move the playhead to the next frame in the sequence
   </td>
  </tr>
  <tr>
   <td><code>NEXT PATCH</code>
   </td>
   <td>A shortcut to move the playhead to the next patch in the sequence
   </td>
  </tr>
  <tr>
   <td><code>GO TO END</code>
   </td>
   <td>A shortcut button to move the playhead to the end of the plate sequence
   </td>
  </tr>
</table>



##### LED SETTINGS


<table>
  <tr>
   <td colspan="2" ><strong><code>TARGET SPECS</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>TARGET GAMUT</code>
   </td>
   <td>The target gamut for the calibration. Choose between predefined standard gamuts (sRGB, P3, Rec2020), or select a custom one that matches the LED wall primaries. 
   </td>
  </tr>
  <tr>
   <td><code>ADD CUSTOM GAMUT</code>
   </td>
   <td>A popup widget allows to add new custom gamut for the calibration by inserting a Custom gamut name and its CIE 1931 x,y primaries and white point coordinates 
   </td>
  </tr>
  <tr>
   <td><code>TARGET EOTF</code>
   </td>
   <td>Select the target EOTF of the LED panel.** Note that when switching between ST2084 to power gamma (sRGB/BT1886), the MaxLum will automatically reset. 
   </td>
  </tr>
  <tr>
   <td><code>TARGET MaxLum (nits)</code>
   </td>
   <td>Select the content peak luminance (only available if the EOTF is ST2084). 
   </td>
  </tr>
  <tr>
   <td><code>(in ADD CUSTOM GAMUT) CUSTOM NAME</code>
   </td>
   <td>Define the name of your custom target colour space.
   </td>
  </tr>
  <tr>
   <td><code>(in ADD CUSTOM GAMUT) TARGET GAMUT CHROMATICITY COORDINATES</code>
   </td>
   <td>Review or modify the xy gamut primaries and the white point coordinates.
   </td>
  </tr>
  <tr>
   <td colspan="2" ><strong><code>TOOL SETTINGS</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>NUMBER OF GREY PATCHES</code>
   </td>
   <td>The number of grey steps to be generated/analysed (default 30)
   </td>
  </tr>
  <tr>
   <td><code>PRIMARIES SATURATION</code>
   </td>
   <td>The saturation intensity for the colour primaries (default 0.7)
   </td>
  </tr>
</table>



##### PLATE SETTINGS


<table>
  <tr>
   <td colspan="2" ><strong><code>PLATE SETTINGS</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>INPUT PLATE GAMUT</code>
   </td>
   <td>The Input colour space of the camera plate sequence (default to ACES 2065-1)
   </td>
  </tr>
  <tr>
   <td><code>NATIVE CAMERA GAMUT</code>
   </td>
   <td>The native linear colour space of the camera used for the calibration
   </td>
  </tr>
  <tr>
   <td><code>AUTO WB SOURCE</code>
   </td>
   <td>If enabled, the input plate will be white-balanced prior to performing the analysis and calibration
   </td>
  </tr>
  <tr>
   <td colspan="2" ><strong><code>REFERENCE SETTINGS</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>MATCH REFERENCE WALL</code>
   </td>
   <td>If checked, the selected LED wall will be matched to the selected reference wall
   </td>
  </tr>
  <tr>
   <td><code>REFERENCE WALL</code>
   </td>
   <td>A list of the available reference walls to match to
   </td>
  </tr>
  <tr>
   <td colspan="2" ><strong><code>USE WHITE POINT OFFSET</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>USE WHITE POINT OFFSET</code>
   </td>
   <td>If checked, the plate's original white point will be shifted towards the measured white point of the indicated file, prior to performing the analysis and the calibration 
   </td>
  </tr>
  <tr>
   <td><code>WHITE POINT OFFSET SOURCE FILE</code>
   </td>
   <td>A path to an image file with the white point offset source
   </td>
  </tr>
</table>



##### PROJECT SETTINGS


<table>
  <tr>
   <td colspan="2" ><strong><code>PROJECT SETTINGS</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>OUTPUT FOLDER</code>
   </td>
   <td>Choose the location on disk to export files and save the project
   </td>
  </tr>
  <tr>
   <td><code>EXPORT LUT FOR ACESCCT In/Out</code>
   </td>
   <td>It modifies the calibration LUT export so that the LUT expects ACEScct input and produces a calibrated ACEScct output. The user will have to apply the colour space conversion and EOTF transform from ACEScct to Target independently  
   </td>
  </tr>
  <tr>
   <td><code>EXPORT LUT FOR ACESCCT IN / TARGET OUT</code>
   </td>
   <td>It modifies the calibration LUT export so that the LUT expects ACEScct input and produces a calibrated target output (with both the colour space and EOTF transform to target applied). 
   </td>
  </tr>
  <tr>
   <td colspan="2" ><strong><code>PATCH GENERATION</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>FILE FORMAT</code>
   </td>
   <td>Choose file format for export. If EXR is chosen, the patches will export in linear (eg Linear Rec 2020), scaled such that 1=100 nits. Otherwise, patches will export in the target space and EOTF (eg ST 2084 - Rec 2020). 
   </td>
  </tr>
  <tr>
   <td><code>RESOLUTION WIDTH</code>
   </td>
   <td>Width resolution of the exported patches
   </td>
  </tr>
  <tr>
   <td><code>RESOLUTION HEIGHT</code>
   </td>
   <td>Height resolution of the exported patches
   </td>
  </tr>
  <tr>
   <td><code>FRAMES PER PATCH</code>
   </td>
   <td>How many frames per patch the tool will export
   </td>
  </tr>
    <tr>
   <td><code>CONTENT MAX LUM</code>
   </td>
   <td>The maximum luminance of the content, which is used to produce three variations of creative rolloff, which gently rolls off the maximum value specified to the peak luminance of the LED wall. We default to 10,000 nits, which is the maximum for PQ. 
   </td>
  </tr>
  <tr>
  <tr>
   <td><code>CUSTOM LOGO</code>
   </td>
   <td>Use a user-defined logo to bake in the patches 
   </td>
  </tr>
</table>



### Add Wall(s)

In this first step, the user is required to add as many walls as required to be calibrated. The concept of a “wall” depends on the use case. Considering that the calibration process is linked to the combination of the physical LED wall and the camera in use (and potentially the lens in use, for certain use cases), users might have multiple walls that all refer to the same physical LED panel type but might aim to calibrate different cameras (eg. a LEDTypeA with Camera A is one wall; LEDTypeA with camera B becomes another wall). Similarly, as the tool offers the ability to perform different calibrations, a “wall” might be a specific calibration process (eg. with or without Gamut Compression enabled). 

The user can add a wall to the LED Wall Bin by clicking on “Add LED Wall”. 



<img src="docs/source/images/image13.png" alt="image_tooltip" width="30%" height="50%">


The user is required to enter a name for the wall. Only alphanumeric characters are allowed.


<img src="docs/source/images/image22.png" alt="image_tooltip" width="20%" height="50%">


Once the wall is created (in this example called “Wall1CamA”), it will appear in the LED Wall bin. 


<img src="docs/source/images/image40.png" alt="image_tooltip" width="25%" height="50%">


At this point, for each wall added, the user is required to define the target parameters. These settings will also influence the calibration patch generation, so make sure to set them correctly before exporting the patches. Select **“Add Custom Gamut”** to define a target colour space such as the LED wall primaries.



<img src="docs/source/images/image16.png" alt="image_tooltip" width="25%" height="50%">


Once a wall is set up, the user can clone it via a contextual menu from the LED wall bin.

This feature is particularly useful when the user is required to calibrate the same wall with different cameras or different calibration pipelines.  


<img src="docs/source/images/image12.png" alt="image_tooltip" width="30%" height="50%">



### Patch Generation

In order to generate the calibration, the user must first export calibration patches that can be played back on the Media Player of preference. Once all walls are created, the user can generate the calibration patches via “File>Generate OpenVpCal Patterns” 

<img src="docs/source/images/image10.png" alt="image_tooltip" width="30%" height="50%">


**The LED Settings in OpenVPCal must be correctly set up before exporting the calibration patches**. 
Most of the colour values of the calibration patches have absolute chromaticity (apart from the Macbeth colour checker chart) but need to be correctly encoded with the invEOTF that will be configured in the LED Wall image processor’s settings (Target Screen EOTF). 
The user can set up the patch file format, resolution and number of frames per patch in the dedicated Patch Generation tab within the Project Settings widget. 

Choose the correct file format and encoding described in the Patch Generation section for the media playback system. For example, if Unreal is used, exporting the patches as linear EXRs might be easier. However, if using a system such as Disguise or Plate Performer, we suggest exporting display-referred patches as DPX files. 



<img src="docs/source/images/image32.png" alt="image_tooltip" width="30%" height="50%">


Once again, please note that if selecting EXR as File Format, **the patch generation will ignore the EOTF and generate linear EXR patches**, scaled so that the value of 1=100nits. These linear EXR are encoded in the Target Colour space, so if you have selected Rec2020, the EXRs will be Linear Rec2020.

When exporting the patches, OpenVPCal will also export a Pre_Calibration_OpenVPCal.ocio config that provides the user with the necessary transforms to apply to the patches. This is fundamental when exporting EXR. 

The OCIO config will have a group of transforms called OpenVPCal, with two subgroups of colour spaces:  \
- INPUT: The pure target colour spaces, in Linear and with the EOTF. These can be used as input colour space when processing the calibration patches. You will find two transforms:
1. A Colour Space + EOTF (eg ST2084 Rec 2020): select this colour space as input colour space for DPX, TIFF, PNG patches
2. A linear Colour Space (eg Linear Rec 2020): select this colour space as input colour space for EXR patches
- UTILITY: A series of utility colour spaces required for the OCIO config to function (e.g. the EOTF curve, the calibration transforms, ...)

<img src="docs/source/images/image28.png" alt="image_tooltip" width="70%" height="50%">


Additionally, the OCIO config will also contain OpenVpCal Display+Views, with a Pre-Calibration Output. This is the output colour space you need to choose for your LED wall to shoot the calibration patches. Once the calibration is completed, OpenVPCal will export a Post-Calibration OCIO, which will add Calibrated Views to the already existing LED Displays.



<img src="docs/source/images/image9.png" alt="image_tooltip" width="70%" height="50%">

#TODO: replace this image with a Rec2020 Linear one
Here’s an example of how the OCIO configuration panel will look with the transforms selected above. 

<img src="docs/source/images/image11.png" alt="image_tooltip" width="100%" height="100%">


In case your Media Playback cannot play each patch for a determined and consistent number of frames, set the “Frames per patch” option, which will export the necessary frames to playback directly at your shooting FPS.

The user can also add a Custom Logo to the generation of the patches that will personalise the first Patch (Home patch) of the calibration sequence. 


### Camera / Lens Info

As OpenVPCal uses the camera as a colourimeter, best practice is to capture the calibration patches with the exact camera that will be used in production. If that is not possible, make sure that the same camera model, running the same firmware as the production camera, is sourced to shoot the calibration. 

The calibration tool will minimise the effect of the lens on the patches. However, a “clean” prime lens with a medium focal length (35-65mm) is recommended.


### Shoot


#### Playback

Use the media playback system of choice for the calibration patch playback, given it meets the following requirements:

1. Is capable of playing back the calibration patches at a consistent FPS
2. Enable transparency & customisation for the colour transform pipeline applied to the images
3. Only the necessary transforms are applied to the patches: the colour of the patches should not be modified, hence only the required EOTF should be applied when using EXR patches, otherwise, the patches should not require any colour transform at all. 
4. Bypass any OS colour management (e.g. Windows ICC profiles) if using a non-standard Media Playback system (that should already bypass OS colour management).


#### Patch Capture

Follow the instructions on the first generated patch, “Home Patch”, to ensure the best possible capture for the calibration process. **Please note that incorrect capture will result in invalid calibration results.** 


<img src="docs/source/images/image39.png" alt="image_tooltip" width="60%" height="50%">



##### Capture Best Practices


###### LED Panels



* Turn off any part of the LED wall that is not directly in front of the camera and is required for the calibration. This is to avoid unnecessary flare.
* Warm up the camera and LED panels: display a flat grey colour on the LED panels for at least 20/40 minutes before capture. It’s good practice to note down the physical temperature of the panel prior to shooting the calibration patches. Most Image Processors should be able to provide this information.   
* Set the LED panels to the maximum gain allowed by the Image processor calibration (do not override the gain).


###### Camera / Lens



* Set the camera as flat as possible to the wall, at a distance where it would be - on average - when shooting on production. Note that the distance from the camera and the wall should be so that the intensity of the light read from the wall into the camera doesn’t change anymore if the distance changes. Use a light meter to define the best distance or the camera’s false colour (see below). 
* Use the first patch to make sure the camera is centred on the wall. The central grey square has a square and a circle inside to help you understand the perspective. 
* Defocus in order to prevent moire. When defocusing, do it towards the camera (closer focus). Imagine that you need to focus on an actor who is sitting in front of the wall. Defocus should be JUST ENOUGH to make sure that the edge lines of the centre square are blurred and blend with the external edge of the centre square. Too little will cause moire, too much might confuse the analysis.

Example Defocus

<img src="docs/source/images/image36b.png" alt="image_tooltip" width="20%" height="50%">

* Record multiple frames for each patch; the suggested amount is 10 for each. When exporting the patches, there is an option to export one frame per patch or multiple frames.
* Set the camera recording mode to RAW (if possible).
* Set the camera at the colour temperature of choice. We suggest setting it to the white point of the LED wall (normally 65000 Kelvin) or Auto white-balance the camera towards the centre target grey square. This choice is important as it will generate different calibrations. For more information about the different use cases, see below in the “Calibration Use Cases'' section.  
* Set the exposure so that the centre square hits 18% of the camera’s sensitivity. Use the camera's false colour tool or a light meter to set the exposure until the whole square is set to 18% (e.g. the box becomes green on an Alexa, Red or Venice).  Use the 17% and 19% small patches at the bottom of the frame to make sure your exposure sits “in the middle”, as false colours can have quite a broad range, relatively speaking. Ideally, use a t-stop that would be used on production. Otherwise, a good range is between T4>T8. ND filters might be required to hit that exposure. Preferably, do not use shutter angle or camera FPS to adjust the exposure (it might create multiplexing issues). Get as close as possible to what will be used during production and/or is required for a correct genlock between the camera and the LED wall. If the distance between the wall and the camera is correct, moving the camera slightly closer or further away from the wall should not generate a drop/increase in the exposure (the false colour should stay consistent). 

<img src="docs/source/images/image36.png" alt="image_tooltip" width="20%" height="50%">

###### Playback/Processor


* If the sequence has only one frame per patch, play it with a frame rate equal to 1/10 of the camera recording's FPS: if the camera records at 25 FPS, set the playback to 2.5 FPS.
* If the exact number of patches is available, the playback speed should be set at the camera FPS. 
* Disable any frame blending and playback loop; the sequence should stop at its last frame.
* Check the video data range (Legal/Full) throughout the pipeline. If a difference can be perceived between the four squares (image below), it is correctly set. Note that when in an ST2084 pipeline, the differences in the black might be slightly less perceivable than the ones in the white squares. Use the SPG Patterns to have a better overview.
* If the difference between squares is imperceptible, check the video pipeline from the media player to the wall (Media Player settings, GPU settings, Image processor settings) and make sure that the video range is set consistently throughout the pipeline. Don’t trust HDMI metadata, force all settings manually if possible.
* Scale the content until the center target grey square covers 60/70% of the vertical camera field of view

<img src="docs/source/images/image31.png" alt="image_tooltip" width="60%" height="50%">


### Load and Set Calibration Plates


#### (OPTION 1) Pre-Process Plate 

Once the patches are captured, you can either decide to pre-process the plate using your DCC of preference, or -if one of the supported formats- load it directly within OpenVpCal (see below, OPTION 2). When pre-processing, we suggest converting the plate to Linear EXR in ACES 2065-1 (AP0) colour space. OpenVpCal does support other input colour spaces, linear and non-linear, but due to the internal processing being all based on the Linear Reference Colour space (which defaults to ACES 2065-1), it's suggested to pre-process directly to that. 
For that reason, the default input for OpenVpCal is Linear ACES AP0 (ACES 2065-1). Make sure to change it if different.


IMPORTANT NOTE: **Plate sequences should follow the naming convention, otherwise it won't be imported.**


_ &lt;FileName>.&lt;FramePadding>.&lt;FileExt>_

Eg calibration_sequence_wall-1.000001.exr

There are several DCCs that can be used for this scope. We are providing here a quick guide for Davinci Resolve.


1. Open Davinci Resolve and set a new project.
2. Go to project settings (the cog on the bottom right of the screen) and set the colour science to ACES (ACES 1.3>, ACEScct, Gamut-Compression disabled). Leave the ACES output transform set to “No Output Transform”. If you shot RAW, you can leave the input transform set as “No Input Transform” as well, or select the required colour space for your camera. If your camera is not on the list and Davinci cannot convert it to ACES automatically, you must source an IDT for your camera that allows you to convert your input colour space to ACES 2065-1. Please defer to the ACADEMY IDT Calculator: https://github.com/ampas/idt-calculator


<img src="docs/source/images/image29.png" alt="image_tooltip" width="60%" height="50%">




3. Load your calibration plate in a new timeline. Do not apply any colour correction or additional transforms to your plate.
4. Go to the delivery menu and, in the Video tab, set up your export as: EXR RGB Half. You can keep the camera's native resolution or reduce it to HD. Make sure that the resizing quality is set to max in the Advanced Settings. 
5. In the File tab, select the Filename as "Source Name". Add a Subfolder with the name of the clip by typing “%Clip Name” in the “File Subfolder” section.



<img src="docs/source/images/image4.png" alt="image_tooltip" width="30%" height="50%">

<img src="docs/source/images/image20.png" alt="image_tooltip" width="38%" height="50%">


6. Render the plate and load the resulting EXR in OpenVpCal. 


#### Load a Pre-Processed or native Plate in OpenVpCal

From the Stage View>Led Wall Bin, you can load the calibration plate associated with the LED wall it was shot for. From OpenVpCal 2.0 we support a larger set of file formats, boh RAW or RGB, both clip-based or frame-based.

<table>
  <tr>
   <td><strong><code>SUPPORTED FILE FORMAT</code></strong>
   </td>
      <td><strong><code>FILE TYPE</code></strong>
   </td>
       </td>
      <td><strong><code>IMAGE TYPE</code></strong>
   </td>
     </td>
       </td>
      <td><strong><code>DEPENDENCY</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>EXR</code>
   </td>
   <td>File sequence
   </td>
    <td>RGB
   </td>
    </td>
    <td>None
   </td>
  </tr>
   <tr>
   <td><code>DPX</code>
   </td>
   <td>File sequence
   </td>
    <td>RGB
   </td>
    </td>
    <td>None
   </td>
  <tr>
   <td><code>TIFF</code>
   </td>
   <td>File sequence
   </td>
    <td>RGB
   </td>
    </td>
    <td>None
   </td>
  </tr>
  <tr>
    <td><code>PNG</code>
   </td>
   <td>File sequence
   </td>
    <td>RGB
   </td>
    </td>
    <td>None
   </td>
  </tr>
  <tr>
    <td><code>MOV</code>
   </td>
   <td>Clip file
   </td>
    <td>RGB
   </td>
    </td>
    <td>FFMPEG
   </td>
  </tr>
  <td><code>MP4</code>
   </td>
   <td>Clip file
   </td>
    <td>RGB
   </td>
    </td>
    <td>FFMPEG
   </td>
  </tr>
   <td><code>ARX</code>
   </td>
   <td>File sequence
   </td>
    <td>RAW
   </td>
    </td>
    <td>ART CMD (Arri Reference Tool)  
   </td>
  </tr>
    </tr>
   <td><code>ARI</code>
   </td>
   <td>File sequence
   </td>
    <td>RAW
   </td>
    </td>
    <td>ART CMD (Arri Reference Tool)  
   </td>
  </tr>
     <td><code>MXF (ARRIRAW)</code>
   </td>
   <td>Clip File
   </td>
    <td>RAW
   </td>
    </td>
    <td>ART CMD (Arri Reference Tool)  
   </td>
  </tr>
       <td><code>MXF (SONY)</code>
   </td>
   <td>File sequence
   </td>
    <td>RAW
   </td>
    </td>
    <td>ART CMD (Arri Reference Tool)  
   </td>
  </tr>
   <td><code>R3D</code>
   </td>
   <td>File sequence
   </td>
    <td>RAW
   </td>
    </td>
    <td>RedCineX 
   </td>
  </tr>  
</table>


To load a plate, select the LED wall, right click on it and select “Load Plate Sequence” or select from File>Load Plate Sequence.

OpenVpCal will automatically ingest the plate and attempt to determine which area of the calibration plate will be utilised for the analysis, the region of interest (ROI), and the separation between each patch (separation). Repeat this process for each LED wall that requires calibration.

<img src="docs/source/images/image37.png" alt="image_tooltip" width="40%" height="50%">


Suppose OpenVPCal fails to determine the correct ROI. In that case, the user must use the first patch centre square as a reference, and align the red ROI shape in the viewer: the reference square has some target crosses on the corners and a centre target. This area should be sufficient for the analysis if the camera was set up correctly. 


#### Load Plate From Raw OCF (Original Camera Footage)
Open VP Cal 2.x supports the ability to extract the input plate directly from the OCF. This utilises third-party applications provided by several of the common camera manufacturers, as well as ffmpeg for decoding conventional file formats such as HEVC or MP4.

This allows the user to skip the process of manually converting the OCF into an EXR, which is often prone to human error, as well as removing an additional step in the process. OpenVPCal will use the supported third-party application to pre-render the OCF into either ACES2065-1 EXR or Camera Native DPX files. The renders will be placed in a RENDER project subfolder and automatically loaded upon finish.  

#### OCF Prerequisites
Depending on your camera, you will need to install the manufacturer's relevant utility.

#### RED
Support for Reds .R3D format is provided via the REDCINE-X PRO application, which can be downloaded from the RED website.
https://www.red.com/downloads

#### SONY
Support for Sony's .mxf format is provided via the Sony RAW Viewer, which can be downloaded from the Sony website.
https://www.sony.com/electronics/support/software/00339639

#### ARRI
Support for ARRIs .ari, .arx and .mxf formats is provided via the ART-CMD application, which can be downloaded from the ARRI website.
https://www.arri.com/en/learn-help/learn-help-camera-system/tools/arri-reference-tool

NOTE: Ensure is the CMD application, not the GUI Application
NOTE: The ART CMD should be placed by default in C:/ARRI or ~/ARRI on macOS/Linux.
NOTE: The art-cmd needs to be on the $PATH variable or directly configured in the pre_process_config (see below for more info). 

#### FFMpeg
Support for .mov, .mp4 files for cameras which record only RGB using a .mov or .mp4 container
https://ffmpeg.org/download.html

#### Pre-Process Config
For applications which do not come with a native installer or for applications which are installed into non-default locations, the user needs to ensure that the executable is either on the $PATH or set into the pre_process_config.

This can be found in the OpenVPCal Prefs folder, which can be opened via the UI.

File > Open Prefs In Folder Viewer

<img src="docs/source/images/user_prefs.png" alt="image_tooltip" width="40%" height="50%">
<img src="docs/source/images/user_prefs2.png" alt="image_tooltip" width="40%" height="50%">


As an example for the ARRI, art-cmd, this can be installed elsewhere on the system. OpenVPCal will default to the $PATH variable first and fall back to the "command_path_overrides" for each platform
``` json
                "commandName": "art-cmd",
                "command_path_overrides": {
                    "darwin": "~/Downloads/art-cmd_0.3.0_macos_universal/bin/art-cmd",
                    "win32": "C:\\ARRI\\bin\\art-cmd.exe",
                    "linux": "~/Downloads/art-cmd_0.3.0_macos_universal/bin/art-cmd"
                },
```

#### Loading OCF
From the menu, rather than select the "RGB_Sequence", select the relevant importer for your camera format.

<img src="docs/source/images/ocf_import.png" alt="image_tooltip" width="40%" height="50%">

From the file dialogue, select your OCF file or folder.
OpenVPCal will now call the commands to the installed and configured third-party applications and convert the footage into an image sequence in the correct format, either EXRs in ACES or DPX files in native camera gamut.
After the footage has been extracted, it is loaded into OpenVPCal as if you had selected the pre-converted image sequence.

Where the OCF format is known, the Input Plate Gamut will be set to the correct colour space, however, please double-check this is correct before proceeding.
Especially in the case of ffmpeg, where metadatas usually default to Rec709, even when the files are encoded as native camera colour spaces.


#### Plate Settings

From the Plate Settings tab, you must set the colour space of the pre-processed plate file (default to ACES 2065-1), as well as the native colour space of the camera used to capture the plate. 

If your workflow requires to auto-wb the plate and you cannot perform this operation in camera, or you require a more accurate white balance, select Auto WB source.

Please refer to the “Common Use-cases” section to learn more about the different types of calibration workflows. 


<table>
  <tr>
   <td colspan="2" ><strong><code>PLATE SETTINGS</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>INPUT PLATE GAMUT</code>
   </td>
   <td>The Input colour space of the pre-processed camera plate sequence (default to ACES 2065-1)
   </td>
  </tr>
  <tr>
   <td><code>NATIVE CAMERA GAMUT</code>
   </td>
   <td>The native colour space of the camera used for the calibration
   </td>
  </tr>
  <tr>
   <td><code>AUTO WB SOURCE</code>
   </td>
   <td>If enabled, the input plate will be white-balanced prior to performing the analysis and calibration
   </td>
  </tr>
</table>



### Analyse

Once the plates are loaded and set up for each LED wall that you intend to analyse and calibrate, you can hit Analyse in the Execution tab.

The analysis will extract the necessary information from the plate and switch the software configuration to the “Analysis layout”. You can select multiple walls at the same time and run the analysis simultaneously. \
 \
NOTE: Any walls which are using another wall as a reference must be analysed and calibrated at the same time


### Analysis Validation

Once the analysis is completed, the tool will prompt a pop-up window with a description of the results for each wall analysed. The analysis might issue some critical errors, warnings or a suggestion that the wall doesn’t require any calibration because it’s within a good tolerance. 


### Analyse Layout


#### Swatch Analysis

In the Analysis Layout, a Swatch Analysis viewer will appear to facilitate the user's appreciation of the status of the wall and its calibration. The viewer is run by Opencolour IO (OCIO) and therefore can map the swatches to any colour space available from the default OCIO config shipped with the tool, the ACES 1.3 Studio Config.  

The viewer plots each patch of the calibration sequence as a square swatch, in which the outer part shows the target colour and the inner part shows the actual patch observed by the camera.  

<img src="docs/source/images/image21.png" alt="image_tooltip" width="20%" height="50%">


The widget offers a series of tools:


<table>
  <tr>
   <td colspan="2" ><strong><code>SWATCH ANALYSIS VIEWER </code></strong>
   </td>
  </tr>
  <tr>
   <td><code>Exposure</code>
   </td>
   <td>A slider to change the exposure level of the swatches
   </td>
  </tr>
  <tr>
   <td><code>Display</code>
   </td>
   <td>A dropdown menu with all available OCIO Displays
   </td>
  </tr>
  <tr>
   <td><code>View</code>
   </td>
   <td>A dropdown menu with all the available OCIO Views for the selected Display 
   </td>
  </tr>
  <tr>
   <td><code>Apply White Balance Preview</code>
   </td>
   <td>Applies a preview of the Auto-WB and or White Balance Offset, if present
   </td>
  </tr>
  <tr>
   <td><code>Preview Calibration</code>
   </td>
   <td>The potential outcome of the calibration, digitally applied to the swatches to emulate what the results might be once the calibration is applied to the LED wall. Be mindful that this is just a simulation, and the results might differ. 
   </td>
  </tr>
</table>




<img src="docs/source/images/image2.png" alt="image_tooltip" width="80%" height="50%">



#### Diagnostic widgets

A series of diagnostic widgets are presented to the user to help determine the status of the LED wall and its calibration. 


##### Max Distance Analysis

This widget shows the extent of the out-of-gamut colours measured in relation to the target colour space of the calibration.


<img src="docs/source/images/image6.png" alt="image_tooltip" width="50%" height="50%">
 


<table>
  <tr>
   <td colspan="2" ><strong><code>MAX DISTANCE ANALYSIS</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>Pre-Cal</code>
   </td>
   <td>The results of the analysis, as measured directly from the calibration plate
   </td>
  </tr>
  <tr>
   <td><code>Post-Cal</code>
   </td>
   <td>The potential outcome of the calibration, digitally applied to the calibration plate to emulate what the results might be once the calibration is applied to the LED wall. Be mindful that this is just a simulation, and the actual results might be different. 
   </td>
  </tr>
</table>



##### EOTF Analysis

This widget tracks the linear response of the LED wall.


<img src="docs/source/images/image26.png" alt="image_tooltip" width="50%" height="50%">



<table>
  <tr>
   <td colspan="2" ><strong><code>EOTF ANALYSIS</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>Pre-Cal</code>
   </td>
   <td>The results of the analysis, as measured directly from the calibration plate
   </td>
  </tr>
  <tr>
   <td><code>Post-Cal</code>
   </td>
   <td>The potential outcome of the calibration, digitally applied to the calibration plate to emulate what the results might be once the calibration is applied to the LED wall. Be mindful that this is just a simulation, and the actual results might be different. 
   </td>
  </tr>
  <tr>
   <td><code>Red</code>
   </td>
   <td>Shows the Red channel data only
   </td>
  </tr>
  <tr>
   <td><code>Green</code>
   </td>
   <td>Shows the Green channel data only
   </td>
  </tr>
  <tr>
   <td><code>Blue</code>
   </td>
   <td>Shows the Blue channel data only
   </td>
  </tr>
</table>



##### White Point Analysis

This widget shows the observed white point of the LED wall, as seen by the camera. 


<img src="docs/source/images/image8.png" alt="image_tooltip" width="50%" height="50%">



<table>
  <tr>
   <td colspan="2" ><strong><code>WHITE POINT ANALYSIS</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>Target</code>
   </td>
   <td>Shows the ideal target of the calibration
   </td>
  </tr>
  <tr>
   <td><code>Pre-Cal</code>
   </td>
   <td>The results of the analysis, as measured directly from the calibration plate
   </td>
  </tr>
  <tr>
   <td><code>Post-Cal</code>
   </td>
   <td>The potential outcome of the calibration, digitally applied to the calibration plate to emulate what the results might be once the calibration is applied to the LED wall. Be mindful that this is just a simulation, and the actual results might be different. 
   </td>
  </tr>
  <tr>
   <td><code>Macbeth</code>
   </td>
   <td>Adds to the plotting the Macbeth samples
   </td>
  </tr>
</table>



##### Colour Space Analysis

This widget shows the observed extent of the colour space and white point of the LED wall, as seen by the camera.

<img src="docs/source/images/image24.png" alt="image_tooltip" width="50%" height="50%">

<table>
  <tr>
   <td colspan="2" ><strong><code>COLOUR SPACE ANALYSIS</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>Target</code>
   </td>
   <td>Shows the ideal target of the calibration
   </td>
  </tr>
  <tr>
   <td><code>Pre-Cal</code>
   </td>
   <td>The results of the analysis, as measured directly from the calibration plate
   </td>
  </tr>
  <tr>
   <td><code>Post-Cal</code>
   </td>
   <td>The potential outcome of the calibration, digitally applied to the calibration plate to emulate what the results might be once the calibration is applied to the LED wall. Be mindful that this is just a simulation, and the results might differ. 
   </td>
  </tr>
  <tr>
   <td><code>Macbeth</code>
   </td>
   <td>Adds to the plotting the Macbeth samples
   </td>
  </tr>
</table>


### Calibration Settings Widget

The calibration settings offer a series of options that allow different calibration paths and functions. The analysis process should have already setup these parameters with the optimal ones required for your LED wall, but the user is free to choose what to enable/disable or what path to use. See the Calibration section for more information. 


<table>
  <tr>
   <td colspan="2" ><strong><code>CALIBRATION SETTINGS</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>REFERENCE TO TARGET CAT</code>
   </td>
   <td>Choose from a standard list of Chromatic Adaptation Transforms or select NONE for the Reference to Target 3x3 matrix. Bradford is set as the default
   </td>
  </tr>
  <tr>
   <td><code>CALCULATIONS ORDER</code>
   </td>
   <td>Edit the order of operations for the calibration transforms
   </td>
  </tr>
  <tr>
   <td><code>ENABLE EOTF CORRECTION</code>
   </td>
   <td>If checked, enable the EOTF correction
   </td>
  </tr>
  <tr>
   <td><code>TARGET TO SCREEN CAT</code>
   </td>
   <td>Choose from a standard list of Chromatic Adaptation Transforms or select NONE for the Calibration matrix. None is set as default.
   </td>
  </tr>
  <tr>
   <td><code>ENABLE GAMUT COMPRESSION</code>
   </td>
   <td>If checked, enable gamut compression
   </td>
  </tr>
  <tr>
   <td><code>AVOID CLIPPING</code>
   </td>
   <td>If checked, it scales the entire calibration transforms to avoid highlight clippings (on by default)
   </td>
  </tr>
</table>


## Calibration Matrix widget

Once the calibration is completed, this widget offers the option to copy each 3x3 matrix used in the calibration transforms in several practical formats. 

Available 3x3 Matrix:



* Target to Screen
* White Balance
* Reference to Target
* Reference to Screen
* Reference to Input
* Reference to XYZ
* E to D65

Available formats:



* Python
* Nuke
* CSV

<table>
  <tr>
   <td colspan="2" >
<strong><code>CALIBRATION MATRIX</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>Matrix Dropdown</code>
   </td>
   <td>A list of the available matrices
   </td>
  </tr>
  <tr>
   <td><code>Format Option</code>
   </td>
   <td>A list of the available formats
   </td>
  </tr>
</table>


## IPT-DeltaE Analysis Widget

OpenVpCal tries to determine the status of the LED wall by using DeltaE IPT measurements, among other factors. This widget shows the measured IPT DeltaE between the reference target colour and the one observed by the camera. It’s separated into groups of patches and offers the ability to select and compare multiple walls, estimating the “best wall” based on the average of deltaE measurements that fall under the just noticeable difference (JND) threshold. This feature is handy when comparing different calibration approaches or verifying a calibration's success against the wall's original status. 

<img src="docs/source/images/image5.png" alt="image_tooltip" width="50%" height="50%">

## Calibrate

The calibration setup has multiple settings that determine how OpenVPCal will attempt to calibrate the LED wall(s). Here’s a more detailed description of what each does:


#### CALCULATION ORDER and EOTF CORRECTION

A specific note is required to clarify the Calculations order, which determines how OpenVpCal calculates the main elements of the calibration, the EOTF correction and the Target to Screen 3x3 Matrix. This choice is then reflected in the calibration files (OCIO or 3D LUTs)

. These options present three different paths: 

* EOTF CORRECTION DISABLED, the calibration will only be performed by a 3x3 matrix applied straight to the incoming RGB data converted to the Target colour space. This approach assumes that the LED wall behaves linearly.
* 1D → 3x3, where the calibration process assumes that the LED wall doesn’t behave linearly. In this path, the non-linearity is assumed to happen at the end of the image processing chain (before the EOTF but after any colour mapping within the LED chain). Hence, the EOTF correction and RGB balancing are measured before the 3x3 calibration matrix
* 3x3 → 1D, where again, the calibration process assumes that the LED wall doesn’t behave linearly; however, in this case, the non-linearity is assumed to happen at the beginning of the image processing chain (before or during the pipeline colour mapping, before the EOTF). Therefore, the EOTF correction and RGB balancing are measured after the 3x3 calibration matrix.

Which one is the correct one? It depends: different pipelines might have different issues; however, when the analysis process determines that the wall is not linear, the OpenVPCal default is the **<span style="text-decoration:underline;">1D>3x3</span>** order.


##### CHROMATIC ADAPTATION TRANSFORM (CAT)

Chromatic Adaptation Transforms are designed to maintain the appearance of colours under different lighting conditions or white points. In order to assure the best possible calibration, OpenVPCal goes through a number of different conversions between colour spaces and white points, which means a number of CAT transforms are applied forward and inverted within each block of the calibration transforms. Because mixing CAT within a set of transformations is bad practice, we provide the user only two places where to select different CATs, as these transform blocks are essentially independent of each other. Selecting NONE will bypass any Chromatic adaptation and will therefore modify the appearance of colours and white points when changing colour space.  Depending on your workflow, different CATs may be appropriate. The OpenVPCal defaults are:


<table>
  <tr>
   <td><code>REFERENCE TO TARGET CAT</code>
   </td>
   <td>BRADFORD
   </td>
   <td>As we use ACES in OCIO as the default colour framework, Bradford is the default CAT used for their output transforms, hence we adopted it as our default as well to map ACES to the target LED wall. 
   </td>
  </tr>
  <tr>
   <td><code>TARGET TO SCREEN CAT</code>
   </td>
   <td>NONE
   </td>
   <td>Because the ordinary scope of this transform is to alter the source  white point of the plate  to match the target of the calibration, the default is set to NONE.
   </td>
  </tr>
</table>



#### AVOID CLIPPING

The calibration might push one or two RGB channels above the intended peak luminance. When targeting ST2084 EOTF, if any of the channels go above then the display will clamp it, affecting the white point of the LED wall. Avoid clipping will push the channels to go below the peak luminance. It might affect the overall brightness of the wall, but it should be quite subtle, nevertheless.


### Calibration Use Cases

OpenVpCal offers a number of different options to calibrate an LED wall, based on different needs. The user can choose different paths within the calibration settings, but also perform things slightly differently according to the use case. Here’s a list of the most common ones:


##### SIMPLE CALIBRATION: Targeting A Specific White Point

This is the most common calibration use case, where the camera is set to a specific white balance setting. The calibration shifts the LED wall to ensure that the emitted white of the wall will result in white in camera with that specific camera setting. A good use case for this is to aim at the LED wall’s native white point (eg 6500K), or when the Cinematographer requires to shoot at a specific white balance and wants the wall to appear white with these parameters. 

For simplicity, we suggest setting the camera at the wall’s native white point so the calibration does not have to bake a huge white point shift. Instead, we recommend modifying the content’s colour temperature in the media player to look pleasing in the camera, leaving the camera and the calibration at the wall’s native white point. 


<table>
  <tr>
   <td colspan="2" ><strong><code>SIMPLE CALIBRATION</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>Use case</code>
   </td>
   <td>Aim the calibration to the camera’s specific white point
   </td>
  </tr>
  <tr>
   <td><code>Pros</code>
   </td>
   <td>Simple, moves the content’s colour temperature problem to the media player
   </td>
  </tr>
  <tr>
   <td><code>Cons</code>
   </td>
   <td>The effect of the lens on the calibration is baked into the calibration, so it might be required to run different calibrations for different lenses
   </td>
  </tr>
</table>


<img src="docs/source/images/image38.png" alt="image_tooltip" width="50%" height="50%">



##### AUTO WHITE BALANCE CALIBRATION: A shortcut to remove the lens effect

In this use case, we ask to perform an auto white-balance in the camera on the first patch of the calibration sequence, prior to shoot the plate (or to the plate, if the camera does not allow to auto-white balance, using the AUTO-WB option in the PLATE SETTINGS widget, when loading the calibration plate). The calibration will not change the white point of the wall. It will only adjust the colour mapping, the EOTF balancing (if enabled) and the out-of-gamut colours (if enabled). This calibration is less subject to potential colour shifts created by the lenses used to shoot, but it will not address the camera’s metameric failure of the white point, forcing the cinematographer to shoot at a specific white point setting (suggested by the auto-white balance in camera) or always to adjust the in-camera white point to obtain the intended result.


<table>
  <tr>
   <td colspan="2" ><strong><code>AUTO WB CALIBRATION</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>Use case</code>
   </td>
   <td>The calibration won’t shift the WALL white point, only corrects colour and EOTF
   </td>
  </tr>
  <tr>
   <td><code>Pros</code>
   </td>
   <td>Simple, more solid with lens colour shifts
   </td>
  </tr>
  <tr>
   <td><code>Cons</code>
   </td>
   <td>The effect of the lens on the calibration is bypassed by the white balance, but the metameric failure of the camera against the wall isn’t fixed as the auto-white-balance fixes that too. 
   </td>
  </tr>
</table>



<img src="docs/source/images/image25.png" alt="image_tooltip" width="60%" height="50%">



##### MATCH WALL CALIBRATION: Shooting the calibration to make multiple walls match

When your stage has multiple LED wall types (brands/models) and you want to match them in camera, this workflow allows you to select a “reference wall” that is used as main target for the calibration. By enabling “Match Reference Wall” and selecting from the dropdown menu one of the other walls from the Stage View Bin, OpenVpCal will make sure that the wall you are calibrating will match the Reference one when keeping the camera at the same white balance. The Reference wall can follow any of the other workflows (Simple, Auto-WB and White Point offset), and these shifts will be handed along to the matching wall(s). 

<img src="docs/source/images/image7.png" alt="image_tooltip" width="60%" height="50%">



##### WHITE POINT OFFSET CALIBRATION: Decoupling lenses or shifting to external white points

Like the auto-wb option, this option allows for correcting the plate prior to being passed to the analysis. 

However, in this case, the calibration plate is white balanced towards a different white point, instead of the target white point. There are different use cases for this workflow, but it has mostly been designed to decouple the effect of the lens or filters used to shoot the calibration plate. When enabling this option, OpenVpCal requires the user to select a frame from which it will calculate the white balance matrix to apply to the calibration patches. When aiming to decouple the effect of the lens, we perform the workflow in these simple steps:



1. Shoot the calibration patches as per **<code>SIMPLE CALIBRATION</code></strong> workflow, setting the camera to the LED wall white point. Once finished shooting, roll back the sequence to the first frame, where the grey square and circle are;
2. Remove the lens from the camera, don’t change anything else;
3. The incoming light from the LED wall to the sensor will be bright without a lens, so change the shutter speed and/or fps of the camera to make sure that the blurred image doesn’t clip. Ideally, it should be exposed correctly (using the false colour of the camera, it should get to the 18% level). 
4. Shoot just a second (a single frame is necessary) of the first patch of the calibration sequence only. You don’t need to run the entire sequence. 
5. Use one frame of the clip shot without a lens as White Point Offset Source File

<table>
  <tr>
   <td colspan="2" >
<strong><code>WHITE BALANCE OFFSET CALIBRATION CALIBRATION</code></strong>
   </td>
  </tr>
  <tr>
   <td><code>Use case</code>
   </td>
   <td>The calibration aims at a specific white point, removing the effect of the lens 
   </td>
  </tr>
  <tr>
   <td><code>Pros</code>
   </td>
   <td>More advanced, solves multiple challenges at once, it does not depend on the lens used
   </td>
  </tr>
  <tr>
   <td><code>Cons</code>
   </td>
   <td>It requires shooting additional plates without the lens, and it's prone to more errors
   </td>
  </tr>
</table>


<img src="docs/source/images/image18.png" alt="image_tooltip" width="60%" height="50%">


Once applied, the grey patches on the right hand of the viewer will show the before and after the white point offset calibration. 


#### EXPORT CALIBRATION

The calibration is complete! The final step is to export the transforms. OpenVPCal uses OCIO as the primary format for the export. Clicking on the EXPORT button prompts the user whether to use the default OCIO config or one they provide.

<img src="docs/source/images/image3.png" alt="image_tooltip" width="20%" height="50%">


The OCIO config file will be saved in the calibration folder within the exports folder of the project. Named Post_Calibration_OpenVPCal.ocio, and contains the calibration transforms as new Displays and Views. The OCIO config will embed transforms for each LED wall if multiple walls were calibrated. 

As per the Pre-Calibration config, the OCIO config exported from the calibration will offer colour spaces under the OpenVpCal group. You can now choose the calibrated LED wall in the Display colour spaces under this naming convention: 

OpenVPCal [WALL_NAME] - [CAMERA NATIVE GAMUT]

Example: OpenVPCal ROE - REDWideGamutRGB

The 3D LUT exported by OpenVPCal is normally a display-to-display LUT. However, in the project settings widget, the user can select to export the LUT in a different format as an ACEScct in/out or ACEScct in and Display Target Out.


<img src="docs/source/images/image30.png" alt="image_tooltip" width="60%" height="50%">



### Validation

Once the calibration is completed and exported, we suggest validating it by re-shooting the original plate on the wall with the calibration transforms applied. OpenVpCal offers the ability to “Add Validation Wall”, which allows the user to compare the status of the wall prior to and post calibration.

Once the verification wall plates are loaded, run the Analysis. OpenVpCal will essentially consider the verification wall as a slave wall of its source; hence, it will copy all the target settings and show it as an additional wall in the Stage View bin. 



<img src="docs/source/images/image17.png" alt="image_tooltip" width="60%" height="50%">


If successful, the analysis of the validation wall should report that the verification wall needs no calibration, and the IPT DeltaE analysis should show primarily green/yellow colours and better JND values than the source wall before its calibration.



<img src="docs/source/images/image14.png" alt="image_tooltip" width="30%" height="50%"> <br>

<img src="docs/source/images/image5.png" alt="image_tooltip" width="60%" height="50%">

### Content Max Lum & Rolloffs
LED Walls are only capable of displaying a given range of brightness, as defined by their peak luminance.
Often, content has values which go beyond this range, which can produce harsh clips in the footage.

A number of Media Servers offer grading controls to apply a creatively controllable roll-off to maintain the linearity of the content on the LED wall while gently rolling the highlights above a certain level to within the capabilities of the LED wall.
For systems which do not provide this functionality, OpenVPCal outputs additional calibration displays within the OCIO config, which can be used to apply a soft, medium and hard roll off of the content, whilst still applying the calibration.

By default, the Content Max Lum is set to 10,000 nits, which is the maximum which can be encoded into PQ (ST2084).  
This tells OpenVPCal to roll off values from 10k nits to the peak lum of the LED wall.

Given that your content may not reach 10k nits, you can set this to a sensible value for the maximum brightness of your content

For instance, if the user were to set 5000 nits, a value in the content would be rolled off to the peak_lum rather than be clipped.

Within the OCIO config, you will see 3 options per wall similarly named as

``` json

  Calibrated ROE_CSonly - ROE - REDWideGamutRGB - CS_EOTF - Soft_Rolloff_s1155-10000_to_1650_nits
  Calibrated ROE_CSonly - ROE - REDWideGamutRGB - CS_EOTF - Medium_Rolloff_s1320-10000_to_1650_nits
  Calibrated ROE_CSonly - ROE - REDWideGamutRGB - CS_EOTF - Hard_Rolloff_s1485-10000_to_1650_nits

```
  


### SPG Test patterns

OpenVpCal is shipped with a version of the synthetic pattern generator for ICVFX tool (SPG). 
From File>Generate SPG Patterns, the images are generated in the same colour space and EOTF as the LED wall.

<img src="docs/source/images/image10.png" alt="image_tooltip" width="40%" height="50%">

The user can export a series of reference images that can be used to verify and debug 
the image chain from the media player to the LED wall, and use this prior to running a calibration to ensure that the 
whole chain is correct and performing as expected.

These patterns should be judged via the camera output primarily however, some patterns exhibit problems to the naked eye.

The default sequence will contain the following patterns:


### **SPG - Frame Sync Count** 

When filmed through the camera lens, should display whole numbers on each frame of the recording
if any ghosting/blending of numbers is present there is a sync or playback issue. If there are numbers missing then similarly there is a mismatch. 
It is important to check all walls especially when driven via multiple processors as some sections of the wall
may be in sync while other sections may not.

**Expected Frame Example**

<img src="docs/source/images/spg/spg.000001.png" alt="image_tooltip" width="50%" height="50%">

**Frame Rate/Sync Issue - Ghosting/Blending**

<img src="docs/source/images/spg/frame_count_sync_issue_1.png" alt="image_tooltip" width="50%" height="50%">

**Frame Rate/Sync Issue - Partial Wall Issue**

<img src="docs/source/images/spg/frame_count_sync_issue_2.png" alt="image_tooltip" width="50%" height="50%">

### **SPG - Checkerboard**
A simple set of checkerboard patterns at different sizes to check for any scaling or aspect ratio issues.
When mapped 1:1 with the led wall the squares should un distorted.

<img src="docs/source/images/spg/spg.000048.png" alt="image_tooltip" width="50%" height="50%">
<img src="docs/source/images/spg/spg.000049.png" alt="image_tooltip" width="50%" height="50%">
<img src="docs/source/images/spg/spg.000050.png" alt="image_tooltip" width="50%" height="50%">


### **SPG - Linear Steps**
A series of linear steps in absolute brightness (nits), when working in PQ (ST2084). 
There should be clearly visible bands up to the peak luminance of the wall, and no further 
visible bands beyond the walls peak.
Patches are generated in bands of 100 nits with a 1000 nit range per image, eg 0-1000, 1000-2000, 2000-3000 etc
These cover the whole range of 0 to 10,000 nits, the entire range of PQ (ST2084).
There is an additional more granular set of steps from 1500 nits to 2000 nits in 50 nit increments to identify closer the more common range of peak values for in camera walls.
With correctly calibrated led wall, a light meter should read the same value as the nits depicted on the band.

If there are more or less bands either above or below the peak of the wall there is a configuration issue with the imaging chain

**Expected Frame Example @ 1000 nits**

<img src="docs/source/images/spg/spg.000052.png" alt="image_tooltip" width="50%" height="50%">

**Correctly Displaying Bands To Example @ 1650 nits**

<img src="docs/source/images/spg/Clipping1650.png" alt="image_tooltip" width="50%" height="50%">

**Incorrectly Displaying No Bands Should Go To 1650 nits**

<img src="docs/source/images/spg/Clipping_Wrong.png" alt="image_tooltip" width="50%" height="50%">


### **SPG - Exposure Stops**

A series of exposure stops, when displayed on the calibrated wall, by exposing the camera using the false colour of the 
camera, moving up and down a stop of exposure either of the content of the media server or via the camera itself, will highlight each exposure stop on the wall confirming a linear lighting response
between the camera and the wall.


<img src="docs/source/images/spg/spg.000061.png" alt="image_tooltip" width="50%" height="50%">

**False Colour Check + 1 Stop**

<img src="docs/source/images/spg/exposure_1Stops.png" alt="image_tooltip" width="50%" height="50%">

**False Colour Check + 2 Stops**

<img src="docs/source/images/spg/exposure_2Stops.png" alt="image_tooltip" width="50%" height="50%">

**False Colour Check + 3 Stops**

<img src="docs/source/images/spg/exposure_3Stops.png" alt="image_tooltip" width="50%" height="50%">


### **SPG - Data Range (legal/extended)**

Ensures that the imaging chain is in extended (full) range and not being limited by a legal range. 
When viewed on the led wall the inner squares should be visible (note the black inner should be very feint look closely! )

<img src="docs/source/images/spg/spg.000062.png" alt="image_tooltip" width="50%" height="50%">

### **SPG - Bit Depth**
A grey ramp moving from left to right, denoting every code value from 0-1023 in 10 bit, 
any vertical banding indicates the imaging chain is not 10 bit.

**Expected Frame**

<img src="docs/source/images/spg/spg.000063.png" alt="image_tooltip" width="50%" height="50%">

**Imaging Chain 8 Bit Vertical Bands**

<img src="docs/source/images/spg/8_bit.png" alt="image_tooltip" width="50%" height="50%">

**Same Image 10 Bit No Vertical Bands**

<img src="docs/source/images/spg/10_bit.png" alt="image_tooltip" width="50%" height="50%">


### **SPG - colour Steps**
A series of colour steps to indicate any colour clipping issues, similar to the Linear Steps 
there should be nice even steps with no black bands or indistinguishable bands. 
This occurs when calibrated correctly to use the custom achievable primaries of the led wall.

**Expected Frame - Identifiable Steps No Black Clips**

<img src="docs/source/images/spg/spg.000064.png" alt="image_tooltip" width="50%" height="50%">


### **SPG - Real Black Level**
LEDs to not brighter and dimmer leds simply turn on and off faster and slower, as the wall gets darker leds turn off
for longer and longer until they become off. At some point the leds are off for long enough to become visible in camera, regardless
of sync. This is the true real black level of the LED panel, the darkest it can go before this multiplexing issue becomes visible in camera.
This patch displays the bottom 18% of code values displayable on the LED panel, this helps determine where
the minimal black level the LED panels are capable of before multiplexing issues are introduced to the camera.


Tilting the camera up and down on this patch will show multiplexing issues at some point, likely close to the top of the wall, where the patch is driving
the leds at their slowest rate, is where we will see this issue.

The lower the black level of the panels, the higher up the patch the multiplexing will appear.

<img src="docs/source/images/spg/spg.000065.png" alt="image_tooltip" width="50%" height="50%">

**Example Minimal Black Level - Multiplexing starting before we hit actual black**

<img src="docs/source/images/spg/real_black_issue_2.png" alt="image_tooltip" width="50%" height="50%">


### **SPG - Alignment**
A series of grids and cross patterns helpful to ensures there are no mis alignments in physical 
construction or mapping of content to the led wall.

**Example Alignment**

<img src="docs/source/images/spg/spg.000066.png" alt="image_tooltip" width="50%" height="50%">

**Digital Mapping + Physical Construction not aligning** 

<img src="docs/source/images/spg/alignment_issue.png" alt="image_tooltip" width="50%" height="50%">



## CLI
OpenVPCal also provides a cli interface to generate calibration patterns, generate SPG test patterns, and to run the calibration itself.
This requires the project settings file to be completed

### Generate SPG Patterns
#### OSX & Linux
```shell
OpenVPCal --ui false --generate_spg_patterns true --project_settings /tmp/output_folder/project_settings.json --output_folder /tmp/output_folder
```
#### Windows
```cmd
OpenVPCal.exe --ui=false --generate_spg_patterns=true --project_settings=/tmp/output_folder/project_settings.json --output_folder=/tmp/output_folder
```

### Generate OpenVPCal Patterns
#### OSX & Linux
```shell
OpenVPCal --ui false --generate_patterns true --project_settings /tmp/output_folder/project_settings.json --output_folder /tmp/output_folder
```
#### Windows
```cmd
OpenVPCal.exe --ui=false --generate_patterns=true --project_settings=/tmp/output_folder/project_settings.json --output_folder=/tmp/output_folder
```
### Run Calibration
#### OSX & Linux
```shell
OpenVPCal --ui false --project_settings /tmp/output_folder/project_settings.json --output_folder /tmp/output_folder
```
#### Windows
```cmd
OpenVPCal.exe --ui=false --project_settings=/tmp/output_folder/project_settings.json --output_folder=/tmp/output_folder
```

## Developer Guide
Below we outline the core usage of the python module, which is the backbone of the OpenVPCal application.

This is available as a python module and can be used to implement into other tools or pipelines as desired.

## Creating A Project

```python
import os

from open_vp_cal.project_settings import ProjectSettings
from open_vp_cal.core.resource_loader import ResourceLoader
from open_vp_cal.core import constants

from open_vp_cal.application_base import OpenVPCalBase

# Create A New Project
project_root = "/tmp/API_TEST"
if not os.path.exists(project_root):
    os.makedirs(project_root)

project_settings = ProjectSettings()
project_settings.ocio_config_path = ResourceLoader.ocio_config_path()
project_settings.output_folder = project_root
project_settings.resolution_height = 2160
project_settings.resolution_width = 3840
project_settings.file_format = constants.FileFormats.FF_EXR
project_settings.export_lut_for_aces_cct = False
project_settings.export_lut_for_aces_cct_in_target_output = False
project_settings.frame_rate = constants.FrameRates.FPS_25
```

## Add A Custom colour Space
```python
custom_primaries = [(0.70800, 0.29200), (0.17000, 0.79700), (0.13100, 0.04600), (0.31270, 0.32900)l]
custom_gamut_name = "LedWall_Custom_Gamut"
project_settings.add_custom_primary(custom_gamut_name, custom_primaries)

### Add a new LED Wall With Standard Gamut
main_wall = project_settings.add_led_wall("Main Wall")
main_wall.target_gamut = constants.ColourSpace.CS_BT2020
main_wall.target_eotf = constants.EOTF.EOTF_ST2084
main_wall.target_max_lum_nits = 1650
```

## Add a new LED Wall With Custom Gamut
```python
custom_wall = project_settings.add_led_wall("Custom Wall")
custom_wall.target_gamut = custom_gamut_name
custom_wall.target_eotf = constants.EOTF.EOTF_ST2084
custom_wall.target_max_lum_nits = 1650
```

## Save The Project Settings
```python
filename = os.path.join(project_settings.output_folder, constants.DEFAULT_PROJECT_SETTINGS_NAME)
project_settings.to_json(filename)
```
## Load The Project Settings
```python
project_settings = ProjectSettings.from_json(filename)
```

## Generate Calibration Patches
```python
open_vp_cal_base = OpenVPCalBase()
open_vp_cal_base.generate_patterns_for_led_walls(project_settings, project_settings.led_walls)
```

## Generate SPG Patches
```python
open_vp_cal_base.generate_spg_patterns_for_led_walls(project_settings, project_settings.led_walls)
```

# NOW WE LOAD AND SHOOT OUR PLATES & PROCESS THE RECORDINGS INTO ACES2065-1 EXRS, SDI CAPTURE COULD BE IMPLEMENTED HERE etc

## Set The Plate Settings
```python
custom_wall.native_camera_gamut = constants.CameraColourSpace.RED_WIDE_GAMUT
main_wall.native_camera_gamut = constants.CameraColourSpace.RED_WIDE_GAMUT
```

## Load The Sequences & Run The ROI Detection & Separation Detection
```python
for led_wall in project_settings.led_walls:
    led_wall.sequence_loader.load_sequence("/path/to/recorded/exrs", file_type=constants.FileFormats.FF_EXR)

    if not led_wall.roi:
        separation_results, auto_roi_results = open_vp_cal_base.run_auto_detect(led_wall)
        if not auto_roi_results or not auto_roi_results.is_valid:
            raise ValueError("Auto ROI detection failed.")

        if not separation_results or not separation_results.is_valid:
            raise ValueError("Separation Detection failed.")

    led_wall.sequence_loader.set_current_frame(led_wall.sequence_loader.start_frame)
```

```python
## Run The Analysis Of The Patches
status = open_vp_cal_base.analyse(project_settings.led_walls)
if not status:
    error_messages = "\n".join(open_vp_cal_base.error_messages())
    warning_messages = "\n".join(open_vp_cal_base.warning_messages())
    raise ValueError(f"Analysis Failed\nWarning Messages:\n{warning_messages}\nError Messages:\n{error_messages}\n")
```

## Run The Post Analysis Validations
```python
status = open_vp_cal_base.post_analysis_validations(project_settings.led_walls)
if not status:
    error_messages = "\n".join(open_vp_cal_base.error_messages())
    warning_messages = "\n".join(open_vp_cal_base.warning_messages())
    raise ValueError(f"Analysis Validation Failed\nWarning Messages:\n{warning_messages}\nError Messages:\n{error_messages}\n")
```

## Apply The Post Analysis Configuration Recommendations
```python
configuration_results = open_vp_cal_base.apply_post_analysis_configuration(project_settings.led_walls)
for led_wall in project_settings.led_walls:
    for param, value in configuration_results[led_wall.name]:
        setattr(led_wall, param, value)
```

## Run The Calibration
```python
status = open_vp_cal_base.calibrate(project_settings.led_walls)
if not status:
    error_messages = "\n".join(open_vp_cal_base.error_messages())
    warning_messages = "\n".join(open_vp_cal_base.warning_messages())
    raise ValueError(f"Calibrate Failed\nWarning Messages:\n{warning_messages}\nError Messages:\n{error_messages}\n")
```

## Export The Calibration
```python
status, led_walls = open_vp_cal_base.export(project_settings, project_settings.led_walls)
if not status:
    error_messages = "\n".join(open_vp_cal_base.error_messages())
    warning_messages = "\n".join(open_vp_cal_base.warning_messages())
    raise ValueError(f"Export Failed\nWarning Messages:\n{warning_messages}\nError Messages:\n{error_messages}\n")
```

## OpenVPCal Project Schema
Whilst the python modules allow for the creation of projects, the schema for the project can be implemented in other languages or libraries.
Below is the schema for the OpenVPCal project settings file.

```json
{
  "type": "object",
  "properties": {
    "openvp_cal_version": {
      "type": "string"
    },
    "project_settings": {
      "type": "object",
      "properties": {
        "file_format": {
          "type": "string"
        },
        "resolution_width": {
          "type": "integer"
        },
        "resolution_height": {
          "type": "integer"
        },
        "output_folder": {
          "type": "string"
        },
        "ocio_config_path": {
          "type": ["string", "null"]
        },
        "custom_logo_path": {
          "type": "string"
        },
        "frames_per_patch": {
          "type": "integer"
        },
        "led_walls": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": {
                "type": "string"
              },
              "enable_eotf_correction": {
                "type": "boolean"
              },
              "enable_gamut_compression": {
                "type": "boolean"
              },
              "auto_wb_source": {
                "type": "boolean"
              },
              "input_sequence_folder": {
                "type": "string"
              },
              "num_grey_patches": {
                "type": "integer"
              },
              "primaries_saturation": {
                "type": "number"
              },
              "calculation_order": {
                "type": "string"
              },
              "input_plate_gamut": {
                "type": "string"
              },
              "native_camera_gamut": {
                "type": "string"
              },
              "reference_to_target_cat": {
                "type": "string"
              },
              "roi": {
                "type": "array",
                "items": {
                  "type": "integer"
                },
                "minItems": 4,
                "maxItems": 4
              },
              "shadow_rolloff": {
                "type": "number"
              },
              "target_max_lum_nits": {
                "type": "integer"
              },
              "target_gamut": {
                "type": "string"
              },
              "target_eotf": {
                "type": "string"
              },
              "target_to_screen_cat": {
                "type": "string"
              },
              "match_reference_wall": {
                "type": "boolean"
              },
              "reference_wall": {
                "type": "string"
              },
              "use_white_point_offset": {
                "type": "boolean"
              },
              "white_point_offset_source": {
                "type": "string"
              },
              "is_verification_wall": {
                "type": "boolean"
              },
              "verification_wall": {
                "type": "string"
              },
              "avoid_clipping": {
                "type": "boolean"
              }
            },
            "required": [
              "name",
              "enable_eotf_correction",
              "enable_gamut_compression",
              "auto_wb_source",
              "input_sequence_folder",
              "num_grey_patches",
              "primaries_saturation",
              "calculation_order",
              "input_plate_gamut",
              "native_camera_gamut",
              "reference_to_target_cat",
              "roi",
              "shadow_rolloff",
              "target_max_lum_nits",
              "target_gamut",
              "target_eotf",
              "target_to_screen_cat",
              "match_reference_wall",
              "reference_wall",
              "use_white_point_offset",
              "white_point_offset_source",
              "is_verification_wall",
              "verification_wall",
              "avoid_clipping"
            ]
          }
        },
        "project_custom_primaries": {
          "type": "object",
          "patternProperties": {
            ".*": {
              "type": "array",
              "items": {
                "type": "array",
                "items": {
                  "type": "number"
                },
                "minItems": 2,
                "maxItems": 2
              },
              "minItems": 4,
              "maxItems": 4
            }
          },
          "additionalProperties": false
        },
        "reference_gamut": {
          "type": "string"
        },
        "frame_rate": {
          "type": "integer"
        },
        "export_lut_for_aces_cct": {
          "type": "boolean"
        },
        "export_lut_for_aces_cct_in_target_out": {
          "type": "boolean"
        }
      },
      "required": [
        "file_format",
        "resolution_width",
        "resolution_height",
        "output_folder",
        "ocio_config_path",
        "custom_logo_path",
        "frames_per_patch",
        "led_walls",
        "project_custom_primaries",
        "reference_gamut",
        "frame_rate",
        "export_lut_for_aces_cct",
        "export_lut_for_aces_cct_in_target_out"
      ]
    }
  },
  "required": ["openvp_cal_version", "project_settings"]
}
```

## Acknowledgements
OpenVPCal was originally developed by Netflix in collaboration with ORCA Studios. The authors would like to extend their deepest gratitude to all the contributors and beta-testers who have made this project possible. Your dedication, insightful feedback, and innovative contributions have been invaluable.

This project has also greatly benefited from the use of several open-source projects, and we are grateful to their respective communities for their ongoing support and development.

Lastly, we appreciate the user community for your enthusiasm and engagement, which inspire continual improvement and innovation.
Thank you all for your support and collaboration.

[Contributors](https://github.com/Netflix-Skunkworks/OpenVPCal/graphs/contributors)

### Changelog


<table>
  <tr>
   <td colspan="2" ><strong><code>CHANGELOG</code></strong>
   </td>
  </tr>
    <tr>
   <td>
   </td>
   <td>Added new changes for release of OpenVPCal 2.0
   </td>
  </tr>
  <tr>
   <td>
   </td>
   <td>Added new userguide for exporting EXR from Davinci and setting up OCIO
   </td>
  </tr>
  <tr>
   <td>
   </td>
   <td>New User guide for V1 released
   </td>
  </tr>
  <tr>
   <td>
   </td>
   <td>
   </td>
  </tr>
</table>





