var ServerOptions = function() {
    var self = this;
    self.use_totp = ko.observable();
    self.auth_token_name = ko.observable();
    self.version = ko.observable('loading ...');
    $.getJSON(SIGIL_BASE_URL + SIGIL_API_URL + '/options', function(data) {
        self.use_totp(data.use_totp == "1");
        self.auth_token_name(data.auth_token);
        self.version(data.version);
    });
};