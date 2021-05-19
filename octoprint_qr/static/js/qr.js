$(function () {
    var PLUGIN_ID = "qr"; // from setup.py plugin_identifier

    ///////////////////////////////////////////////////////////////////////////////////////////////////////// VIEW MODEL
    function QrViewModel(parameters) {
        var PLUGIN_ID = "qr"; // from setup.py plugin_identifier

        var self = this;
        self.apiClient = new QrAPIClient(PLUGIN_ID, BASEURL);
        self.pluginSettings = null;
        self.loginStateViewModel = parameters[0];
        self.loginState = parameters[0];
        self.settingsViewModel = parameters[1];
        self.printerStateViewModel = parameters[2];
        self.filesViewModel = parameters[3];
        self.pluginSettings = null;
        self.spoolDialog = new SpoolDialog();
        self.spoolDialog._createSpoolItemForEditing();
        self.customCamUrlVisible = ko.observable(false);

        self.title = ko.observable();
        self.title("asfdasdfasd");
        self.updateButtonText = ko.observable();
        self.updateButtonText("Update");
        self.readQr = function () {
            self.spoolDialog.scanQr();
        };
        self.update = function () {
            self.spoolDialog.updateSpools();
        };
        self.onBeforeBinding = function () {
            self.spoolDialog.initBinding(self.apiClient);
            self.pluginSettings =
                self.settingsViewModel.settings.plugins[PLUGIN_ID];
            self.pluginSettings.useOctoprintCam.subscribe(function (
                newCheckedVaue
            ) {
                self.customCamUrlVisible(!newCheckedVaue);
            });
            self.customCamUrlVisible(!self.pluginSettings.useOctoprintCam());
        };
        self.showSpoolDialogAction = function (selectedSpoolItem) {
            self.spoolDialog.showDialog(selectedSpoolItem);
        };
        ko.bindingHandlers.numeric = {
            init: function (element, valueAccessor) {
                $(element).on("keydown", function (event) {
                    // Allow: backspace, delete, tab, escape, and enter
                    if (
                        event.keyCode == 46 ||
                        event.keyCode == 8 ||
                        event.keyCode == 9 ||
                        event.keyCode == 27 ||
                        event.keyCode == 13 ||
                        // Allow: Ctrl+A
                        (event.keyCode == 65 && event.ctrlKey === true) ||
                        // Allow: . ,
                        event.keyCode == 188 ||
                        event.keyCode == 190 ||
                        event.keyCode == 110 ||
                        // Allow: home, end, left, right
                        (event.keyCode >= 35 && event.keyCode <= 39)
                    ) {
                        // let it happen, don't do anything
                        return;
                    } else {
                        // Ensure that it is a number and stop the keypress
                        if (
                            event.shiftKey ||
                            ((event.keyCode < 48 || event.keyCode > 57) &&
                                (event.keyCode < 96 || event.keyCode > 105))
                        ) {
                            event.preventDefault();
                        }
                    }
                });
            },
        };
    }
    OCTOPRINT_VIEWMODELS.push({
        construct: QrViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [
            "loginStateViewModel",
            "settingsViewModel",
            "printerStateViewModel",
            "filesViewModel",
        ],
        // Elements to bind to, e.g. #settings_plugin_SpoolManager, #tab_plugin_SpoolManager, ...
        elements: [
            document.getElementById("settings_qr"),
            document.getElementById("tab_qrOverview"),
        ],
    });
});
