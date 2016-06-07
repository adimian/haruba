define(function(require) {

    var ServerOptions = function() {
        var ko = require('ko');
        var requests = require('models/requests');
        var self = this;

        self.use_totp = ko.observable();
        self.auth_token_name = ko.observable();
        self.version = ko.observable('loading ...');
        self.application_name = ko.observable('');
        requests.get(requests.SIGIL_API + '/options').success(function(data) {
            self.use_totp(data.use_totp == "1");
            self.auth_token_name(data.auth_token);
            self.version(data.version);
            self.application_name(data.application_name);
            document.title = self.application_name();
        });

    };

    return {ServerOptions: ServerOptions};
});
