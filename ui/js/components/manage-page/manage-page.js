define(['ko', 'text!./manage-page.html'], function(ko, templateMarkup) {

    function ManagePageViewModel(params) {
        var self = this;
        var ko = require('ko');
        var requests = require('models/requests');
        var zone = require('models/zone');

        self.new_name = ko.observable('');
        self.new_path = ko.observable('');

        self.selected_zone = ko.observable();

        self.new_path.subscribe(function(val){
            if (val.startsWith('/')){
                self.new_path(self.new_path().substring(1));
            }
        }, this);

        self.zones = ko.observableArray([]);

        self.refresh = function() {
            var url = [requests.HARUBA_API, 'zone'].join('/');
            self.zones([]);
            requests.get(url).success(function(data) {
                ko.utils.arrayForEach(data, function(info) {
                    self.zones.push(new zone.AdminZone(info));
                })
            })
        }

        self.refresh();

        self.create = function() {
            var created = new zone.AdminZone({
                name: self.new_name(),
                path: self.new_path()
            });

            created.create().success(function(data){
                self.new_name('');
                self.new_path('');
                self.refresh();
            })
        }

        self.edit_permissions = function(item){
            self.selected_zone(item);
        }

    }
    return {
        viewModel: ManagePageViewModel,
        template: templateMarkup
    };

});
