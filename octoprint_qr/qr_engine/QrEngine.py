from __future__ import absolute_import
import octoprint.plugin
import pyzbar.pyzbar as pyzbar
import cv2
import logging
import time


class QrEngine(octoprint.plugin.SettingsPlugin):
    def __init__(self, parentLogger, url, timeout):
        self._logger = logging.getLogger(parentLogger.name + "." + self.__class__.__name__)
        self._url = url
        self._timeout = timeout

    def decode(self, im):
        decodedObjects = pyzbar.decode(im)
        return decodedObjects

    def get_qr(self):
        cap = cv2.VideoCapture(self._url)
        previousData = None
        barCode = None
        timeout = self._timeout
        timeout_start = time.time()
        decodedObjects = None
        im = None
        while(barCode is None and time.time() < timeout_start + timeout):
            # Capture frame-by-frame
            ret, frame = cap.read()
            # Our operations on the frame come here
            im = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            decodedObjects = self.decode(im)
            for decodedObject in decodedObjects:
                if(previousData != decodedObject.data):
                    self._logger.info(f"decode object type: {decodedObject.type}")
                    # if decodedObject.type == "QRCODE":
                    self._logger.info("QR code found")
                    previousData = decodedObject.data
                    self._logger.info(f'Type : {decodedObject.type}')
                    self._logger.info(f'Data : {decodedObject.data}')
                    barCode = decodedObject.data.decode("utf-8")
                    break
        cap.release()
        cv2.destroyAllWindows()
        return barCode
