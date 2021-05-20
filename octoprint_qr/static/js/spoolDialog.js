function SpoolDialog() {
    var self = this;
    // self.componentFactory = new ComponentFactory();
    self.spoolDialog = null;
    self.apiClient = null;
    self.webcamUrl = null;
    self.spools = ko.observableArray();
    self.showPopUp = function(popupType, popupTitle, message){
        var title = popupType.toUpperCase() + ": " + popupTitle;
        var popupId = (title+message).replace(/([^a-z0-9]+)/gi, '-');
        if($("."+popupId).length <1) {
            new PNotify({
                title: title,
                text: message,
                type: popupType,
                hide: false,
                addclass: popupId
            });
        }
    };
    var SpoolItem = function (spoolData) {
        this.code = ko.observable();
        this.gcodeText = ko.observable();
        this.databaseId = ko.observable();
        this.displayName = ko.observable();
        this.spoolManagerId = ko.observable();
        this.new = ko.observable(true);
        this.update(spoolData);
    };
    SpoolItem.prototype.update = function (data) {
        var updateData = data || {};
        this.code(updateData.code);
        this.gcodeText(updateData.gcodeText);
        this.databaseId(updateData.databaseId);
        this.displayName(updateData.displayName);
        this.spoolManagerId(updateData.spoolManagerId);
        if (this.databaseId() != null) {
            this.new(false);
        }
    };
    self.selectedSpool = new SpoolItem(null);
    this.initBinding = function (apiClient, webcamUrl) {
        self.apiClient = apiClient;
        self.webcamUrl = webcamUrl;
        self.spoolDialog = $("#dialog_qr_edit");
        self.apiClient.callGetAllSpools(function (responseData) {
            var allSpoolItems = ko.utils.arrayMap(
                responseData,
                function (spoolData) {
                    var result = self.createSpoolItemForTable(spoolData);
                    return result;
                }
            );
            self.spools(allSpoolItems);
        });
    };

    this._createSpoolItemForEditing = function () {
        self.selectedSpool = new SpoolItem(null);
        return self.selectedSpool;
    };

    this.createSpoolItemForTable = function (spoolData) {
        newSpoolItem = new SpoolItem(spoolData);
        return newSpoolItem;
    };
    this.showDialog = function (spoolItem) {
        self.selectedSpool.update(spoolItem);
        self.spoolDialog
            .modal({
                keyboard: false,
                clickClose: true,
                showClose: true,
                backdrop: "static",
            })
            .css({
                width: "auto",
                "margin-left": function () {
                    return -($(this).width() / 2);
                },
            });
    };
    this.scanQr = function () {

        self.apiClient.callLoadSpoolsByQuery(function (responseData) {
            var spoolItem = self.createSpoolItemForTable(responseData);
            self.selectedSpool.update(spoolItem);
            if (spoolItem.new() && spoolItem.code() != null) {
                self.spoolDialog
                    .modal({
                        keyboard: false,
                        clickClose: true,
                        showClose: true,
                        backdrop: "static",
                    })
                    .css({
                        width: "auto",
                        "margin-left": function () {
                            return -($(this).width() / 2);
                        },
                    });
            }else if(spoolItem.code() == null){
                self.showPopUp("error", 'Timeout', 'No code was found!');
            }
             else {
                self.apiClient.callSelectQr(
                    spoolItem.databaseId,
                    function (responseData) {
                        // var spoolItem = null;
                        // var spoolData = responseData["selectedSpool"];
                        // if (spoolData != null){
                        //     spoolItem = self.spoolDialog.createSpoolItemForTable(spoolData);
                        // }
                        // self.selectedSpoolForSidebar(spoolItem)
                        self.showPopUp("info", 'Selected QR', 'Code: '+spoolItem.code()+' selected for printing');
                    }
                );
            }
        });
    };
    this.updateSpools = function () {
        self.apiClient.callGetAllSpools(function (responseData) {
            var allSpoolItems = ko.utils.arrayMap(
                responseData,
                function (spoolData) {
                    var result = self.createSpoolItemForTable(spoolData);
                    return result;
                }
            );
            self.spools(allSpoolItems);
        });
    };
    this.saveSpool = function () {
        self.apiClient.callSaveSpool(
            self.selectedSpool,
            function (allPrintJobsResponse) {
                self.updateSpools();
                self.spoolDialog.modal("hide");
            }
        );
    };
    this.deleteSpool = function () {
        self.apiClient.callDeleteSpool(
            self.selectedSpool.databaseId()(),
            function (allPrintJobsResponse) {
                self.updateSpools();
                self.spoolDialog.modal("hide");
            }
        );
    };
}
