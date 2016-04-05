var current_zone = "";
var current_path = "";
var ctrl = navigator.platform.toUpperCase().indexOf('MAC')>=0?'Cmd':'Ctrl';

function OptionAction(click_handler, glyph_icon, text, hotkey, divider, read, write){
	this.click_handler = click_handler;
	this.glyph_icon = "glyphicon option-icon " + glyph_icon;
	this.text = text;
	this.hotkey = hotkey;
	// do you need read rights for this action
	this.read = read;
	// do you need write rights for this action
	this.write = write;
	// appends a divider when set to true
	this.divider = divider;
}
OptionAction.prototype.can_show = function(has_read, has_write, item){
	value = true;
	if(this.read){
		value = has_read()
	}
	if(this.write){
		value = value && has_write()
	}
	if(item && this.text == " Unzip"){
		var ext = item.name.split('.').pop()
		if(ext == "zip"){
			value = value && true
		}else{
			value = value && false
		}
	}
	return value;
}

function ZoneViewModel(){
	var self = this;
	self.query = ko.observable('');
	self.zones = ko.observable();
	self.loading = ko.observable(false);
	self.folder = ko.observableArray();
	self.folder_display = ko.computed(function() {
        var searchbar = self.query();
        if (!searchbar) {
            return this.folder();
        } else {
            return ko.utils.arrayFilter(this.folder(), function(item) {
                searchbar = searchbar.toLowerCase();
                if(item.name.toLowerCase().indexOf(searchbar) > -1){
                	return true;
                }
            });
        }
    }, this);
	self.complete_folder = ko.observableArray();
	self.selected_zone = ko.observable();
	self.selected_zone_name = ko.observable();
	self.breadcrumbs = ko.observableArray();
	self.selected_items = ko.observableArray();
	self.cut_candidates = ko.observableArray();
	self.copy_candidates = ko.observableArray();
	self.cut_paths = ko.observableArray();
	self.copy_paths = ko.observableArray();
	self.has_read = ko.computed(function(){
		if(this.selected_zone()){			
			return this.selected_zone().access.indexOf('read')>-1;
		}
		return false;
	}, this);
	self.has_write = ko.computed(function(){
		if(this.selected_zone()){
			return this.selected_zone().access.indexOf('write')>-1;
		}
		return false;
	}, this);
	hclient.zone.myzones(self.zones)
	self.current_user = new CurrentUser()
	
	//behaviour
	self.load_zone = load_zone;
	self.go_to_folder = go_to_folder;
	self.go_to_breadcrumb = go_to_breadcrumb;
	self.logout = function(){hclient.logout()};
	self.sort_items = sort_items;
	self.select_item = select_item;
	self.delete_items = delete_items;
	self.prepare_copy = prepare_copy;
	self.prepare_cut = prepare_cut;
	self.execute_copy_cut = execute_copy_cut;
	self.download_selected = download_selected;
	self.option_upload = option_upload;
	self.delete_single = function(item, evt){confirm_delete([item], [item.name]);};
	self.download_single = function(item, evt){hclient.download.single(current_zone, current_path + "/" + item.name);};
	self.rename = rename;
	self.create_folder = create_folder;
	self.unzip = unzip;
	self.load_admin = function(){$.get("/admin.html", function(data){ $("body").html(data);})};
	self.load_profile = function(){$.get("/profile.html", function(data){ $("body").html(data);})};
	
	self.options = ko.observableArray([new OptionAction(self.option_upload, 'glyphicon-upload', ' Upload', "", false, true, true),
	                                   new OptionAction(self.create_folder, 'glyphicon-plus-sign', ' New Folder', "", true, true, true),
	                                   new OptionAction(self.prepare_copy, 'glyphicon-copy', ' Copy', ctrl+"+C", false, true, true),
	                                   new OptionAction(self.prepare_cut, 'glyphicon-scissors', ' Cut', ctrl+"+X", false, true, true),
	                                   new OptionAction(self.execute_copy_cut, 'glyphicon-paste', ' Paste', ctrl+"+V", true, true, true),
	                                   new OptionAction(self.delete_items, 'glyphicon-remove', ' Delete', 'Del', false, true, true),
	                                   new OptionAction(self.download_selected, 'glyphicon-download-alt', ' Download as Zip', "", false, true, false),]);
	self.row_options = ko.observableArray([new OptionAction(self.rename, 'glyphicon-pencil', ' Rename', "", false, true, true),
	                                       new OptionAction(self.delete_single, 'glyphicon-remove', ' Delete', "", false, true, true),
	                                       new OptionAction(self.download_single, 'glyphicon-download-alt', ' Download', "", false, true, false),
	                                       new OptionAction(self.unzip, 'glyphicon-compressed', ' Unzip', "", false, true, true),]);
}

var load_content = function(current_zone, current_path, folder){
	zvm.loading(true)
	zvm.folder({})
	var success = function(data){
		zvm.loading(false)
		folder(data)
	}
	hclient.folder.content(current_zone, current_path, success)
}

var go_to_folder = function(item, evt){
	current_path += "/" + item.name
	zvm.breadcrumbs.push({name: item.name, 
						  path: current_path, 
						  components: zvm.breadcrumbs().slice()})
	load_content(current_zone, current_path, zvm.folder);
}

var load_zone = function(item, evt){
	current_zone = item.zone;
	zvm.selected_zone(item);
	zvm.selected_zone_name(current_zone);
	current_path = "";
	zvm.breadcrumbs([{name: "Home", 
		              path: current_path, 
		              components: zvm.breadcrumbs().slice()}]);
	load_content(current_zone, current_path, zvm.folder);
	zvm.selected_items([])
};

var go_to_breadcrumb = function(item, evt){
	if(item.path == current_path){return;};
	current_path = item.path;
	zvm.breadcrumbs(item.components)
	zvm.breadcrumbs.push({name: item.name, 
						  path: current_path, 
						  components: zvm.breadcrumbs().slice()})
	load_content(current_zone, current_path, zvm.folder);
	zvm.selected_items([])
};

var sort_toggle = true
var sort_items = function(item, evt){
	
	console.log(item);
	console.log(evt);
	
	sortkey = $(evt.target).data('sortkey')
	
	console.log(sortkey);
	sort_toggle = !sort_toggle
	zvm.folder.sort(function(left, right) {
		
		if (left['is_dir'] !== right['is_dir']) {
			return (left['is_dir'] > right['is_dir'] ? -1 : 1);
		}
		else {
			var left_name = left[sortkey]
			var right_name = right[sortkey]
			if(sort_toggle){
				return left_name == right_name ? 0 : (left_name < right_name ? -1 : 1);
			}else{
				return left_name == right_name ? 0 : (left_name > right_name ? -1 : 1);
			}
		}
		
	});
};

var select_item = function(item, evt){
	var index = zvm.selected_items.indexOf(item)
	if(index == -1){		
		zvm.selected_items.push(item)
	}else{
		zvm.selected_items.remove(item)
	}
}

var delete_items = function(item, evt){
	data = []
	to_remove = []
	for(i = 0; zvm.selected_items().length > i; i++){
		data.push(zvm.selected_items()[i].name)
		to_remove.push(zvm.selected_items()[i])
	}
	confirm_delete(to_remove, data)
}

var confirm_delete = function(to_remove, data){
	var text = "Are you sure you want to delete the following items? </br></br>" + data.join('</br>')
	HDialog("Confirm delete", text, function(){
		delete_helper(to_remove, data)
	}, true)
}

var delete_helper = function(to_remove, data){
	hclient.folder.remove(current_zone, current_path, data, function(){
		for(i = 0; to_remove.length > i; i++){			
			zvm.folder.remove(to_remove[i])
		}
		zvm.selected_items([]);
	})	
}

var construct_path = function(name){
	return current_zone + current_path + "/" + name
}

var prepare_copy = function(){
	zvm.copy_paths(zvm.selected_items().map(function(e){return construct_path(e.name)}));
	zvm.cut_paths([]);
	zvm.copy_candidates(zvm.selected_items().slice());
	zvm.cut_candidates([]);
}

var prepare_cut = function(){
	zvm.cut_paths(zvm.selected_items().map(function(e){return construct_path(e.name)}));
	zvm.copy_paths([]);
	zvm.cut_candidates(zvm.selected_items().slice());
	zvm.copy_candidates([]);
}

var execute_copy_cut = function(){
	data = {}
	if(zvm.copy_candidates().length > 0){
		copy_cut_helper('copy', zvm.copy_paths, zvm.copy_candidates)
	}
	if(zvm.cut_candidates().length > 0){
		copy_cut_helper('cut', zvm.cut_paths, zvm.cut_candidates)
	}
}

var copy_cut_helper = function(type, list_paths, list_candidates){
	data['type'] = type;
	data['from'] = list_paths()
	hclient.command(current_zone, current_path, [data], function(){
		list_paths([])
		for(i = 0; list_candidates().length > i; i++){
			zvm.folder().push(list_candidates()[i])
		}
		zvm.folder.valueHasMutated();
		list_candidates([]);
	})
}

var download_selected = function(){
	files = zvm.selected_items().map(function(e){return e.name})
	hclient.download.multi(current_zone, current_path, files)
	zvm.selected_items([])
}

var option_upload = function(){
	var input = $('<input type="file" name="files" multiple/>')
	input.on('change', function(){		
		var files = input[0].files;
		make_upload(files);
	});
	input.trigger('click');
}

var rename = function(item, evt){
	var fader = $("<div class='fader'></div>")
	var input = $("<input type='text' class='form-control fader-input' value='"+item.name+"'></input>")
	var row = $(evt.target).parent().parent();
	var file_name_el = row.find(".file_name");
	var css = file_name_el.position();
	css['top'] = css['top'] - 6;
	input.appendTo(fader);
	fader.appendTo("body");
	input.css(css);
	fader.click(function(evt){if(evt.target == this){this.remove();}});
	input.focus();
	input.select();
	input.keyup(function(e){
	    if(e.keyCode == 13)
	    {
	    	var new_fn = input.val();
	    	if(new_fn == item.name){
	    		fader.remove();
	    		return;
	    	}
	        hclient.folder.rename(current_zone, current_path + "/" + item.name, new_fn, function(){
	        	zvm.folder()[zvm.folder().indexOf(item)].name = new_fn;
	        	zvm.folder.valueHasMutated();
	        	fader.remove();
	        });
	    }
	});
}

var create_folder = function(){
	var folder_name = 'new_folder'
	hclient.folder.create(current_zone, current_path + "/" + folder_name, function(){		
		new_folder = {'name': folder_name,
					  'is_dir': true,
					  'size': 0,
					  'modif_date': "",
					  'extension': 'folder'}
		zvm.folder().unshift(new_folder);
		zvm.folder.valueHasMutated();
		var target = $(".file_name:contains('new_folder')").parent().find('.glyphicon-pencil');
		rename(new_folder, {'target': target});
	})
}

var unzip = function(item, evt){
	data['type'] = 'unzip';
	hclient.command(current_zone, current_path + "/" + item.name, [data], function(){
		console.log($('.menu').find('div:contains("'+current_zone+'")'))
		$('.menu').find('div:contains("'+current_zone+'")').trigger('click');
	})
}


var attach_bindings = function(){
	console.log("attaching bindings")
	$("html").bind({
		copy : function(){
			console.log("copy");
			if(current_zone){
				console.log("copy");
				prepare_copy();
			}
		},
		paste : function(){
			if(current_zone){			
				execute_copy_cut();
			}
		},
		cut : function(){
			if(current_zone){			
				prepare_cut();
			}
		},
		keyup: function(e){
			console.log("copy");
			if(current_zone){
				if(e.keyCode == 46){
					delete_items();
				}
			}
		},
	});
}

var zvm = new ZoneViewModel()
