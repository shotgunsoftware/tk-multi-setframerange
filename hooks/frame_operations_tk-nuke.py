# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import nuke

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

        :returns: Returns the frame range in the form (in_frame, out_frame, head_frame, tail_frame)
        :rtype: tuple[int, int, int, int]
        """
        current_in = int(nuke.root()["first_frame"].value())
        current_out = int(nuke.root()["last_frame"].value())

        current_head = nuke.root()["first_frame"].value()
        current_tail = nuke.root()["last_frame"].value()

        Viewer = nuke.activeViewer().node()
        if Viewer:
            val = Viewer['frame_range'].value()
            if val != '':
                current_in, current_out = val.split("-")
                current_in = int(current_in)
                current_out = int(current_out)
            else:
                current_in = current_head
                current_out = current_tail

        else:
            current_in = current_head
            current_out = current_tail

        return (current_in, current_out, current_head, current_tail)

    def set_frame_range(self, in_frame=None, out_frame=None, head_frame=None, tail_frame=None, **kwargs):
        """
        set_frame_range will set the frame range using `in_frame` and `out_frame` and the head and tail

        :param int in_frame: in_frame for the current context
            (e.g. the current shot, current asset etc)

        :param int out_frame: out_frame for the current context
            (e.g. the current shot, current asset etc)

        :param int head_frame: head_frame for the current context
            (e.g. the current shot, current asset etc)

        :param int tail_frame: tail_frame for the current context
            (e.g. the current shot, current asset etc)
        """

        # unlock
        locked = nuke.root()["lock_range"].value()
        if locked:
            nuke.root()["lock_range"].setValue(False)
        # set values
        nuke.root()["first_frame"].setValue(head_frame)
        nuke.root()["last_frame"].setValue(tail_frame)

        for n in nuke.allNodes('Viewer'):
            n['frame_range_lock'].setValue(True)
            n['frame_range'].setValue('%i-%i' % (int(in_frame), int(out_frame)))

        # and lock again
        if locked:
            nuke.root()["lock_range"].setValue(True)
