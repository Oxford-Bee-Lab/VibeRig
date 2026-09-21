# VibeRig

VibeRig is a rig for studying bumblebee responses to vibration stimuli. It is built on top
of [ExPiDITE](https://github.com/Oxford-Bee-Ops/expidite), which provides the fleet management, sensor
recording and cloud-upload framework used by the **Monitor** device, while a lightweight standalone
script drives the **Controller** device.

## Bill of materials

- **Structure**: box / frame that mounts the shake plate on which the bees are placed.
- **Controller**: vibration control RPI, driving an "exciter" (aka speaker) attached to the shake plate.
- **Monitoring**: RPI running ExPiDITE, recording video, audio and [optinally] acceleration of the shake plate.

## Software

- Code lives in the GitHub repo [Oxford-Bee-Lab/VibeRig](https://github.com/Oxford-Bee-Lab/VibeRig).
- VibeRig must be installed on **both** devices (Monitor and Controller).
- The **Monitor** runs [ExPiDITE](https://github.com/Oxford-Bee-Ops/expidite), configured using the fleet
  config at [src/VibeRig/configs/fleet_config_lab.py](src/VibeRig/configs/fleet_config_lab.py).
- The **Controller** is deliberately simple: it just runs
  [vibe_controller.py](src/VibeRig/controller/vibe_controller.py), driven by a `config_test*.csv` file
  that specifies the tones (frequency / duration / volume / silence) to play.

## Installation

VibeRig is installed as a Python package on top of ExPiDITE, following the same device installation
flow as ExPiDITE itself. See the [ExPiDITE README](https://github.com/Oxford-Bee-Ops/expidite) for full
background on the underlying framework.

### Pre-requisites

You will need:

- A Raspberry Pi (RPI) for each device (Monitor and Controller) and any attached sensors / actuators
  (accelerometer, microphone, camera, speaker / shaker).
- A GitHub account with access to the
  [Oxford-Bee-Lab/VibeRig](https://github.com/Oxford-Bee-Lab/VibeRig) repo.
- An Azure blobstore account for storage of the Monitor's sensor output (VibeRig uploads to the
  `LabWHO-2026` blobstore).
- Some basic experience with Python.

Helpful applications:

- **Microsoft Visual Studio Code** as an IDE.
- **GitHub Desktop** to manage code easily.
- **Raspberry Pi Imager** to flash the Raspberry Pi OS onto SD cards.
- An SSH terminal app, such as **PuTTY**, to remotely log in to the RPIs.
- A secure file transfer app, such as **WinSCP**, to upload initial config to the RPIs.
- **Microsoft Azure Storage Explorer** to view files in the Azure blobstore.

### Installing the Monitor device

The Monitor runs the full ExPiDITE stack, configured for VibeRig.

1. Physically build the rig and attach the Monitor's sensors (accelerometer, microphone, camera).
2. Flash an SD card with Raspberry Pi OS (using Raspberry Pi Imager, enable SSH access and default Wifi
   config to make life easier), install it and power up the RPI.
3. Get the device's `wlan0` MAC address (this is its `device_id` in the fleet config):
   ```bash
   cat /sys/class/net/wlan0/address
   ```
4. Check the device is already listed in
   [fleet_config_lab.py](src/VibeRig/configs/fleet_config_lab.py) under `INVENTORY`. If not, add a
   `DeviceCfg` entry for it (see the ExPiDITE `DeviceCfg` docs for details).
5. Log in to the RPI and create an `.expidite` folder in the user's home directory:
   ```bash
   mkdir ~/.expidite
   ```
6. Copy your `keys.env` (based on the templates in
   `expidite_rpi/example/` in the ExPiDITE repo) and `system.cfg` files (in VibeRig/configs) into `~/.expidite`:
   - In `keys.env`, set `cloud_storage_key` to the Shared Access Signature for the `LabWHO-2026` Azure
     Storage account.
7. Copy the `rpi_installer.sh` script (from `expidite_rpi/scripts/` in the ExPiDITE repo) into
   `~/.expidite` and run it:
   ```bash
   cd ~/.expidite && dos2unix *.sh && chmod +x *.sh && ./rpi_installer.sh
   ```
   This creates a virtual environment, updates OS packages, installs ExPiDITE's RpiCore, installs
   VibeRig (via `my_git_repo_url`) and its dependencies, and sets up the RPI ready to run as a Monitor.
8. Once installed, verify it's working:
   - CLI: run `bcli` and select `2. View Status`.
   - You should see acceleration, audio and video data appearing in the `LabWHO-2026` blobstore.

### Installing the Controller device

The Controller does not run ExPiDITE - it just needs Python and the VibeRig package so it can run
`vibe_controller.py`.

1. Flash an SD card with Raspberry Pi OS, install it and power up the RPI. Attach the speaker / shaker
   used to drive the vibration / sound stimuli.
2. Install VibeRig and its dependencies:
   ```bash
   pip install git+https://github.com/Oxford-Bee-Lab/VibeRig.git
   ```
3. Confirm the controller scripts and config are present:
   ```bash
   ls
   ```
   You should see `vibe_controller.py` and one or more `config_test*.csv` files under
   [src/VibeRig/controller/](src/VibeRig/controller/).

## Operation

The current rig has two RPIs:

| Device     | Device ID (`wlan0` MAC) |
|------------|--------------------------|
| Monitor    | `d83addf7857a`           |
| Controller | `d83add4fc38b`           |

### Controller: triggering vibration / sound

The Controller is used to trigger a vibration stimulus:

1. Log in over SSH with `bee-ops` & password.
2. Run `ls` to confirm the presence of `vibe_controller.py` and the `config_test*.csv` files.
3. Edit (or choose) a `config_test*.csv` file to specify the audio / vibration sequence you want to
   play. Each row defines one tone: `frequency`, `duration_seconds`, `relative_volume` and
   `silence_after`.
4. Trigger the stimulus, passing the config file as the only argument, for example:
   ```bash
   python vibe_controller.py config_test_5_knocks.csv
   ```
   A results file, recording the actual start time of each tone, is written to `~/splat_output`.

### Monitor: continuous recording

The Monitor should be running 24x7 once installed. It uploads acceleration, audio and video data to the
`LabWHO-2026` blobstore automatically. Check its status remotely at any time using `bcli` (option
`2. View Status`) or via the ExPiDITE dashboard.

## Development

Static analysis checks (ruff, ty, pyright, mypy) can be run locally with:

```bash
check.cmd
```

Install the development dependencies first:

```bash
pip install -e ".[dev]"
```
