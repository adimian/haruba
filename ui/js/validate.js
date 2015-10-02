"use strict"
var UserAccount = function() {
    var self = this;
    self.username = ko.observable();
    self.password = ko.observable();
    self.totp = ko.observable();
};

var LoginAccountApplication = function() {
    var self = this;
    self.server_options = new ServerOptions();
    self.user_account = new UserAccount();

    self.sms_message = ko.observable();
    self.error_message = ko.observable();

    self.send_sms = function() {
    	if(!self.user_account.username()){
    		self.error_message("You must provide a username to be able to send and sms")
    	}
    	
        var data = {
            username: self.user_account.username()
        };

        var success = function(data) {
            self.sms_message('SMS sent !');
        };

        self.sms_message("Sending a SMS right now ...")
        $.ajax({
            method: "POST",
            dataType: "json",
            url: SIGIL_API_URL + '/user/2fa/sms',
            data: data,
            success: success
        }).error(function(data) {
        	self.sms_message("")
            self.error_message('We are unable to send an SMS: ' + data.responseJSON.message);
        });

    };

    self.login = function() {
    	hclient.login(self.user_account.username(), 
    				  self.user_account.password(),
    				  self.user_account.totp())
    }

};

var init_login = function() {
    var app = new LoginAccountApplication();
    ko.applyBindings(app, $("#login-panel")[0]);
    window.login_app = app
};
