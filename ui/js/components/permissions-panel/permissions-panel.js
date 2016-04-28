define(['ko', 'text!./permissions-panel.html'], function(ko, templateMarkup) {

    var MIN_SEARCH_LENGTH = 3;

    function PermissionsPanelViewModel(params) {
        var self = this;

        self.zone = ko.observable(params.zone);
        self.users = ko.observableArray([]);
        self.loading_message = ko.observable();
        self.linked_users = ko.observableArray([]);
        self.query = ko.observable('');

        var requests = require('models/requests');
        var user = require('models/user');

        self.zone_name = ko.pureComputed(function(){
            return self.zone().zone();
        })

        self.refresh = function() {
            $("#add-user-form").hide();
            self.loading_message('Loading users, this can take a few seconds');
            self.linked_users([]);
            self.users([]);
            var zone_name = self.zone_name();
            var url = [requests.HARUBA_API, 'permissions'].join('/');
            requests.get(url).success(function(data) {
                ko.utils.arrayForEach(data.users, function(item) {
                    var u = new user.User();
                    u.load(item);
                    self.users.push(u);
                    if (u.access(zone_name))  {
                        self.linked_users.push(u);
                    }
                });
                self.loading_message('');
                $("#add-user-form").show();
                $("#username").focus();
            });
        }

        self.refresh();

        self.candidates = ko.pureComputed(function() {
            var result = [];
            var querytext = self.query().toLowerCase();
            if (querytext.length >= MIN_SEARCH_LENGTH) {
                ko.utils.arrayForEach(self.users(), function(user) {
                    if (user.matches(querytext))  {
                        result.push(user);
                    }
                });
            }
            return result.sort();
        })

        self.add_user = function(user) {
            self.query('');
            user.grant(self.zone_name(), 'write').success(function(data){
                user.provides.push(['zone', 'write', self.zone_name()]);
                user.provides.push(['zone', 'read', self.zone_name()]);
                self.linked_users.push(user);
            })
        };

        self.remove_user = function(user) {
            user.withdraw(self.zone_name(), 'read').success(function(data){
                self.linked_users.remove(user);
            })
        };

        self.toggle_readonly = function(user) {
            if (user.has_write(self.zone_name())){
                user.withdraw(self.zone_name(), 'write').success(function(data){
                    self.refresh();
                })
            } else {
                user.grant(self.zone_name(), 'write').success(function(data){
                    self.refresh();
                })
            }
        }

    }
    return {
        viewModel: PermissionsPanelViewModel,
        template: templateMarkup
    };

});
