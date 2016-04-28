define(function(require) {
    var jquery = require('jquery'),
        bootstrap = require('bootstrap'),
        ko = require('ko'),
        text = require('text'),
        user = require('models/user'),
        file = require('models/file'),
        zone = require('models/zone'),
        dropzone = require('dropzone'),
        server = require('models/server'),
        cookies = require('cookies-js'),
        router = require('./router');

    // support for CORS queries
    $.ajaxSetup({
        xhrFields: {
            withCredentials: true
        }
    });

    // register components [components:register]
    ko.components.register('permissions-panel', {require: 'components/permissions-panel/permissions-panel'});
    ko.components.register('manage-page', {require: 'components/manage-page/manage-page'});
    ko.components.register('profile-page', {require: 'components/profile-page/profile-page'});
    ko.components.register('fileicon', {require: 'components/fileicon/fileicon'});
    ko.components.register('filelist', {require: 'components/filelist/filelist'});
    ko.components.register('breadcrumbs', {require: 'components/breadcrumbs/breadcrumbs'});
    ko.components.register('browsing-pane', {require: 'components/browsing-pane/browsing-pane'});
    ko.components.register('zones-bar', {require: 'components/zones-bar/zones-bar'});
    ko.components.register('browse-page', {require: 'components/browse-page/browse-page'});
    ko.components.register('nav-bar', {require: 'components/nav-bar/nav-bar'});
    ko.components.register('login-page', {require: 'components/login-page/login-page'});

    // register application singletons
    window.current_user = new user.CurrentUser();
    window.server_options = new server.ServerOptions();
    window.router = router;

    // get knockout started
    ko.applyBindings({
        route: router.currentRoute,
    });

    window.current_user.restore();

});
