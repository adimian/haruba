var current_zone = "";
var current_path = "";

function ZoneViewModel(){
	var is_mac = navigator.platform.toUpperCase().indexOf('MAC')>=0;
	
	var self = this;
	self.ctrl = is_mac?'Cmd':'Ctrl';
	console.log(self.ctrl)
	self.zones = ko.observable();
	self.folder = ko.observable();
	self.working_folder = ko.observableArray();
	self.selected_zone = ko.observable();
	self.breadcrumbs = ko.observableArray();
	self.selected_items = ko.observableArray();
	self.cut_candidates = ko.observableArray();
	self.copy_candidates = ko.observableArray();
	self.cut_paths = ko.observableArray();
	self.copy_paths = ko.observableArray();
	hclient.zone.myzones(self.zones)
	
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
	self.delete_single = function(item, evt){delete_helper([item], [item.name]);};
	self.download_single = function(item, evt){hclient.download.single(current_zone, current_path + "/" + item.name);};
	self.rename = rename;
	self.create_folder = create_folder;
}

var go_to_folder = function(item, evt){
	current_path += "/" + item.name
	zvm.breadcrumbs.push({name: item.name, 
						  path: current_path, 
						  components: zvm.breadcrumbs().slice()})
	hclient.folder.content(current_zone, current_path, zvm.folder)
}

var load_zone = function(item, evt){
	current_zone = item.zone;
	zvm.selected_zone(current_zone)
	current_path = "";
	zvm.breadcrumbs([{name: "Home", 
		              path: current_path, 
		              components: zvm.breadcrumbs().slice()}]);
	hclient.folder.content(current_zone, current_path, zvm.folder);
	zvm.selected_items([])
};

var go_to_breadcrumb = function(item, evt){
	if(item.path == current_path){return;};
	current_path = item.path;
	zvm.breadcrumbs(item.components)
	zvm.breadcrumbs.push({name: item.name, 
						  path: current_path, 
						  components: zvm.breadcrumbs().slice()})
	hclient.folder.content(current_zone, current_path, zvm.folder);
	zvm.selected_items([])
};

var sort_toggle = true
var sort_items = function(item, evt){
	zvm.working_folder(zvm.folder())
	sortkey = $(evt.target).data('sortkey')
	sort_toggle = !sort_toggle
	zvm.working_folder.sort(function(left, right) {
		var left_name = left[sortkey]
		var right_name = right[sortkey]
		if(sort_toggle){
			return left_name == right_name ? 0 : (left_name < right_name ? -1 : 1);
		}else{
			return left_name == right_name ? 0 : (left_name > right_name ? -1 : 1);
		}
	});
	zvm.folder(zvm.working_folder())
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
	delete_helper(to_remove, data);
}

var delete_helper = function(to_remove, data){
	hclient.folder.remove(current_zone, current_path, data, function(){
		zvm.working_folder(zvm.folder())
		for(i = 0; to_remove.length > i; i++){			
			zvm.working_folder.remove(to_remove[i])
		}
		zvm.folder(zvm.working_folder());
		zvm.selected_items([]);
	})	
}

var construct_path = function(name){
	return current_zone + current_path + "/" + name
}

var prepare_copy = function(){
	zvm.copy_paths(zvm.selected_items().map(function(e){return construct_path(e.name)}));
	zvm.cut_paths([]);
	zvm.copy_candidates(zvm.selected_items());
	zvm.cut_candidates([]);
}

var prepare_cut = function(){
	zvm.cut_paths(zvm.selected_items().map(function(e){return construct_path(e.name)}));
	zvm.copy_paths([]);
	zvm.cut_candidates(zvm.selected_items());
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
			console.log(list_candidates()[i])
			zvm.working_folder(zvm.folder())
			zvm.working_folder().push(list_candidates()[i])
			zvm.folder(zvm.working_folder())
		}
		list_candidates([])
	})
}

var download_selected = function(){
	files = zvm.selected_items().map(function(e){return e.name})
	console.log(files)
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
	        hclient.folder.rename(current_zone, current_path + "/" + item.name, new_fn, function(){
	        	zvm.working_folder(zvm.folder());
	        	zvm.working_folder()[zvm.working_folder().indexOf(item)].name = new_fn;
	        	zvm.folder(zvm.working_folder());
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
		zvm.working_folder(zvm.folder());
		zvm.working_folder().unshift(new_folder);
		zvm.folder(zvm.working_folder());
		$(".file_name:contains('new_folder')").parent().find('.glyphicon-pencil').trigger('click');
	})
}

$("html").bind({
	copy : function(){
		if(current_zone){			
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
		if(current_zone){
			if(e.keyCode == 46){
				delete_items();
			}
		}
	},
});

var zvm = new ZoneViewModel()