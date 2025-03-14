# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import hou

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class FrameOperation(HookBaseClass):
    """
    Hook called to perform a frame operation with the
    current scene
    """

    def get_frame_range(self, **kwargs):
        """
        get_frame_range will return a tuple of (in_frame, out_frame)

        :returns: Returns the frame range in the form (in_frame, out_frame)
        :rtype: tuple[int, int]
        """
        # Get the global start and end frame
        # Note, when using hou.playbar.playbackRange(), unpacking the start frame returns `1001.0000000000001`,
        # thus will incorrectly flag the scene sync summary pop up to show, if the PTR start frame is 1001.0
        current_in, current_out = hou.playbar.frameRange()
        return int(current_in), int(current_out)

    def set_frame_range(self, in_frame=None, out_frame=None, **kwargs):
        """
        set_frame_range will set the frame range using `in_frame` and `out_frame`

        :param int in_frame: in_frame for the current context
            (e.g. the current shot, current asset etc)

        :param int out_frame: out_frame for the current context
            (e.g. the current shot, current asset etc)

        """

        # We have to use hscript until SideFX gets around to implementing hou.setGlobalFrameRange()
        hou.hscript("tset `((%s-1)/$FPS)` `(%s/$FPS)`" % (in_frame, out_frame))
        hou.playbar.setPlaybackRange(in_frame, out_frame)
