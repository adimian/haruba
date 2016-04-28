define(function(require) {

    var onerror = function(error) {

        if (error.status != 404) {
            console.log(error);
        }

        if (error.status == 404 && error.responseJSON){
            noty({
                text: error.responseJSON.message,
                type: 'error',
                timeout: 3500
            });
        }

        if (error.status == 401 && current_user.is_authenticated()) {
            noty({
                text: 'Your session has expired, please sign-in again',
                type: 'error',
                timeout: 3500
            });
            current_user.logout(true);
        }

        if (error.status == 400) {
            noty({
                text: 'The server encountered an error while processing your request',
                type: 'error',
                timeout: 3500
            });
        }

        if (error.status == 500) {
            noty({
                text: 'The server encountered an error, this page might not display properly',
                type: 'error',
                timeout: 3500
            });
        }

        if (error.status == 403) {
            noty({
                text: "You don't have sufficient permissions to perform this action",
                type: 'error',
                timeout: 3500
            });
        }

    }

    var get = function(url, payload)  {
        return $.ajax({
            url: url,
            data: payload,
            method: 'GET',
        }).error(onerror);
    };

    var post = function(url, payload, json)  {
        if (json || false) {
            return $.ajax({
                url: url,
                contentType: 'application/json',
                dataType: 'json',
                data: JSON.stringify(payload),
                method: 'POST'
            }).error(onerror);
        } else {
            return $.ajax({
                url: url,
                data: payload,
                method: 'POST'
            }).error(onerror);
        }

    };

    var deleteme = function(url, payload, json)  {
        if (json || false) {
            return $.ajax({
                url: url,
                contentType: 'application/json',
                dataType: 'json',
                data: JSON.stringify(payload),
                method: 'DELETE'
            }).error(onerror);
        } else {
            return $.ajax({
                url: url,
                data: payload,
                method: 'DELETE'
            }).error(onerror);
        }

    };

    var putme = function(url, payload)  {
        return $.ajax({
            url: url,
            data: payload,
            method: 'PUT'
        }).error(onerror);
    };

    return {
        SIGIL_API: 'http://local.docker/sigil-api',
        SIGIL_UI: 'http://local.docker/sigil',
        HARUBA_API: 'http://local.docker/haruba-api',
        SIGIL_TOKEN_HEADER: 'Sigil-Token',
        TOKEN_PLACEHOLDER: 'placeholder',
        get: get,
        post: post,
        delete: deleteme,
        put: putme
    }
})
