define(function(require) {

    CAN_VIEW = [
        'jpg', 'png', 'bmp', 'gif', 'pdf', 'txt', 'csv',
        'py', 'dat', 'ini', 'log', 'condorlog', 'err', 'json', 'gms',
        'lst', 'asc', 'pf', 'opt', 'solverlog', 'modellog', 'md'
    ];


    var File = function(data) {
        var self = this;
        var ko = require('ko');
        var base64 = require('models/base64')

        self.name = ko.observable(data.name);
        self.uri = ko.observable(data.uri);
        self.size = ko.observable(data.size);
        self.path = ko.observable(data.path);
        self.numerical_size = ko.observable(data.numeric_size);
        self.extension = data.extension;
        self.modified = ko.observable(data.modif_date);
        self.browsable = ko.observable(false);
        self.download_link = ko.observable(data.download_link);
        self.is_dir = self.extension == 'folder';
        self.selected = ko.observable(false);

        self.id = ko.pureComputed(function(){
            var name = base64.Base64.encode(self.name());
            return 'item-name-' + name;
        }, this);

        self.url = ko.observable('')
        if (self.extension == 'folder') {
            self.url([window.location, self.name()].join('/'));
            self.browsable(true);
        }

        if (CAN_VIEW.indexOf(self.extension) >= 0) {
            self.url(self.download_link() + '?view=1');
            self.browsable(true);
        }

        if (self.is_dir) {
            self.size = '-';
        }

        self.delete = function(data) {
            var requests = require('models/requests');
            return requests.delete(self.uri());
        }

        self.rename = function(new_name) {
            var requests = require('models/requests');
            return requests.put(self.uri(), {rename_to: new_name}).success(function(data){
                // update linked URIs
                self.uri(self.uri().replace(self.name(), new_name));
                self.download_link(self.download_link().replace(self.name(), new_name));
                // finally update name
                self.name(new_name);
            });
        }

        self.download = function(data) {
            window.location = self.download_link();
        }

        self.create = function(data){
            var requests = require('models/requests');
            var url = [requests.HARUBA_API, 'files', self.path(), data].join('/')
            return requests.post(url)
        }

    }

    return {
        'File': File
    };
})
