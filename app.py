# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
An app that syncs the frame range between a scene and a shot in Shotgun.

"""

import sys
import os

from tank.platform import Application
import tank


class SetFrameRange(Application):

    def init_app(self):

        # make sure that the context has an entity associated - otherwise it wont work!
        if self.context.entity is None:
            raise tank.TankError("Cannot load the Set Frame Range application! "
                                 "Your current context does not have an entity (e.g. "
                                 "a current Shot, current Asset etc). This app requires "
                                 "an entity as part of the context in order to work.")

        self.engine.register_command("Sync Frame Range with Shotgun", self.run_app)

    def destroy_app(self):
        self.log_debug("Destroying sg_set_frame_range")


    def run_app(self):
        """
        Callback from when the menu is clicked.
        """

        (new_in, new_out) = self.get_frame_range_from_shotgun()
        (current_in, current_out) = self.get_current_frame_range(self.engine.name)

        if new_in is None or new_out is None:
            message =  "Shotgun has not yet been populated with \n"
            message += "in and out frame data for this Shot."

        elif int(new_in) != int(current_in) or int(new_out) != int(current_out):
            # change!
            message =  "Your scene has been updated with the \n"
            message += "latest frame ranges from shotgun.\n\n"
            message += "Previous start frame: %d\n" % current_in
            message += "New start frame: %d\n\n" % new_in
            message += "Previous end frame: %d\n" % current_out
            message += "New end frame: %d\n\n" % new_out
            self.set_frame_range(self.engine.name, new_in, new_out)

        else:
            # no change
            message = "Already up to date!\n\n"
            message += "Your scene is already in sync with the\n"
            message += "start and end frames in shotgun.\n\n"
            message += "No changes were made."

        # present a pyside dialog
        # lazy import so that this script still loads in batch mode
        from tank.platform.qt import QtCore, QtGui

        QtGui.QMessageBox.information(None, "Frame Range Updated", message)







    ###############################################################################################
    # implementation


    def get_frame_range_from_shotgun(self):
        """
        Returns (in, out) frames from shotgun.
        """
        # we know that this exists now (checked in init)
        entity = self.context.entity

        sg_entity_type = self.context.entity["type"]
        sg_filters = [["id", "is", entity["id"]]]

        sg_in_field = self.get_setting("sg_in_frame_field")
        sg_out_field = self.get_setting("sg_out_frame_field")
        fields = [sg_in_field, sg_out_field]

        data = self.shotgun.find_one(sg_entity_type, filters=sg_filters, fields=fields)

        # check if fields exist!
        if sg_in_field not in data:
            raise tank.TankError("Configuration error: Your current context is connected to a Shotgun "
                                 "%s. This entity type does not have a "
                                 "field %s.%s!" % (sg_entity_type, sg_entity_type, sg_in_field))

        if sg_out_field not in data:
            raise tank.TankError("Configuration error: Your current context is connected to a Shotgun "
                                 "%s. This entity type does not have a "
                                 "field %s.%s!" % (sg_entity_type, sg_entity_type, sg_out_field))

        return ( data[sg_in_field], data[sg_out_field] )


    def get_current_frame_range(self, engine):

        if engine == "tk-maya":
            import pymel.core as pm
            import maya.cmds as cmds
            current_in = cmds.playbackOptions(query=True, minTime=True)
            current_out = cmds.playbackOptions(query=True, maxTime=True)

        elif engine == "tk-nuke":
            import nuke
            current_in = nuke.root()["first_frame"].value()
            current_out = nuke.root()["last_frame"].value()

        elif engine == "tk-motionbuilder":
            from pyfbsdk import FBPlayerControl, FBTime

            lPlayer = FBPlayerControl()
            current_in = lPlayer.LoopStart.GetFrame()
            current_out = lPlayer.LoopStop.GetFrame()

        elif engine == "tk-softimage":
            import win32com
            xsi = win32com.client.Dispatch('XSI.Application')

            current_in = xsi.GetValue("PlayControl.In")
            current_out = xsi.GetValue("PlayControl.Out")

        elif engine == "tk-houdini":
            import hou
            current_in, current_out = hou.playbar.playbackRange()

        elif engine == "tk-cinema4d":
            import c4d
            doc = c4d.documents.GetActiveDocument()
            current_in = doc[c4d.DOCUMENT_MINTIME].GetFrame(doc.GetFps())
            current_out = doc[c4d.DOCUMENT_MAXTIME].GetFrame(doc.GetFps())

        else:
            raise tank.TankError("Don't know how to get current frame range for engine %s!" % engine)

        return (current_in, current_out)

    def set_frame_range(self, engine, in_frame, out_frame):

        if engine == "tk-maya":
            import pymel.core as pm

            # set frame ranges for plackback
            pm.playbackOptions(minTime=in_frame,
                               maxTime=out_frame,
                               animationStartTime=in_frame,
                               animationEndTime=out_frame)

            # set frame ranges for rendering
            defaultRenderGlobals=pm.PyNode('defaultRenderGlobals')
            defaultRenderGlobals.startFrame.set(in_frame)
            defaultRenderGlobals.endFrame.set(out_frame)

        elif engine == "tk-nuke":
            import nuke

            # unlock
            locked = nuke.root()["lock_range"].value()
            if locked:
                nuke.root()["lock_range"].setValue(False)
            # set values
            nuke.root()["first_frame"].setValue(in_frame)
            nuke.root()["last_frame"].setValue(out_frame)
            # and lock again
            if locked:
                nuke.root()["lock_range"].setValue(True)

        elif engine == "tk-motionbuilder":
            from pyfbsdk import FBPlayerControl, FBTime

            lPlayer = FBPlayerControl()
            lPlayer.LoopStart = FBTime(0, 0, 0, in_frame)
            lPlayer.LoopStop = FBTime(0, 0, 0, out_frame)

        elif engine == "tk-softimage":
            import win32com
            Application = win32com.client.Dispatch('XSI.Application')

            Application.SetValue("PlayControl.In", in_frame)
            Application.SetValue("PlayControl.Out", out_frame)

        elif engine == "tk-houdini":
            import hou
            hou.playbar.setPlaybackRange(in_frame, out_frame)

        elif engine == "tk-cinema4d":
            import c4d
            doc = c4d.documents.GetActiveDocument()
            # set values in the editing view
            doc[c4d.DOCUMENT_MINTIME] = c4d.BaseTime(int(in_frame),
                                                     doc.GetFps())
            doc[c4d.DOCUMENT_MAXTIME] = c4d.BaseTime(int(out_frame),
                                                     doc.GetFps())
            # set values for render
            rd = doc.GetActiveRenderData()
            rd[c4d.RDATA_FRAMEFROM] = c4d.BaseTime(int(in_frame), doc.GetFps())
            rd[c4d.RDATA_FRAMETO] = c4d.BaseTime(int(out_frame), doc.GetFps())

        else:
            raise tank.TankError("Don't know how to set current frame range for engine %s!" % engine)
