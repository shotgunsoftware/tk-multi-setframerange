# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import win32com

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
        xsi = win32com.client.Dispatch("XSI.Application")

        current_in = xsi.GetValue("PlayControl.In")
        current_out = xsi.GetValue("PlayControl.Out")
        return (current_in, current_out)

    def set_frame_range(self, in_frame=None, out_frame=None, **kwargs):
        """
        set_frame_range will set the frame range using `in_frame` and `out_frame`

        :param int in_frame: in_frame for the current context
            (e.g. the current shot, current asset etc)

        :param int out_frame: out_frame for the current context
            (e.g. the current shot, current asset etc)

        """

        Application = win32com.client.Dispatch("XSI.Application")

        # set playback control
        Application.SetValue("PlayControl.In", in_frame)
        Application.SetValue("PlayControl.Out", out_frame)
        Application.SetValue("PlayControl.GlobalIn", in_frame)
        Application.SetValue("PlayControl.GlobalOut", out_frame)

        # set frame ranges for rendering
        Application.SetValue("Passes.RenderOptions.FrameStart", in_frame)
        Application.SetValue("Passes.RenderOptions.FrameEnd", out_frame)
