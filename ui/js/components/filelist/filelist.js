define(['ko', 'text!./filelist.html'], function(ko, templateMarkup) {

    function FileListViewModel(params) {
        var self = this;
        self.path = ko.observable(params.path);
        self.headers = ko.observableArray(['Name', '', 'Size', 'Modified']);
        self.content = ko.observableArray([]);
        self.query = ko.observable(null);

        self.multiselect = ko.observable(true);
        self.show_paste = ko.observable(false);
        self.show_up = ko.observable(self.path().split('/').length - 1);

        self.parent_url = ko.pureComputed(function() {
            var crumbs = self.path().split('/');
            var parent = crumbs.slice(0, crumbs.length - 1);
            return [router.urlfor('browse-page'), parent].join('/');
        }, this);

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

            if (!selection.paths.length) {
                return;
            }

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
            self.show_paste(true);
        }

        self.mass_cut = function() {
            self._copy_cut('cut');
        }

        self.mass_copy = function() {
            self._copy_cut('copy');
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
                self.show_paste(false);
                self.reload();
            })

        }

        self._post_ajax_download = function(url, data, input_name) {
            var $iframe,
                iframe_doc,
                iframe_html;

            if (($iframe = $('#download_iframe')).length === 0) {
                $iframe = $("<iframe id='download_iframe'" +
                    " style='display: none' src='about:blank'></iframe>"
                ).appendTo("body");
            }

            iframe_doc = $iframe[0].contentWindow || $iframe[0].contentDocument;
            if (iframe_doc.document) {
                iframe_doc = iframe_doc.document;
            }

            iframe_html = "<html><head></head><body><form method='POST' action='" +
                url + "'>" +
                '<input type=hidden name="' + input_name + '" value="' +
                data + '"/></form>' +
                "</body></html>";

            iframe_doc.open();
            iframe_doc.write(iframe_html);
            $(iframe_doc).find('form').submit();
        }

        self.mass_download = function() {
            var selection = self._mass_selection();
            if (!selection.paths.length) {
                return;
            }
            var filenames = [];
            ko.utils.arrayForEach(selection.files, function(item) {
                filenames.push(item.name());
            })

            var requests = require('models/requests');
            var url = [requests.HARUBA_API, 'download', self.path()].join('/');

            self._post_ajax_download(url, filenames.join(','), 'filenames');

        }

        self.mass_delete = function() {
            var selection = self._mass_selection();
            if (!selection.paths.length) {
                return;
            }
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

        self.load_content = function(item) {
            $('#contentmodal iframe').attr('src', item.url());

            $('#contentmodal').modal('show');
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
