from __future__ import absolute_import

import datetime
import os
import logging
import shutil
from peewee import SqliteDatabase
from playhouse.migrate import SqliteMigrator
from octoprint_qr.models.QrModel import QrModel
from octoprint_qr.models.PluginMetaDataModel import PluginMetaDataModel
FORCE_CREATE_TABLES = False

CURRENT_DATABASE_SCHEME_VERSION = 2

# List all Models
MODELS = [PluginMetaDataModel, QrModel]


class DatabaseManager(object):

    class DatabaseSettings:
        # Internal stuff
        baseFolder = ""
        fileLocation = ""
        # External stuff
        useExternal = False
        type = "postgresql"  # postgresql,  mysql NOT sqlite
        name = ""
        host = ""
        port = 0
        user = ""
        password = ""

        def __str__(self):
            return str(self.__dict__)

    def __init__(self, parentLogger, sqlLoggingEnabled):
        self.sqlLoggingEnabled = sqlLoggingEnabled
        self._logger = logging.getLogger(
            parentLogger.name + "." + self.__class__.__name__)
        self._sqlLogger = logging.getLogger(
            parentLogger.name + "." + self.__class__.__name__ + ".SQL")

        self._database = None
        self._databseSettings = None
        self._sendDataToClient = None
        self._isConnected = False
        self._currentErrorMessageDict = None

    def _buildDatabaseConnection(self):
        database = SqliteDatabase(self._databaseSettings.fileLocation)
        return database

    def _createDatabase(self, forceCreateTables):

        if forceCreateTables:
            self._logger.info(
                "Creating new database-tables, because FORCE == TRUE!")
            self._createDatabaseTables()
        else:
            # check, if we need an scheme upgrade
            self._createOrUpgradeSchemeIfNecessary()

        self._logger.info("Database created-check done")

    def _createOrUpgradeSchemeIfNecessary(self):

        self._logger.info("Check if database-scheme upgrade needed...")
        schemeVersionFromDatabaseModel = None
        schemeVersionFromDatabase = None
        try:
            cursor = self.db.execute_sql(
                'select "version" from "qr_pluginmetadatamodel" where key="'+PluginMetaDataModel.KEY_DATABASE_SCHEME_VERSION+'";')
            result = cursor.fetchone()
            if (result != None):
                schemeVersionFromDatabase = int(result[0])
                self._logger.info("Current databasescheme: " +
                                  str(schemeVersionFromDatabase))
            else:
                self._logger.warn(
                    "Strange, table is found (maybe), but there is no result of the schem version. Try to recreate a new db-scheme")
                self.backupDatabaseFile()  # safty first
                self._createDatabaseTables()
                return
            pass
        except Exception as e:
            self._logger.exception(e)
            self.closeDatabase()
            errorMessage = str(e)
            if (
                # - SQLLite
                errorMessage.startswith("no such table") or
                # - Postgres
                "does not exist" in errorMessage or
                # - mySQL errorcode=1146
                "doesn\'t exist" in errorMessage
            ):
                self._createDatabaseTables()
                return
            else:
                self._logger.error(str(e))

        if not schemeVersionFromDatabase == None:
            currentDatabaseSchemeVersion = schemeVersionFromDatabase
            if (currentDatabaseSchemeVersion < CURRENT_DATABASE_SCHEME_VERSION):
                # auto upgrade done only for local database
                if (self._databaseSettings.useExternal == True):
                    self._logger.warn(
                        "Scheme upgrade is only done for local database")
                    return

                # evautate upgrade steps (from 1-2 , 1...6)
                self._logger.info("We need to upgrade the database scheme from: '" + str(
                    currentDatabaseSchemeVersion) + "' to: '" + str(CURRENT_DATABASE_SCHEME_VERSION) + "'")

                try:
                    self.backupDatabaseFile()
                    self._upgradeDatabase(
                        currentDatabaseSchemeVersion, CURRENT_DATABASE_SCHEME_VERSION)
                except Exception as e:
                    self._logger.error("Error during database upgrade!!!!")
                    self._logger.exception(e)
                    return
                self._logger.info("...Database-scheme successfully upgraded.")
            else:
                self._logger.info("...Database-scheme upgraded not needed.")
        else:
            self._logger.warn(
                "...something was strange. Should not be shwon in log. Check full log")
        pass

    def _upgradeDatabase(self, currentDatabaseSchemeVersion, targetDatabaseSchemeVersion):

        migrationFunctions = [self._upgradeFrom1To2]

        for migrationMethodIndex in range(currentDatabaseSchemeVersion - 1, targetDatabaseSchemeVersion - 1):
            self._logger.info("Database migration from '" + str(
                migrationMethodIndex + 1) + "' to '" + str(migrationMethodIndex + 2) + "'")
            migrationFunctions[migrationMethodIndex]()
            pass
        pass

    def _upgradeFrom1To2(self):
        migrator = SqliteMigrator(self._database)
        migrate(
            migrator.add_column('qr_qrmodel', 'displayName',
                                QrModel.displayName),
            migrator.add_column(
                'qr_qrmodel', 'spoolManagerId', QrModel.spoolManagerId),
        )

    def _createDatabaseTables(self):
        self._logger.info("Creating new database tables for qr-plugin")
        self._database.connect(reuse_if_open=True)
        self._database.drop_tables(MODELS)
        self._database.create_tables(MODELS)

        PluginMetaDataModel.create(
            key=PluginMetaDataModel.KEY_DATABASE_SCHEME_VERSION, value=CURRENT_DATABASE_SCHEME_VERSION)
        self.closeDatabase()

    def _storeErrorMessage(self, type, title, message, sendErrorPopUp):
        # store current error message
        self._currentErrorMessageDict = {
            "type": type,
            "title": title,
            "message": message
        }
        # send to client, if needed
        if (sendErrorPopUp == True):
            self._passMessageToClient(type, title, message)

    # public functions
    @staticmethod
    def buildDefaultDatabaseFileLocation(pluginDataBaseFolder):
        databaseFileLocation = os.path.join(
            pluginDataBaseFolder, "spoolmanager.db")
        return databaseFileLocation

    def initDatabase(self, databaseSettings, sendMessageToClient):

        self._logger.info("Init DatabaseManager")
        self._currentErrorMessageDict = None
        self._passMessageToClient = sendMessageToClient
        self._databaseSettings = databaseSettings

        databaseFileLocation = DatabaseManager.buildDefaultDatabaseFileLocation(
            databaseSettings.baseFolder)
        self._databaseSettings.fileLocation = databaseFileLocation
        existsDatabaseFile = str(os.path.exists(
            self._databaseSettings.fileLocation))
        self._logger.info(
            "Databasefile '" + self._databaseSettings.fileLocation + "' exists: " + existsDatabaseFile)

        import logging
        logger = logging.getLogger('peewee')
        # we need only the single logger without parent
        logger.parent = None
        # logger.addHandler(logging.StreamHandler())
        # activate SQL logging on PEEWEE side and on PLUGIN side
        # logger.setLevel(logging.DEBUG)
        # self._sqlLogger.setLevel(logging.DEBUG)
        self.showSQLLogging(self.sqlLoggingEnabled)

        connected = self.connectoToDatabase(sendErrorPopUp=False)
        if (connected is True):
            self._createDatabase(FORCE_CREATE_TABLES)
            self.closeDatabase()

        return self._currentErrorMessageDict

    def assignNewDatabaseSettings(self, databaseSettings):
        self._databaseSettings = databaseSettings

    def getDatabaseSettings(self):
        return self._databaseSettings

    def testDatabaseConnection(self, databaseSettings=None):
        result = None
        backupCurrentDatabaseSettings = None
        try:
            # use provided databasesettings or default if not provided
            if (databaseSettings is not None):
                backupCurrentDatabaseSettings = self._databaseSettings
                self._databaseSettings = databaseSettings

            succesfull = self.connectoToDatabase()
            if (succesfull is False):
                result = self.getCurrentErrorMessageDict()
        finally:
            try:
                self.closeDatabase()
            except:
                pass  # do nothing
            if (backupCurrentDatabaseSettings is not None):
                self._databaseSettings = backupCurrentDatabaseSettings

        return result

    def getCurrentErrorMessageDict(self):
        return self._currentErrorMessageDict

    # connect to the current database
    def connectoToDatabase(self, withMetaCheck=False, sendErrorPopUp=True):
        # reset current errorDict
        self._currentErrorMessageDict = None
        self._isConnected = False

        # build connection
        try:
            self._logger.info("Databaseconnection with...")
            self._logger.info(self._databaseSettings)
            self._database = self._buildDatabaseConnection()

            # connect to Database
            DatabaseManager.db = self._database
            self._database.bind(MODELS)

            self._database.connect()
            self._logger.info(
                "Database connection succesful. Checking Scheme versions")
            self._isConnected = True
        except Exception as e:
            errorMessage = str(e)
            self._logger.exception("connectoToDatabase")
            self.closeDatabase()
            # type, title, message
            self._storeErrorMessage(
                "error", "connection problem", errorMessage, sendErrorPopUp)
            return False
        return self._isConnected

    def closeDatabase(self, ):
        self._currentErrorMessageDict = None
        try:
            self._database.close()
            pass
        except Exception as e:
            pass  # ignore close exception
        self._isConnected = False

    def isConnected(self):
        return self._isConnected

    def showSQLLogging(self, enabled):
        import logging
        logger = logging.getLogger('peewee')

        if (enabled):
            logger.setLevel(logging.DEBUG)
            self._sqlLogger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.ERROR)
            self._sqlLogger.setLevel(logging.ERROR)

    def backupDatabaseFile(self):

        if (os.path.exists(self._databaseSettings.fileLocation)):
            self._logger.info("Starting database backup")
            now = datetime.datetime.now()
            currentDate = now.strftime("%Y%m%d-%H%M")
            backupDatabaseFilePath = self._databaseSettings.fileLocation[0:-
                                                                         3] + "-backup-"+currentDate+".db"
            # backupDatabaseFileName = "spoolmanager-backup-"+currentDate+".db"
            # backupDatabaseFilePath = os.path.join(backupFolder, backupDatabaseFileName)
            if not os.path.exists(backupDatabaseFilePath):
                shutil.copy(self._databaseSettings.fileLocation,
                            backupDatabaseFilePath)
                self._logger.info(
                    "Backup of spoolmanager database created '" + backupDatabaseFilePath + "'")
            else:
                self._logger.warn("Backup of spoolmanager database ('" +
                                  backupDatabaseFilePath + "') is already present. No backup created.")
            return backupDatabaseFilePath
        else:
            self._logger.info("No database backup needed, because there is no databasefile '" +
                              str(self._databaseSettings.fileLocation)+"'")

    def reCreateDatabase(self, databaseSettings):
        self._currentErrorMessageDict = None
        self._logger.info("ReCreating Database")

        backupCurrentDatabaseSettings = None
        if (databaseSettings is not None):
            backupCurrentDatabaseSettings = self._databaseSettings
            self._databaseSettings = databaseSettings
        try:
            # - connect to dataabase
            self.connectoToDatabase()

            self._createDatabase(True)

            # - close dataabase
            self.closeDatabase()
        finally:
            # - restore database settings
            if (backupCurrentDatabaseSettings is not None):
                self._databaseSettings = backupCurrentDatabaseSettings

    # DATABASE OPERATIONS

    def _handleReusableConnection(self, databaseCallMethode, withReusedConnection, methodeNameForLogging, defaultReturnValue=None):
        try:
            if (withReusedConnection is True):
                if (self._isConnected is False):
                    self._logger.error(
                        "Database not connected. Check database-settings!")
                    return defaultReturnValue
            else:
                self.connectoToDatabase()
            return databaseCallMethode()
        except Exception:
            errorMessage = "Database call error in methode " + methodeNameForLogging
            self._logger.exception(errorMessage)

            self._passMessageToClient("error",
                                      "DatabaseManager",
                                      errorMessage + ". See OctoPrint.log for details!")
            return defaultReturnValue
        finally:
            try:
                if (withReusedConnection == False):
                    self._closeDatabase()
            except:
                pass  # do nothing
        pass

    def loadDatabaseMetaInformations(self, databaseSettings=None):

        backupCurrentDatabaseSettings = None
        if (databaseSettings is not None):
            backupCurrentDatabaseSettings = self._databaseSettings
        else:
            databaseSettings = self._databaseSettings
            backupCurrentDatabaseSettings = self._databaseSettings
        schemeVersionFromPlugin = CURRENT_DATABASE_SCHEME_VERSION
        localSchemeVersionFromDatabaseModel = "-"
        externalSchemeVersionFromDatabaseModel = "-"
        errorMessage = ""
        loadResult = False
        try:
            currentDatabaseType = databaseSettings.type
            databaseSettings.type = "sqlite"
            databaseSettings.baseFolder = self._databaseSettings.baseFolder
            databaseSettings.fileLocation = self._databaseSettings.fileLocation
            self._databaseSettings = databaseSettings
            try:
                self.connectoToDatabase(sendErrorPopUp=False)
                localSchemeVersionFromDatabaseModel = PluginMetaDataModel.get(
                    PluginMetaDataModel.key == PluginMetaDataModel.KEY_DATABASE_SCHEME_VERSION).value
                self.closeDatabase()
            except Exception as e:
                errorMessage = "local database: " + str(e)
                self._logger.error("Connecting to local database not possible")
                self._logger.exception(e)
                try:
                    self.closeDatabase()
                except Exception:
                    pass  # ignore close exception

            # Use orign Databasetype to collect the other meta dtaa (if neeeded)
            databaseSettings.type = currentDatabaseType
            if (databaseSettings.useExternal == True):
                # External DB
                self._databaseSettings = databaseSettings
                self.connectoToDatabase(sendErrorPopUp=False)
                externalSchemeVersionFromDatabaseModel = PluginMetaDataModel.get(
                    PluginMetaDataModel.key == PluginMetaDataModel.KEY_DATABASE_SCHEME_VERSION).value
                self.closeDatabase()
            loadResult = True
        except Exception as e:
            errorMessage = str(e)
            self._logger.exception(e)
            try:
                self.closeDatabase()
            except Exception:
                pass  # ignore close exception
        finally:
            # restore orig. databasettings
            if (backupCurrentDatabaseSettings != None):
                self._databaseSettings = backupCurrentDatabaseSettings

        return {
            "success": loadResult,
            "errorMessage": errorMessage,
            "schemeVersionFromPlugin": schemeVersionFromPlugin,
            "localSchemeVersionFromDatabaseModel": localSchemeVersionFromDatabaseModel,
            "externalSchemeVersionFromDatabaseModel": externalSchemeVersionFromDatabaseModel,
        }

    def loadQr(self, databaseId, withReusedConnection=False):
        def databaseCallMethode():
            self._logger.info(f"try to find qr model with id: {databaseId}")
            qrmodel = QrModel.get_by_id(databaseId)
            self._logger.info(f"qr model found with code: {qrmodel.code}")
            return qrmodel

        return self._handleReusableConnection(databaseCallMethode, withReusedConnection, "loadQr")

    def getQrByCode(self, qr, withReusedConnection=False):
        def databaseCallMethode():
            result = None
            try:
                result = QrModel.get(QrModel.code == qr)
                self._logger.info(
                    f"myQuery: {result} first object: {result.code}")
            except QrModel.DoesNotExist:
                pass
            return result

        return self._handleReusableConnection(databaseCallMethode, withReusedConnection, "loadQr")

    def getSpools(self, withReusedConnection=False):
        def databaseCallMethode():
            result = QrModel.select()
            return result

        return self._handleReusableConnection(databaseCallMethode, withReusedConnection, "getSpools")

    def deleteQr(self, databaseId, withReusedConnection=False):
        def databaseCallMethode():
            with self._database.atomic() as transaction:  # Opens new transaction.
                try:
                    deleteResult = QrModel.delete_by_id(databaseId)
                    if (deleteResult == 0):
                        return None
                    return databaseId
                    pass
                except Exception as e:
                    # Because this block of code is wrapped with "atomic", a
                    # new transaction will begin automatically after the call
                    # to rollback().
                    transaction.rollback()
                    self._logger.exception("Could not delete spool from database:" + str(e))

                    self._passMessageToClient("Qr DatabaseManager", "Could not delete the spool ('"+ str(databaseId) +"') from the database. See OctoPrint.log for details!")
                    return None
        return self._handleReusableConnection(databaseCallMethode, withReusedConnection, "saveSpool")

    def saveQr(self, qrModel, withReusedConnection=False):
        def databaseCallMethode():
            with self._database.atomic() as transaction:  # Opens new transaction.
                try:
                    databaseId = qrModel.databaseId
                    if (databaseId is not None):
                        # we need to update and we need to make sure nobody else modify the data
                        currentQrModel = self.loadQr(
                            databaseId, withReusedConnection)
                        if (currentQrModel is None):
                            self._passMessageToClient("error", "DatabaseManager",
                                                      "Could not update the Spool, because it is already deleted!")
                            return
                    qrModel.save()
                    databaseId = qrModel.databaseId
                    transaction.commit()
                except Exception:
                    transaction.rollback()
                    self._logger.exception(
                        "Could not insert Spool into database")

                    self._passMessageToClient(
                        "error", "DatabaseManager", "Could not insert the spool into the database. See OctoPrint.log for details!")
                pass

            return databaseId

        return self._handleReusableConnection(databaseCallMethode, withReusedConnection, "saveSpool")
