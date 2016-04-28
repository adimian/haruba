define(['ko', 'text!./login-page.html'], function(ko, templateMarkup) {

    function LoginPageViewModel(params) {
        var self = this;
        self.login = function(){
            current_user.login();
        }

        self.recover = function(){
            var requests = require('models/requests');
            var url = [requests.SIGIL_UI, 'recover.html'].join('/')
            console.log(url);
            window.location = url;
        }
    }
    return {
        viewModel: LoginPageViewModel,
        template: templateMarkup
    };

});
