define(function(require){

    var URLRouter = function(config) {

        // director is old and does not support AMD
        // so it's using the 'window' object to register himself
        // but we still need to require() it.
        var director = require('director');
        var ko = require('ko');
        var cookies = require('cookies-js')

        var self = this;
        var router = window.Router().configure({
            'recurse': false,
            'notfound': function(data){
                router.setRoute(config.startup)
            }
        });

        self.root = window.location.pathname;

        self.currentRoute = ko.observable({});

        ko.utils.arrayForEach(config.routes, function(route) {
            router.on(route.url, function(requestParams) {
                self.currentRoute(ko.utils.extend({
                    params: requestParams
                }, route.params));
            })
        })

        router.init(config.startup);

        self.go = function(route){
            window.location = self.urlfor(route);
        };

        self.already = function(route) {
            return self.currentRoute().page == route;
        }

        self.urlfor = function(page, params) {
            var url = null;
            ko.utils.arrayForEach(config.routes, function(route) {
                if (route.params.page == page){
                    url = route.root || route.url;
                }
            });
            var result = [self.root, '#', url].join('/');
            while (result.search('//') >= 0){
                result = result.replace('//', '/');
            }
            return result;
        };
    };


    var config = {
        routes: [{
            url: '/login',
            params: {
                page: 'login-page'
            }
        }, {
            url: '/profile',
            params: {
                page: 'profile-page'
            }
        }, {
            url: '/browse/?((\w|.)*)',
            root: '/browse',
            params: {
                page: 'browse-page'
            }
        }, {
            url: '/manage',
            params: {
                page: 'manage-page'
            }
        }],
        startup: '/browse'
    };

    return new URLRouter(config);
});
