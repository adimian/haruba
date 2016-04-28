define(['ko', 'text!./browsing-pane.html'], function(ko, templateMarkup) {

    function BrowsingPaneViewModel(params) {
        var self = this;
        self.path = router.currentRoute().params;
    }
    return {
        viewModel: BrowsingPaneViewModel,
        template: templateMarkup
    };

});
