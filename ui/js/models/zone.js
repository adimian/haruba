define(function(require) {

    var Zone = function(data) {
        var self = this;
        var ko = require('ko');

        self.id = ko.observable(data.id);
        self.zone = ko.observable(data.name);
        self.url = ko.observable([router.urlfor('browse-page'), self.zone()].join('/'));
        self.path = ko.observable(data.path)

        self.create = function() {
            var requests = require('models/requests');
            var url = [requests.HARUBA_API, 'zone'].join('/');

            if (self.path().startsWith('/')){
                self.path(self.path().substring(1));
            }

            var zones = [{
                zone: self.zone(),
                path: self.path()
            }];

            return requests.post(url, {zones: zones}, true);
        }

    }

    var UserZone = function(data) {
        var self = this;
        var ko = require('ko');

        self.zone = ko.observable(data.zone);
        self.url = ko.observable([router.urlfor('browse-page'), self.zone()].join('/'));

        var path = router.currentRoute().params;
        var items = path.split('/');
        self.active = ko.observable(items[0] == self.zone());

        self.can_read = data.access.indexOf('read') >= 0;
        self.can_write = data.access.indexOf('write') >= 0;

    }

    return {
        'AdminZone': Zone,
        'UserZone': UserZone
    }
})
