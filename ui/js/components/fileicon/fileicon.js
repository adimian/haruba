define(['ko', 'text!./fileicon.html'], function(ko, templateMarkup) {

    function FileIconViewModel(params) {
        var self = this;
        self.extension = params.extension;

        self.src = ko.observable('icons/' + self.extension + '.png');

    }
    return {
        viewModel: FileIconViewModel,
        template: templateMarkup
    };

});
