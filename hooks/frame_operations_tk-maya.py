# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import maya.cmds as cmds

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class FrameOperation(HookBaseClass):
    """
    Hook called to perform a frame operation with the
    current scene
    """

    def get_frame_range(self, **kwargs):
        """
        get_frame_range will return a dictionary of head_cut_in, cut_in, cut_out, tail_out

        :returns: data (dict of str: int): head_in, cut_in, cut_out, tail_out
        :rtype: dict()
        :raises: tank.TankError
        """
        result = {}
        result['head_in'] = cmds.playbackOptions(query=True, minTime=True)
        result['cut_in'] = cmds.playbackOptions(query=True, animationStartTime=True)
        result['cut_out'] = cmds.playbackOptions(query=True, maxTime=True)
        result['tail_out'] = cmds.playbackOptions(query=True, animationEndTime=True)
        return result

    def set_frame_range(self, cut_in=None, cut_out=None, **kwargs):
        """
        set_frame_range will set the frame range using `cut_in` and `cut_out`

        :param int cut_in: cut_in for the current context
            (e.g. the current shot, current asset etc)

        :param int cut_out: cut_out for the current context
            (e.g. the current shot, current asset etc)

        """

        min_cut_in = cut_in
        max_cut_out = cut_out

        for key, value in kwargs.items():
            if 'head' in key:
                min_cut_in = value
            elif 'tail' in key:
                max_cut_out = value

        # set frame ranges for plackback
        cmds.playbackOptions(
            minTime=min_cut_in,
            maxTime=max_cut_out,
            animationStartTime=cut_in,
            animationEndTime=cut_out,
        )

        # set frame ranges for rendering
        cmds.setAttr("defaultRenderGlobals.startFrame", cut_in)
        cmds.setAttr("defaultRenderGlobals.endFrame", cut_out)
