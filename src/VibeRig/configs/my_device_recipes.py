from dataclasses import replace

from expidite_rpi import DPtree
from expidite_rpi import configuration as root_cfg
from expidite_rpi.sensors.sensor_audio_on_demand import (
    DEFAULT_AUDIO_SENSOR_CFG,
    AudioSensor,
    AudioSensorCfg,
)
from expidite_rpi.sensors.sensor_rpicam_vid import (
    DEFAULT_RPICAM_SENSOR_CFG,
    RpicamSensor,
    RpicamSensorCfg,
)

logger = root_cfg.setup_logger("vibe_rig")


def create_vibe_rig_monitor() -> list[DPtree]:
    """Create a basic vibe rig monitor with continuous recording of video and audio."""
    # Define the audio sensor
    audio_cfg: AudioSensorCfg = replace(
        DEFAULT_AUDIO_SENSOR_CFG,
        sensor_index=1,
    )
    my_audio_sensor = AudioSensor(audio_cfg)

    # Define the video sensor
    video_cfg: RpicamSensorCfg = replace(
        DEFAULT_RPICAM_SENSOR_CFG,
        rpicam_cmd=(
            "rpicam-vid --camera SENSOR_INDEX --framerate 10 --width 1296 --height 1296 -o FILENAME -t 180000"
        ),
    )
    my_video_sensor = RpicamSensor(video_cfg)

    my_audio_tree = DPtree(my_audio_sensor)
    my_video_tree = DPtree(my_video_sensor)
    return [my_audio_tree, my_video_tree]


def create_vibe_rig_controller() -> list[DPtree]:
    """Create a basic vibe rig controller, that just records audio."""
    # Define the audio sensor
    audio_cfg: AudioSensorCfg = replace(
        DEFAULT_AUDIO_SENSOR_CFG,
        sensor_index=1,
    )
    my_audio_sensor = AudioSensor(audio_cfg)

    my_audio_tree = DPtree(my_audio_sensor)
    return [my_audio_tree]
