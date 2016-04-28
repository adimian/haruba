define(['ko', 'text!./filelist.html'], function(ko, templateMarkup) {

    function FileListViewModel(params) {
        var self = this;
        self.path = ko.observable(params.path);
        self.headers = ko.observableArray(['Name', '', 'Size', 'Modified']);
        self.content = ko.observableArray([]);
        self.query = ko.observable(null);

        self.multiselect = ko.observable(false);

        self.list = ko.computed(function() {
            var query = self.query();
            if (!query) {
                return self.content();
            } else {
                return ko.utils.arrayFilter(self.content(), function(item) {
                    query = query.toLowerCase();
                    if (item.name().toLowerCase().indexOf(query) > -1) {
                        return true;
                    }
                });
            }
        }, this);

        self.reload = function() {
            var requests = require('models/requests');
            var root = requests.HARUBA_API + '/files'
            var folder_path = [root, self.path()].join('/')
            var file = require('models/file');

            self.content([]);

            requests.get(folder_path).success(function(data) {
                ko.utils.arrayForEach(data, function(info) {
                    self.content.push(new file.File(info));
                });
                self.sort('name');
            });
        }

        if (self.path()) {
            // trigger initial load
            self.reload();
        }

        self.sort_asc = false;
        self.sort = function(column) {
            var sortkey = column.toLowerCase();

            // sort size based on the number of bytes
            if (sortkey == 'size') {
                sortkey = 'numerical_size';
            }

            self.sort_asc = !self.sort_asc;

            self.content.sort(function(left, right) {
                if (left['is_dir'] !== right['is_dir']) {
                    return (left['is_dir'] > right['is_dir'] ? -1 : 1);
                } else {
                    var left_name = left[sortkey]();
                    var right_name = right[sortkey]();

                    // case-insensitive sort
                    if (sortkey == 'name') {
                        left_name = left_name.toLowerCase();
                        right_name = right_name.toLowerCase();
                    }

                    if (self.sort_asc) {
                        return left_name == right_name ? 0 : (left_name < right_name ? -1 : 1);
                    } else {
                        return left_name == right_name ? 0 : (left_name > right_name ? -1 : 1);
                    }
                }
            })
        };

        self.delete = function(item)  {
            noty({
                layout: 'center',
                text: 'Do you want to delete ' + item.name() + '?',
                buttons: [{
                    addClass: 'btn btn-primary',
                    text: 'Yes',
                    onClick: function($noty) {
                        item.delete().success(function(data) {
                            self.content.remove(item);
                        })
                        $noty.close();
                    }
                }, {
                    addClass: 'btn btn-danger',
                    text: 'No',
                    onClick: function($noty) {
                        $noty.close();
                    }
                }]
            });
        }

        self.rename = function(item) {
            var input = $('<input type="text" class="form-control fader-input" value="' + item.name() + '"></input>')
            var anchor = $('#' + item.id());
            var css = {
                width: anchor.parent().width() * 0.4,
                display: 'inline'
            };

            anchor.hide();
            input.appendTo(anchor.parent());
            input.css(css);
            input.focus();
            input.select();

            input.keyup(function(e) {
                // Enter pressed
                if (e.keyCode == 13) {
                    var new_value = input.val();
                    if (new_value !== item.name()) {
                        if (item.uri()) {
                            item.rename(new_value);
                        } else {
                            item.create(new_value).success(function(data) {
                                self.reload();
                            })
                        }
                    }
                    input.remove();
                    anchor.show();
                }

                // Esc pressed
                if (e.keyCode == 27) {
                    input.remove();
                    anchor.show();
                }
            });
        }

        self.toggle_multiselect = function() {
            self.multiselect(!self.multiselect());
        }

        self.select_all = function() {
            ko.utils.arrayForEach(self.content(), function(item) {
                item.selected(true);
            })
        }

        self.select_none = function() {
            ko.utils.arrayForEach(self.content(), function(item) {
                item.selected(false);
            })
        }

        self._mass_selection = function() {
            var files = [];
            var paths = [];
            ko.utils.arrayForEach(self.content(), function(item) {
                if (item.selected()) {
                    paths.push('/' + item.path());
                    files.push(item);
                }
            })
            return {
                paths: paths,
                files: files
            };
        }

        self._copy_cut = function(action) {
            var cookies = require('cookies-js');
            var selection = self._mass_selection();
            cookies('clipboard', JSON.stringify(selection.paths), {
                expires: 300
            });
            cookies('clipboard-action', action, {
                expires: 300
            });
            noty({
                text: selection.paths.length + ' files copied to clipboard',
                type: 'information',
                timeout: 3500
            });
        }

        self.mass_cut = function() {
            self._copy_cut('cut');
            self.multiselect(false);
        }

        self.mass_copy = function() {
            self._copy_cut('copy');
            self.multiselect(false);
        }

        self.mass_paste = function() {
            var cookies = require('cookies-js');
            var paths = cookies('clipboard');
            var action = cookies('clipboard-action');

            if (paths === undefined || !paths.length) {
                noty({
                    text: 'Clipboard is empty',
                    type: 'error',
                    timeout: 3500
                });
                return;
            }

            if (action === undefined || !action.length) {
                noty({
                    text: 'No clipboard action defined',
                    type: 'error',
                    timeout: 3500
                });
                return;
            }

            var command = {
                type: action,
                from: JSON.parse(paths),
                to: '/' + self.path()
            };


            var requests = require('models/requests');
            var url = [requests.HARUBA_API, 'command', self.path()].join('/');

            requests.post(url, {
                commands: [command]
            }, true).success(function(data) {
                self.reload();
            })

        }

        self.mass_delete = function() {
            var selection = self._mass_selection();
            noty({
                layout: 'center',
                text: 'Do you want to delete ' + selection.files.length + ' files ?',
                buttons: [{
                    addClass: 'btn btn-primary',
                    text: 'Yes',
                    onClick: function($noty) {
                        ko.utils.arrayForEach(selection.files, function(item) {
                            item.delete().success(function(data) {
                                self.content.remove(item);
                            })
                        })
                        self.multiselect(false);
                        $noty.close();
                    }
                }, {
                    addClass: 'btn btn-danger',
                    text: 'No',
                    onClick: function($noty) {
                        self.multiselect(false);
                        $noty.close();
                    }
                }]
            });
        }

        self.new_folder = function() {
            var file = require('models/file');
            var item = new file.File({
                extension: 'folder',
                url: '',
                uri: '',
                download_link: '',
                name: '',
                path: self.path()
            });
            self.content.unshift(item);
            self.rename(item);
        }

        // define the dropzone
        var requests = require('models/requests');
        var dropzone = require('dropzone');
        var upload_url = [requests.HARUBA_API, 'upload', params.path].join('/');

        var drop_zone = new dropzone(".file-upload-container", {
            url: upload_url,
            clickable: '.upload-file-prompt',
            paramName: function(n) {
                return "files";
            },
            uploadMultiple: true,
            withCredentials: true,
            parallelUploads: 5,
            maxFilesize: 2000,
            previewsContainer: ".dropzone-previews"
        });
        drop_zone.on("successmultiple", function(file) {
            self.reload();
        });

    }
    return {
        viewModel: FileListViewModel,
        template: templateMarkup
    };

});
