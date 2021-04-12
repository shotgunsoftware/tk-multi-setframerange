# Copyright (c) 2021 DreamView
# Orginal Author: Shotgun Software
# Modifications: Mark Thielen

"""
An app that syncs the frame range between a scene and a shot in Shotgun.

"""
import os
import traceback

from tank.platform import Application
from tank.platform.qt import QtCore, QtGui
import tank


class SetFrameRange(Application):
    """
    dvs-multi-setframerange is a Shotgun toolkit application that allows you to set and get the
        frame range from shotgun regardless of your specific DCC application.

    Standard applications come implemented for you but you are able to implement support for
        custom engines through the provided hooks.
    """

    def init_app(self):
        """
        App entry point
        """

        # We grab the menu name from the settings so that the user is able to register multiple instances
        # of this app with different frame range fields configured.
        self.engine.register_command(self.get_setting("menu_name"), self.run_app)

    @property
    def context_change_allowed(self):
        """
        Specifies that entity changes are allowed.
        """
        return True

    def destroy_app(self):
        """
        App teardown
        """
        self.logger.debug("Destroying sg_set_frame_range")

    def run_app(self, entity=None):
        """
        Callback from when the menu is clicked.

        The default callback will first query the frame range from shotgun and validate the data.
        If there is missing Shotgun data it will popup a QMessageBox dialog alerting the user.

        Assuming all data exists in shotgun, it will set the frame range with the newly
            queried data and popup a QMessageBox with results.

        Args:
            entity (dict, optional): The entity dictionary with 'id' and 'type'.
        """

        if not entity:
            entity = self.get_entity()
        
        if not entity.get('id'):
            message = "This tool requires an existing scene opened and the scene is associated with a Shot in Shotgun. Check In current file and try again.\n"
            QtGui.QMessageBox.warning(None, "Sync Frame Range not run!", message)
            return

        try:
            new_frame_range = self.get_frame_range_from_shotgun(entity)
            current_frame_range = self.get_current_frame_range()

            if new_frame_range == current_frame_range:
                self.logger.info('Frame range matches Shotgun: {head_in}, {cut_in}, {cut_out}, {tail_out}'.format(**current_frame_range))
                return

            if new_frame_range.get('cut_in') is None or new_frame_range.get('cut_out') is None:
                message = "Shotgun has not yet been populated with \n"
                message += "in and out frame data for this Shot."
                QtGui.QMessageBox.information(None, "No data in Shotgun!", message)
                return

            # now update the frame range.
            # because the frame range is often set in multiple places (e.g render range,
            # current range, anim range etc), we go ahead an update every time, even if the values
            # in Shotgun are the same as the values reported via get_current_frame_range()
            self.set_frame_range(new_frame_range.get('cut_in'), new_frame_range.get('cut_out'), head_in=new_frame_range.get('head_in'), tail_out=new_frame_range.get('tail_out'))
            message = "Your scene has been updated with the \n"
            message += "latest frame ranges from shotgun.\n\n"
          
            message += "{:^5}{:^18}  {:^16} {:^16}\n\n".format("Head In", "Cut In", "Cut Out", "Tail Out").expandtabs(7)
            message += "              {render_in:^18.1f}{render_out:^18.1f}                         ==> Previous Render Frames\n".format(**current_frame_range).expandtabs(8)
            message += "{head_in:^10.1f}{cut_in:^18.1f}{cut_out:^18.1f}{tail_out:^18.1f}  ==> Previous Timeline\n\n".format(**current_frame_range).expandtabs(8)
            message += "{head_in:^10.1f}{cut_in:^18.1f}{cut_out:^18.1f}{tail_out:^18.1f}  ==> Updated Frames".format(**new_frame_range).expandtabs(8)

            QtGui.QMessageBox.information(None, "Frame range updated!", message)
            self.logger.info('Previous Render Frames: {render_in}, {render_out}'.format(**current_frame_range))
            self.logger.info('Previous Timeline: {head_in}, {cut_in}, {cut_out}, {tail_out}'.format(**current_frame_range))
            self.logger.info('Updated Frames: {head_in}, {cut_in}, {cut_out}, {tail_out}'.format(**new_frame_range))


        except tank.TankError:
            message = "There was a problem updating your scene frame range.\n"
            QtGui.QMessageBox.warning(None, "Frame range not updated!", message)
            error_message = traceback.format_exc()
            self.logger.error(error_message)


    ###############################################################################################
    # implementation

    def get_entity(self, entity_type='Shot'):
        """
        get entity from scene

        :returns: data (dict of str: int)
        :rtype: dict()
        :raises: tank.TankError
        """
        try:
            result = self.execute_hook_method("hook_frame_operation", "get_entity", entity_type=entity_type)
        except Exception as err:
            error_message = traceback.format_exc()
            self.logger.error(error_message)
            raise tank.TankError(
                "Encountered an error while getting the entity: {}".format(str(err))
            )

        if not isinstance(result, dict):
            raise tank.TankError(
                "Unexpected type returned from 'hook_frame_operation' for operation get_"
                "entity - expected a 'dictionary' with 'type' and 'id{} {}".format(result, (type(result).__name__)),
                result,
            )
        return result    

    def get_scene_filename(self):
        """
        get scene filename from current scene

        :returns: unicode
        :rtype: unicode
        :raises: tank.TankError
        """
        try:
            result = self.execute_hook_method("hook_frame_operation", "get_scene_filename")
        except Exception as err:
            error_message = traceback.format_exc()
            self.logger.error(error_message)
            raise tank.TankError(
                "Encountered an error while getting the scene filename: {}".format(str(err))
            )

        if not isinstance(result, unicode):
            raise tank.TankError(
                "Unexpected type returned from 'hook_frame_operation' for operation get_"
                "scene_filename - expected a string'{} {}".format(result, (type(result).__name__)),
                result,
            )
        return result    

    def get_frame_range_from_shotgun(self, entity=None):
        """
        get_frame-range_from_shotgun will query shotgun for the
            'sg_head_in_field', 'sg_cut_in_frame_field', 'sg_cut_out_frame_field', 'sg_tail_out_field' 
            setting values and return a
            dict of (str: int): head_in, in, out, tail_out

        If the fields specified in the settings do not exist in your Shotgun site, this will raise
            a tank.TankError letting you know which field is missing.

        :returns: data (dict of str: int): head_in, in, out, tail_out
        :rtype: dict()
        :raises: tank.TankError
        """

        sg_entity_type = entity["type"]
        sg_filters = [["id", "is", entity["id"]]]

        sg_head_in_field = 'sg_head_in'
        if self.get_setting("sg_head_in_field"):
            sg_head_in_field = self.get_setting("sg_head_in_field")

        sg_cut_in_field = 'sg_cut_in'
        if self.get_setting("sg_cut_in_frame_field"):
            sg_cut_in_field = self.get_setting("sg_cut_in_frame_field")
        sg_cut_out_field = 'sg_cut_out'
        if self.get_setting("sg_cut_out_frame_field"):
            sg_cut_out_field = self.get_setting("sg_cut_out_frame_field")

        sg_tail_out_field = 'sg_tail_out'
        if self.get_setting("sg_tail_out_field"):
            sg_tail_out_field = self.get_setting("sg_tail_out_field")
        fields = ['code', sg_head_in_field, sg_tail_out_field, sg_cut_in_field, sg_cut_out_field]

        data = self.shotgun.find_one(sg_entity_type, filters=sg_filters, fields=fields)

        # check shot name matches scene file name
        if data is None:
            raise tank.TankError(
                "Configuration error: No entity found in Shotgun for {}, id: {}".format(sg_entity_type, entity['id'])
            ) 
        else:
            if data and not self.get_scene_filename() != data.get('code'):
                raise tank.TankError(
                    "Configuration error: Your current scene does not match"
                    " the Shotgun {} name of {}".format(data.get('type'), data.get('code'))
                )


        # check if fields exist!
        if sg_cut_in_field not in data:
            raise tank.TankError(
                "Configuration error: Your current entity is connected to a Shotgun "
                "{}. This entity type does not have a "
                "field {}.{}!".format(entity, sg_entity_type, sg_cut_in_field)
            )

        if sg_cut_out_field not in data:
            raise tank.TankError(
                "Configuration error: Your current entity is connected to a Shotgun "
                "{}. This entity type does not have a "
                "field {}.{}!".format(entity, sg_cut_in_field, sg_cut_out_field)
            )

        result = {
            'head_in': data[sg_head_in_field], 
            'cut_in': data[sg_cut_in_field], 
            'cut_out': data[sg_cut_out_field], 
            'tail_out': data[sg_tail_out_field],
            'render_in': data[sg_cut_in_field],
            'render_out': data[sg_cut_out_field]
        }
        return result

    def get_current_frame_range(self):
        """
        get_current_frame_range will execute the hook specified in the 'hook_frame_operation'
            setting for this app.
        It will record the result of the hook and return the values as a dict of (str: int).

        If there is an internal exception thrown from the hook, it will reraise the exception as
            a tank.TankError and write the traceback to the log.
        If the data returned is not in the correct format, dict with at least two keys, it will
            also throw a tank.TankError exception.

        :returns: data (dict of str: int): head_in, in, out, tail_out
        :rtype: dict()
        :raises: tank.TankError
        """
        try:
            result = self.execute_hook_method("hook_frame_operation", "get_frame_range")
        except Exception as err:
            error_message = traceback.format_exc()
            self.logger.error(error_message)
            raise tank.TankError(
                "Encountered an error while getting the frame range: {}".format(str(err))
            )

        if not isinstance(result, dict) or (
            isinstance(result, dict) and len(result) < 2
        ):
            raise tank.TankError(
                "Unexpected type returned from 'hook_frame_operation' for operation get_"
                "frame_range - expected a 'dictionary' with in_frame, out_frame values but "
                "returned '{} {}".format(result, (type(result).__name__)),
                result,
            )
        return result

    def set_frame_range(self, cut_in, cut_out, head_in=None, tail_out=None):
        """
        set_current_frame_range will execute the hook specified in the 'hook_frame_operation'
            setting for this app.
        It will pass the 'cut_in' and 'cut_out' to the hook.

        If there is an internal exception thrown from the hook, it will reraise the exception as
            a tank.TankError and write the traceback to the log.

        :param int in_frame: The value of in_frame that we want to set in the current session.
        :param int out_frame: The value of out_frame that we want to set in the current session.
        :raises: tank.TankError
        """
        try:
            self.execute_hook_method(
                "hook_frame_operation",
                "set_frame_range",
                cut_in=cut_in,
                cut_out=cut_out,
                head_in=head_in,
                tail_out=tail_out,
            )
        except Exception as err:
            error_message = traceback.format_exc()
            self.logger.error(error_message)
            raise tank.TankError(
                "Encountered an error while setting the frame range: {}".format(str(err))
            )
