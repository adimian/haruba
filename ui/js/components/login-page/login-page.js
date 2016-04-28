define(['ko', 'text!./login-page.html'], function(ko, templateMarkup) {

    function LoginPageViewModel(params) {
        var self = this;
        self.login = function(){
            current_user.login();
        }

        self.recover = function(){
            var requests = require('models/requests');
            window.location = requests.SIGIL_RECOVER_URL;
        }
    }
    return {
        viewModel: LoginPageViewModel,
        template: templateMarkup
    };

});
