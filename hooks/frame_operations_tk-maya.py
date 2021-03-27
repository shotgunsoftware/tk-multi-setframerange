# Copyright (c) 2021 DreamView
# Orginal Author: Shotgun Software
# Modifications: Mark Thielen

import maya.cmds as cmds
import os
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class FrameOperation(HookBaseClass):
    """
    Hook called to perform a frame operation with the
    current scene
    """

    def get_entity(self, entity_type='Shot'):
        """Get an entity id from the dvs_data node embedded in the maya scene if it exists.\n
        Search scene using cmds.ls('dvs_data')\n
        The dvs_asset attribute could be any entity in Shotgun. \n
        This forces the type to 'Shot' by default.

        Args:
            entity_type (str, optional): The type of entity to set. Defaults to 'Shot'.
        Returns:
            dict: dict of 'id' and 'type'
        """        
        entity = {}
        if cmds.ls('dvs_data'):
            entity['id'] = cmds.getAttr('dvs_data.dvs_asset')
            entity['type'] = entity_type
        return entity

    def get_scene_filename(self):
        """Get the current scene filename without the folder.\n
        i.e. scene.ma or scene.mb

        Returns:
            str: Scene filename
        """        
        return os.path.basename(cmds.file(q=1, sceneName=True))

    def get_frame_range(self, **kwargs):
        """
        get_frame_range will return a dictionary of head_cut_in, cut_in, cut_out, tail_out

        :returns: data (dict of str: int): head_in, cut_in, cut_out, tail_out
        :rtype: dict()
        :raises: tank.TankError
        """
        result = {}
        result['head_in'] = cmds.playbackOptions(query=True, animationStartTime=True)
        result['cut_in'] = cmds.playbackOptions(query=True, minTime=True)
        result['cut_out'] = cmds.playbackOptions(query=True, maxTime=True)
        result['tail_out'] = cmds.playbackOptions(query=True, animationEndTime=True)
        result['render_in'] = cmds.getAttr("defaultRenderGlobals.startFrame")
        result['render_out'] = cmds.getAttr("defaultRenderGlobals.endFrame")
        return result

    def set_frame_range(self, cut_in, cut_out, **kwargs):
        """
        set_frame_range will set the frame range using `cut_in` and `cut_out`

        :param int cut_in: cut_in for the current context
            (e.g. the current shot, current asset etc)

        :param int cut_out: cut_out for the current context
            (e.g. the current shot, current asset etc)

        """
        head_in = cut_in
        tail_out = cut_out

        for key, value in kwargs.items():
            if 'head' in key:
                head_in = value
            if 'tail' in key:
                tail_out = value

        # set frame ranges for plackback
        cmds.playbackOptions(
            ast=head_in,
            minTime=cut_in,
            maxTime=cut_out,
            aet=tail_out
        )

        # set frame ranges for rendering
        cmds.setAttr("defaultRenderGlobals.startFrame", cut_in)
        cmds.setAttr("defaultRenderGlobals.endFrame", cut_out)
