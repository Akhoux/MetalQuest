from typing import Union

import hou


def set_shot_frame_range(
    start: Union[int, float],
    end: Union[int, float],
    set_playback_range: bool = True,
    snap_to_integers: bool = True,
) -> None:
    if snap_to_integers:
        start_i = int(round(start))
        end_i = int(round(end))
    else:
        start_i = int(start)
        end_i = int(end)

    if start_i > end_i:
        start_i, end_i = end_i, start_i

    hou.playbar.setFrameRange(start_i, end_i)
    if set_playback_range:
        hou.playbar.setPlaybackRange(start_i, end_i)
    hou.setFrame(start_i)

    hou.putenv("SHOT_START", str(start_i))
    hou.putenv("SHOT_END", str(end_i))


