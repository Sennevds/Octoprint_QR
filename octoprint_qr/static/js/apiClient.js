function QrAPIClient(pluginId, baseUrl) {
    this.pluginId = pluginId;
    this.baseUrl = baseUrl;

    // see https://gomakethings.com/how-to-build-a-query-string-from-an-object-with-vanilla-js/
    var _buildRequestQuery = function (data) {
        // If the data is already a string, return it as-is
        if (typeof data === "string") return data;

        // Create a query array to hold the key/value pairs
        var query = [];

        // Loop through the data object
        for (var key in data) {
            if (data.hasOwnProperty(key)) {
                // Encode each key and value, concatenate them into a string, and push them to the array
                query.push(
                    encodeURIComponent(key) +
                        "=" +
                        encodeURIComponent(data[key])
                );
            }
        }
        // Join each item in the array with a `&` and return the resulting string
        return query.join("&");
    };

    var _addApiKeyIfNecessary = function (urlContext) {
        if (UI_API_KEY) {
            urlContext = urlContext + "?apikey=" + UI_API_KEY;
        }
        return urlContext;
    };
    this.callGetAllSpools = function (responseHandler) {
        urlToCall = this.baseUrl + "plugin/" + this.pluginId + "/GetSpools";
        $.ajax({
            url: urlToCall,
            type: "GET",
        }).always(function (data) {
            responseHandler(data);
        });
    };
    this.callLoadSpoolsByQuery = function (responseHandler) {
        urlToCall = this.baseUrl + "plugin/" + this.pluginId + "/ReadQR";
        $.ajax({
            //url: API_BASEURL + "plugin/"+PLUGIN_ID+"/loadPrintJobHistory",
            url: urlToCall,
            type: "GET",
        }).always(function (data) {
            responseHandler(data);
            //shoud be done by the server to make sure the server is informed countdownDialog.modal('hide');
            //countdownDialog.modal('hide');
            //countdownCircle = null;
        });
    };
    this.callSaveSpool = function (spoolItem, responseHandler) {
        jsonPayload = ko.toJSON(spoolItem);
        $.ajax({
            url: this.baseUrl + "plugin/" + this.pluginId + "/saveSpool",
            dataType: "json",
            contentType: "application/json; charset=UTF-8",
            data: jsonPayload,
            type: "PUT",
        }).always(function (data) {
            responseHandler();
        });
    };
    this.callDeleteSpool = function (databaseId, responseHandler) {
        $.ajax({
            url:
                this.baseUrl +
                "plugin/" +
                this.pluginId +
                "/deleteSpool/" +
                databaseId,
            type: "DELETE",
        }).always(function (data) {
            responseHandler();
        });
    };
    this.callSelectQr = function (databaseId, responseHandler) {
        if (databaseId == null) {
            databaseId = -1;
        }
        var jsonPayload = '{"databaseId":' + databaseId() + "}";
        $.ajax({
            url: this.baseUrl + "plugin/" + this.pluginId + "/selectSpool",
            dataType: "json",
            contentType: "application/json; charset=UTF-8",
            data: jsonPayload,
            type: "PUT",
        }).always(function (data) {
            responseHandler();
        });
    };
}
