define(['ko', 'text!./nav-bar.html'], function(ko, templateMarkup) {

    function NavBarViewModel(params) {
        this.route = params.route;
    }
    return {
        viewModel: NavBarViewModel,
        template: templateMarkup
    };

});
