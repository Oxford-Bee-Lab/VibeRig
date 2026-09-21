# Script to play a series of tones, based on a config csv file and then output a csv listing the original
# config plus a column of start times for each tone.

import logging
import math
import os
import platform
import subprocess
import sys
import time
import wave
from collections.abc import Iterator
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io.wavfile

OUTPUT_DIR = Path.home() / "vr_output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FRAMES_PER_SECOND: int = 44100
SINE_WAV_FILENAME = "sine_wave.wav"
TEST_FILENAME = "test.txt"

CFG_COL_DURATION = "duration_seconds"
CFG_COL_FREQUENCY = "frequency"
CFG_COL_RELATIVE_VOLUME = "relative_volume"
CFG_COL_SILENCE_AFTER = "silence_after"
CFG_COLS = [
    CFG_COL_DURATION,
    CFG_COL_FREQUENCY,
    CFG_COL_RELATIVE_VOLUME,
    CFG_COL_SILENCE_AFTER,
]

OUTPUT_COL_TONE_START_TIME = "tone_play_start_utc"

##############################################################################################################
# Set up logging.
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("vibe_rig")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s"))
logger.addHandler(handler)
##############################################################################################################


def get_tone_config_list(filename: str) -> list[dict]:
    """Read config from CSV and return as a list of key:value pairs."""
    config_path = Path(filename)
    if config_path.is_file():
        config_source = config_path.open(mode="rb")
    else:
        config_resource = resources.files("VibeRig.controller").joinpath(filename)
        if not config_resource.is_file():
            msg = f"Config file not found: {filename}"
            raise FileNotFoundError(msg)
        config_source = config_resource.open(mode="rb")

    with config_source:
        config_df = pd.read_csv(filepath_or_buffer=config_source)
    tone_config_list: list[dict] = config_df.to_dict(orient="records")

    ##########################################################################################################
    # Check the config is valid

    # All columns are present?
    for column in CFG_COLS:
        if column not in config_df.columns:
            msg = f"ERROR: '{column}' column is missing from config file {filename}"
            raise ValueError(msg)

    # Data is valid
    # We do this at start of day so we fail ASAP if there's an issue, rather than waiting until we try to
    # generate the wav.
    for tone_cfg in tone_config_list:
        if tone_cfg[CFG_COL_DURATION] < 0:
            msg = f"ERROR: {CFG_COL_DURATION} must be >=0, not {tone_cfg[CFG_COL_DURATION]}"
            raise ValueError(msg)
        if tone_cfg[CFG_COL_FREQUENCY] <= 0:
            msg = f"ERROR: {CFG_COL_FREQUENCY} must be >0, not {tone_cfg[CFG_COL_FREQUENCY]}"
            raise ValueError(msg)
        if not 0 <= tone_cfg[CFG_COL_RELATIVE_VOLUME] <= 100:
            msg = f"ERROR: {CFG_COL_RELATIVE_VOLUME} must be 0-100, not {tone_cfg[CFG_COL_RELATIVE_VOLUME]}"
            raise ValueError(msg)
        if tone_cfg[CFG_COL_SILENCE_AFTER] < 0:
            msg = f"ERROR: {CFG_COL_SILENCE_AFTER} must be >=0, not {tone_cfg[CFG_COL_SILENCE_AFTER]}"
            raise ValueError(msg)

    # All good, return the list
    logger.info(f"Config successfully read from {filename}")
    return tone_config_list


def create_sine_wav_file_using_math_wave(duration: float, frequency: float, relative_volume: float) -> str:
    """Create an 8-bit PCM, mono wav file in current directory, return the filename."""

    def sound_wave() -> Iterator[int]:
        for frame in range(round(duration * FRAMES_PER_SECOND)):
            time = frame / FRAMES_PER_SECOND
            amplitude = math.sin(2 * math.pi * frequency * time)

            # Amplitude range is 0-255 for 8 bit unsigned integer
            yield round(128 + 127 * relative_volume / 100 * amplitude)

    with wave.open(SINE_WAV_FILENAME, mode="wb") as wav_file:
        wav_file.setnchannels(1)  # 1 channel = mono
        wav_file.setsampwidth(1)  # 1 byte = PCM with 8-bit unsigned integer samples
        wav_file.setframerate(FRAMES_PER_SECOND)
        wav_file.writeframes(bytes(sound_wave()))
    return SINE_WAV_FILENAME


def create_sine_wav_file_using_scipy(duration: float, frequency: float, relative_volume: float) -> str:
    """Create a 16 bit PCM, mono wav file in current directory, return the filename."""
    # Generate time points
    time_points = np.linspace(0, duration, int(FRAMES_PER_SECOND * duration))

    # Generate sine wave with maximum 16 bit amplitude/value for relative_volume = 100
    max_16_bit_value = np.iinfo(np.int16).max
    sine_wave = relative_volume / 100 * max_16_bit_value * np.sin(frequency * time_points * 2 * np.pi)

    # Save the WAV file
    scipy.io.wavfile.write(SINE_WAV_FILENAME, FRAMES_PER_SECOND, sine_wave)
    logger.debug(f"Wav file {SINE_WAV_FILENAME} created, {frequency=}")

    return SINE_WAV_FILENAME


def delete_wav_file(filename: str) -> None:
    logger.debug("Delete wav file")
    os.remove(filename)


def play_wav_file(wav_filename: str, relative_volume: float) -> str:
    vol_command: list[str] | None = None
    # Use platform-specific command to play the wavfile. Throw exception if there's an issue
    match platform.system():
        case "Windows":
            wav_path = str(Path(wav_filename).resolve()).replace("'", "''")
            command = [
                "powershell",
                "-NoProfile",
                "-Command",
                f"(New-Object Media.SoundPlayer '{wav_path}').PlaySync();",
            ]
        case "Linux":
            relative_volume = math.sqrt(relative_volume / 100) * 100
            vol_command = ["amixer", "-c", "2", "set", "Digital", f"{relative_volume}%"]
            command = ["aplay", "-D", "plughw:2,0", str(Path(wav_filename).resolve())]
        case _:
            msg = f"Unrecognized system OS type: {platform.system()}"
            raise NotImplementedError(msg)

    if vol_command:
        result = subprocess.check_output(vol_command, text=True)
        logger.debug(f"Set volume result: {result}")

    # Checking output will throw an exception if the cmd line command failed
    return subprocess.check_output(command, text=True)


def run_experiment(config_filename: str) -> None:
    """Entry point to run the experiment for a given config."""
    logger.info(f"Run experiment using config from {config_filename}")
    # Load & check config from a CSV
    tone_configs = get_tone_config_list(filename=config_filename)

    # Check we have permission to write & delete in the local directory
    with open(TEST_FILENAME, "a") as f:
        f.write("Test file to check permissions")
    os.remove(TEST_FILENAME)

    start_time: datetime = datetime.now(tz=UTC)
    output_rows = []

    try:
        for tone_cfg in tone_configs:
            # For each row in the CSV
            # - Create a wav file based on the cfg.
            # - Create a row to output to the results file, with the cfg and start tone time
            # - Play the wav file
            # - Delete the wav file (so they don't accumulate)
            # - Do nothing for a while, based on cfg
            logger.info(f"Run {tone_cfg=}")
            wav_filename: str = create_sine_wav_file_using_math_wave(
                duration=tone_cfg[CFG_COL_DURATION],
                frequency=tone_cfg[CFG_COL_FREQUENCY],
                relative_volume=tone_cfg[CFG_COL_RELATIVE_VOLUME],
            )
            output_row = tone_cfg.copy()
            output_row[OUTPUT_COL_TONE_START_TIME] = datetime.now(tz=UTC)
            output_rows.append(output_row)

            play_wav_file(wav_filename=wav_filename, relative_volume=tone_cfg[CFG_COL_RELATIVE_VOLUME])

            delete_wav_file(filename=wav_filename)

            # Sleep until the next tone. We don't need the tone timings to be completely precise, so we don't
            # worry about any delays added by creating wav files etc.
            time.sleep(tone_cfg[CFG_COL_SILENCE_AFTER])

            # Try to generate tone & pipe directly to aplay. (Didn't work)
            # For each row in the CSV
            # - @@@ create row to output to the results file
            # - Tell ffmpeg to generate a sine wave based on config, and pipe to aplay
            # - Do nothing for a while, based on config file
            # cmd_string = f"ffmpeg -f lavfi -i
            #  'sine=frequency={tone_cfg[CFG_COL_FREQUENCY]}:duration={tone_cfg[CFG_COL_DURATION]}'
            #  -f alsa hw:0,0 | aplay"

            # https://forums.raspberrypi.com/viewtopic.php?t=298333 may help with volume
            # https://www.procedimento.com.br/?p=go&os=raspberrypi&
            #  raspberrypi=using-aplay-on-raspberry-pi-a-guide-to-audio-playback
            # says you can do aplay -V50 <filemame>

    except Exception:
        logger.exception("Expected fatal error")
        raise
    finally:
        # Always output whatever data we got
        output_name = OUTPUT_DIR / f"output_{start_time.strftime(format='%Y%m%dT%H%M')}_{config_filename}"
        output_df = pd.DataFrame(data=output_rows)
        output_df.to_csv(
            output_name,
            index=False,
        )
        logger.info(f"Done. Results of {len(output_rows)} tones output to {output_name}")


if __name__ == "__main__":
    print("Running vibe controller from command line")
    if len(sys.argv) != 2:
        print("You must provide a config csv filename as a cmd line parameter")
        sys.exit(1)

    config_filename = sys.argv[1]
    run_experiment(config_filename=config_filename)
