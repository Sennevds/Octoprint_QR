# coding=utf-8
from __future__ import absolute_import
from octoprint_qr.DatabaseManager import DatabaseManager
from octoprint_qr.api.QrAPI import QrManagerAPI
from octoprint.events import Events

# (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.

import octoprint.plugin


class QRPlugin(QrManagerAPI,
               octoprint.plugin.SimpleApiPlugin,
               octoprint.plugin.SettingsPlugin,
               octoprint.plugin.AssetPlugin,
               octoprint.plugin.TemplatePlugin,
               octoprint.plugin.StartupPlugin,
               octoprint.plugin.EventHandlerPlugin):

    # ~~ SettingsPlugin mixin
    def initialize(self):
        self._logger.info("Start initializing")
        self.selectedSpool = None
        # DATABASE
        self.databaseConnectionProblemConfirmed = False
        sqlLoggingEnabled = False
        self._databaseManager = DatabaseManager(
            self._logger, sqlLoggingEnabled)
        databaseSettings = self._buildDatabaseSettingsFromPluginSettings()

        # init database
        self._databaseManager.initDatabase(
            databaseSettings, self._sendMessageToClient)
        self.selectedSpool = self.loadSelectedSpool()

    def _buildDatabaseSettingsFromPluginSettings(self):
        databaseSettings = DatabaseManager.DatabaseSettings()
        pluginDataBaseFolder = self.get_plugin_data_folder()
        databaseSettings.baseFolder = pluginDataBaseFolder
        databaseSettings.fileLocation = self._databaseManager.buildDefaultDatabaseFileLocation(databaseSettings.baseFolder)
        return databaseSettings

    def _sendDataToClient(self, payloadDict):
        self._plugin_manager.send_plugin_message(self._identifier,
                                                 payloadDict)

    def _sendMessageToClient(self, type, title, message):
        self._logger.warning("SendToClient: " + type +
                             "#" + title + "#" + message)
        title = "SPM:" + title
        self._sendDataToClient(dict(action="showPopUp",
                                    type=type,
                                    title=title,
                                    message=message))

    def get_settings_defaults(self):
        settings = dict()
        settings["selectedSpoolDatabaseId"] = None
        settings["sendToSpoolManager"] = False
        settings["useOctoprintCam"] = True
        settings["customCamUrl"] = None
        settings["codeScanTimeout"] = 300
        return settings

    # ~~ AssetPlugin mixin
    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return dict(
            js=["js/qr.js", "js/apiClient.js", "js/spoolDialog.js"]
            )

    def on_event(self, event, payload):
        if (Events.PRINT_STARTED == event):
            self._logger.info("print started")
            self.selectedSpool = self.loadSelectedSpool()
            return
    # ~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return dict(
            qr=dict(
                displayName="QR Plugin",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="Sennevds",
                repo="OctoPrint-QR",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/Sennevds/OctoPrint-QR/archive/{target_version}.zip"
            )
        )

    def get_template_configs(self):
        return [
            dict(type="tab", name="Qr"),
            dict(type="settings")
        ]

    # def on_after_startup(self):
    #     self._logger.info("Hello World!")
    #     self._logger.info(self._settings.global_get(["webcam", "stream"]))

    # def gcode_script_variables(self, comm, script_type, script_name, *args, **kwargs):
    #     if not script_type == "gcode" or not script_name == "beforePrintStarted":
    #         return None

    #     prefix = None
    #     postfix = None

    #     variables = dict(myvariable="")
    #     return prefix, postfix, variables

    def queuing_hook(self, comm, phase, cmd, cmd_type, gcode, *args, **kwargs):
        if cmd and cmd == "{{Custom_Command}}":
            self._logger.info("random found")
            splitted = self.selectedSpool.gcodeText.splitlines()
            for command in splitted:
                self._logger.info(f"send command: {command}")
                comm._sendCommand(command)
            return None


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "QR Plugin"

# Starting with OctoPrint 1.4.0 OctoPrint will also support to run under Python 3 in addition to the deprecated
# Python 2. New plugins should make sure to run under both versions for now. Uncomment one of the following
# compatibility flags according to what Python versions your plugin supports!
# __plugin_pythoncompat__ = ">=2.7,<3" # only python 2
__plugin_pythoncompat__ = ">=3,<4"  # only python 3
# __plugin_pythoncompat__ = ">=2.7,<4" # python 2 and 3
__plugin_name__ = "QR"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = QRPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.queuing_hook
    }
