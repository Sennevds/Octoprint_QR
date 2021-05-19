from __future__ import absolute_import

import octoprint.plugin
import json
import flask
from playhouse.shortcuts import model_to_dict
import requests
from flask import request
from octoprint_qr.models.QrModel import QrModel
from octoprint_qr.qr_engine.QrEngine import QrEngine


class QrManagerAPI(octoprint.plugin.BlueprintPlugin):
    def initialize(self):
        self._logger.info("Api initialize")
        self._logger.info(flask.url_for("plugin.qr.CreateQR"))

    def isEmpty(self, value):
        if (value is None or len(str(value).strip()) == 0):
            return True
        return False

    def isNotEmpty(self, value):
        return self.isEmpty(value) is False

    def _getValueFromJSONOrNone(self, key, json):
        if key in json:
            return json[key]
        return None

    def _toIntFromJSONOrNone(self, key, json):
        value = self._getValueFromJSONOrNone(key, json)
        if (value is not None):
            if (self.isNotEmpty(value)):
                try:
                    value = int(value)
                except Exception as e:
                    errorMessage = str(e)
                    self._logger.error(
                        f"could not transform value '{str(value)}' for key '{key}' to int: {errorMessage}")
                    value = None
            else:
                value = None
        return value

    def _updateSpoolModelFromJSONData(self, spoolModel, jsonData):
        if (self._getValueFromJSONOrNone("databaseId", jsonData) is not None):
            spoolModel.code = self._getValueFromJSONOrNone(
                "databaseId", jsonData)
        spoolModel.code = self._getValueFromJSONOrNone("code", jsonData)
        spoolModel.gcodeText = self._getValueFromJSONOrNone(
            "gcodeText", jsonData)
        spoolModel.displayName = self._getValueFromJSONOrNone(
            "displayName", jsonData)
        spoolModel.spoolManagerId = self._toIntFromJSONOrNone(
            "spoolManagerId", jsonData)
        pass

    def loadSelectedSpool(self, ):
        spoolModel = None
        databaseId = self._settings.get_int(["selectedSpoolDatabaseId"])
        self._logger.info(f"database id: {databaseId}")
        if (databaseId is not None):
            self._databaseManager.connectoToDatabase()
            self._logger.info("connected to database")
            spoolModel = self._databaseManager.loadQr(databaseId)

            self._databaseManager.closeDatabase()
            if (spoolModel is None):
                self._logger.warning(
                    "Last selected Spool from plugin-settings not found in database. Maybe deleted in the meantime.")
        return spoolModel

    def _selectSpool(self, databaseId):
        spoolModel = None
        if (databaseId is not None and databaseId != -1):
            spoolModel = self._databaseManager.loadQr(databaseId)
            # check if loaded
            if (spoolModel is not None):
                self._logger.info("Store selected spool '" +
                                  spoolModel.code+"' in settings.")

                # - store spool in Settings
                self._settings.set_int(["selectedSpoolDatabaseId"], databaseId)
                self._settings.save()
            else:
                self._logger.warning(f"Selected Spool with id '{str(databaseId)}" +
                                     "' not in database anymore. Maybe deleted in the meantime.")

        if (spoolModel is None):
            # No selection
            self._logger.info("Clear stored selected spool in settings.")
            self._settings.set_int(["selectedSpoolDatabaseId"], None)
            self._settings.save()
            pass

        return spoolModel

    @octoprint.plugin.BlueprintPlugin.route("/CreateQR", methods=["PUT"])
    def CreateQR(self):
        self._logger.info("API Save spool")
        jsonData = request.json
        databaseId = self._getValueFromJSONOrNone("databaseId", jsonData)
        self._databaseManager.connectoToDatabase()
        # if (databaseId != None):
        #     self._logger.info("Update spool with database id '"+str(databaseId)+"'")
        #     spoolModel = self._databaseManager.loadSpool(databaseId, withReusedConnection=True)
        #     if (spoolModel == None):
        #         self._logger.warning("Save spool failed. Something is wrong")
        #     else:
        #         self._updateSpoolModelFromJSONData(spoolModel, jsonData)
        # else:
        self._logger.info("Create new spool")
        qrModel = QrModel()
        qrModel.code = self._getValueFromJSONOrNone("code", jsonData)
        qrModel.gcodeText = self._getValueFromJSONOrNone("gcode", jsonData)
        databaseId = self._databaseManager.saveQr(
            qrModel, withReusedConnection=True)
        self._databaseManager.closeDatabase()

        return flask.jsonify()

    @octoprint.plugin.BlueprintPlugin.route("/ReadQR", methods=["GET"])
    def ReadQR(self):
        self._logger.info("Get code from camera")
        webcamUrl = self._settings.global_get(["webcam", "stream"]) if self._settings.get_boolean(["useOctoprintCam"]) else self._settings.get(["customCamUrl"])
        self._logger.info(f"Webcam URL: {webcamUrl}")
        qrEngine = QrEngine(
            self._logger, webcamUrl, self._settings.get_int(["codeScanTimeout"]))
        code = qrEngine.get_qr()
        self._logger.info(f"code found {code}")
        qr = self._databaseManager.getQrByCode(
            code, withReusedConnection=False)
        if(qr is None):
            qr = QrModel()
            qr.code = code
        self._logger.info(f"Gcode {qr.gcodeText}")
        json_data = model_to_dict(qr)
        return flask.jsonify(json_data)

    @octoprint.plugin.BlueprintPlugin.route("/GetSpools", methods=["GET"])
    def GetSpools(self):
        spools = self._databaseManager.getSpools(withReusedConnection=False)
        json_data = transformAllSpoolModelsToDict(spools)
        return flask.jsonify(json_data)

    @octoprint.plugin.BlueprintPlugin.route("/saveSpool", methods=["PUT"])
    def saveSpool(self):
        self._logger.info("API Save spool")
        jsonData = request.json
        databaseId = self._getValueFromJSONOrNone("databaseId", jsonData)
        self._databaseManager.connectoToDatabase()
        if (databaseId is not None):
            self._logger.info(
                "Update spool with database code '"+str(databaseId)+"'")
            spoolModel = self._databaseManager.loadQr(
                databaseId, withReusedConnection=True)
            if (spoolModel is None):
                self._logger.warning("Save spool failed. Something is wrong")
            else:
                self._updateSpoolModelFromJSONData(spoolModel, jsonData)
        else:
            self._logger.info("Create new spool")
            spoolModel = QrModel()
            self._updateSpoolModelFromJSONData(spoolModel, jsonData)

        databaseId = self._databaseManager.saveQr(
            spoolModel, withReusedConnection=True)
        self._databaseManager.closeDatabase()
        return flask.jsonify()

    @octoprint.plugin.BlueprintPlugin.route("/selectSpool", methods=["PUT"])
    def select_spool(self):
        self._logger.info("API Store selected spool")
        jsonData = request.json
        databaseId = self._getValueFromJSONOrNone("databaseId", jsonData)
        spoolModel = self._selectSpool(databaseId)
        spoolModelAsDict = None
        if (spoolModel is not None):
            spoolModelAsDict = model_to_dict(spoolModel)
            spoolManager = self._plugin_manager.get_plugin_info(
                "SpoolManager", require_enabled=True)
            if(self._settings.get_boolean(["sendToSpoolManager"]) and spoolManager is not None):
                url = f'{request.host_url}plugin/SpoolManager/selectSpool'
                self._logger.info(f"SpoolManager url: {url}")
                payload = json.dumps({
                    "databaseId": spoolModel.spoolManagerId
                })
                headers = {
                    'X-Api-Key': '022BFC3E2FC84BAA8C46A35CC4189C2B',
                    'Content-Type': 'application/json'
                }
                response = requests.put(url, headers=headers, data=payload)
                self._logger.info(f"response: {response.text}")
                # requests.get(url)
        return flask.jsonify({
            "selectedSpool": spoolModelAsDict
        })


def transformAllSpoolModelsToDict(allSpoolModels):
    result = []
    if (allSpoolModels is not None):
        for job in allSpoolModels:
            spoolAsDict = model_to_dict(job)
            result.append(spoolAsDict)
    return result
