define(['ko', 'text!./zones-bar.html'], function(ko, templateMarkup) {

    function ZonesBarViewModel(params) {
        var self = this;
        self.available_zones = ko.observableArray([]);

        self.refresh = function(){
            var requests = require('models/requests');
            var zone = require('models/zone');
            requests.get(requests.HARUBA_API + '/myzones').success(function(data) {
                ko.utils.arrayForEach(data, function(info) {
                    self.available_zones.push(new zone.UserZone(info));
                });
            });
        }

        self.refresh();
    }
    return {
        viewModel: ZonesBarViewModel,
        template: templateMarkup
    };

});
