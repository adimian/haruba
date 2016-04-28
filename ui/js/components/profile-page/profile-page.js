define(['ko', 'text!./profile-page.html'], function(ko, templateMarkup) {

    function ProfilePageViewModel(params) {
        var self = this;

        self.user = current_user;

        self.permissions = ko.observableArray([]);

    }
    return {
        viewModel: ProfilePageViewModel,
        template: templateMarkup
    };

});
