define(['ko', 'text!./breadcrumbs.html'], function(ko, templateMarkup) {

    function BreadcrumbsViewModel(params) {
        var self = this;
        var browseurl = router.urlfor('browse-page');
        self.crumbs = ko.observableArray([]);
        var items = params.path.split('/');
        var buffer = [];
        ko.utils.arrayForEach(items, function(item){
            buffer.push(item);
            var crumb = {
                name: item,
                url: [browseurl , buffer.join('/')].join('/'),
                active: item === items[items.length-1]
            };
            self.crumbs.push(crumb);
        });

    }
    return {
        viewModel: BreadcrumbsViewModel,
        template: templateMarkup
    };

});
