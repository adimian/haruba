define(function(require) {

    var User = function() {
        var ko = require("ko");

        var self = this;
        self.active = ko.observable();
        self.first_name = ko.observable();
        self.last_name = ko.observable();
        self.display_name = ko.observable();
        self.username = ko.observable();
        self.api_key = ko.observable();
        self.provides = ko.observableArray([]);

        self.load = function(data) {
            self.display_name(data.displayname);
            self.first_name(data.firstname);
            self.last_name(data.lastname);
            self.active(data.active);
            self.username(data.username);
            self.api_key(data.api_key);
            self.provides(data.provides);
        }

        self._has = function(zone)  {
            var result = [];
            ko.utils.arrayForEach(self.provides(), function(item) {
                if (item[2] == zone) {
                    result.push(item[1]);
                }
            })
            return result;
        }

        self.has_write = function(zone) {
            return this._has(zone).indexOf('write') >= 0;
        }

        self.access = function(zone) {
            return this._has(zone).sort().join(', ');
        };

        self.matches = function(query) {
            return ([
                self.username().toLowerCase(),
                self.first_name().toLowerCase(),
                self.last_name().toLowerCase()
            ].join('').indexOf(query) >= 0)
        }

        self._perm = function(what, zone, permission) {
            var permissions = [];

            // there is no write-only permission
            if (what == 'grant' && permission == 'write') {
                permissions.push('read');
            } else if (what == 'withdraw' && permission == 'read') {
                permissions.push('write');
            }

            if (!permissions.indexOf(permission) >= 0)  {
                permissions.push(permission);
            }

            var requests = require('models/requests');
            var url = [requests.HARUBA_API, 'permissions'].join('/');

            var needs = [];

            ko.utils.arrayForEach(permissions, function(perm) {
                var perm = ['zone', perm, zone]
                needs.push(perm);
            })

            var payload = {
                permissions: [{
                    username: self.username(),
                    needs: needs
                }]
            }

            if (what == 'grant')  {
                return requests.post(url, payload, true);
            } else {
                return requests.delete(url, payload, true);
            }
        }

        self.grant = function(zone, permission)  {
            return self._perm('grant', zone, permission);
        }

        self.withdraw = function(zone, permission) {
            return self._perm('withdraw', zone, permission);
        }

        self.toggle_readonly = function(zone)  {
            if (self.has_write(zone)) {
                self.withdraw(zone, 'write');
            } else {
                self.grant(zone, 'write');
            }
        }

    };

    var CurrentUser = function() {
        var ko = require("ko");
        var noty = require("noty");

        var self = this;
        self.password = ko.observable();
        self.totp = ko.observable();
        self.is_authenticated = ko.observable();
        self.is_admin = ko.observable();

        self.is_authenticated.subscribe(function(is_authenticated) {
            if (!is_authenticated) {
                window.router.go('login-page');
            } else {
                window.router.go('browse-page');
            }
        })

        self.load_details = function() {
            var requests = require('models/requests');
            requests.get(requests.HARUBA_API + '/user/details').success(function(data) {
                self.load(data);
            });
        };

        self._has = function(zone)  {
            var result = [];
            ko.utils.arrayForEach(self.provides(), function(item) {
                if (item.zone == zone) {
                    result = item.access;
                }
            })
            return result;
        }

        self.restore = function() {
            var requests = require('models/requests');
            requests.get(requests.HARUBA_API + '/login').success(function(data) {
                self.is_authenticated(data.authenticated);
                self.is_admin(data.admin);
                self.password(null);

                self.load_details();
            });
        };

        self.logout = function(force) {
            var requests = require('models/requests');
            if (force)  {
                self.is_admin(false);
                self.is_authenticated(false);
            } else {
                requests.get(requests.HARUBA_API + '/logout').success(function(data) {
                    self.is_admin(false);
                    self.is_authenticated(false);
                }).error(function(data) {});
            }
        };

        self.login = function() {
            var creds = {
                login: self.username(),
                password: self.password(),
                totp: self.totp()
            };

            var requests = require('models/requests');
            requests.post(requests.HARUBA_API + '/login', creds).success(
                function(data) {
                    self.restore();
                }).error(function(data) {

                var n = window.noty({
                    text: data.responseJSON ? data.responseJSON.message : 'unknown error',
                    layout: 'topCenter',
                    type: 'error'
                });
            });
        };

        self.send_sms = function() {
            var requests = require('models/requests');
            var url = [requests.SIGIL_API, 'user', '2fa', 'sms'].join('/')
            requests.post(url, {
                username: self.username()
            }).success(function(data) {
                noty({
                    text: 'SMS sent !',
                    timeout: 3500,
                    layout: 'topCenter',
                    type: 'success',
                });
            })
        };

    }
    CurrentUser.prototype = new User();

    return {
        'User': User,
        'CurrentUser': CurrentUser
    };
})
