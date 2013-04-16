"""
Copyright (c) 2012 Shotgun Software, Inc
----------------------------------------------------

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
        
        self.engine.register_command("sync_framerange", self.run_app, {"title": "Sync Frame Range with Shotgun"})

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
            
        else:
            raise tank.TankError("Don't know how to get current frame range for engine %s!" % engine)

        return (current_in, current_out)

    def set_frame_range(self, engine, in_frame, out_frame):

        if engine == "tk-maya":
            import pymel.core as pm
            pm.playbackOptions(minTime=in_frame, maxTime=out_frame)
        
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
            
        else:
            raise tank.TankError("Don't know how to set current frame range for engine %s!" % engine)


        
        
        
        
