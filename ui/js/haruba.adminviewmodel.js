function AdminViewModel(){
	var self = this;
	self.zones = ko.observableArray();
	self.selected_zone = ko.observable();
	self.selected_zone_name = ko.observable();
	self.users = ko.observableArray();
	self.user_candidates = ko.observableArray();
	self.user_dialog_candidates = ko.observableArray();
	self.user_dialog_selected = ko.observableArray();
	self.zone_dialog_candidates = ko.observableArray();
	self.zone_dialog_selected = ko.observableArray();
	self.query = ko.observable('');
	self.query_dialog = ko.observable('');
	self.has_read_rights_css = function(user){return get_permission_css(user, "read");};
	self.has_write_rights_css = function(user){return get_permission_css(user, "write");};
	self.revoke_rights = ko.observableArray();
	self.grant_rights = ko.observableArray();
	self.has_changed = ko.observable(false);
	self.pending_permissions = ko.observableArray();
	
	//behaviour
	self.logout = function(){hclient.logout()};
	self.load_home = function(){$.get("/app.html", function(data){ $("body").html(data);})};
	self.load_zone = load_zone;
	self.register_pemission_change = register_pemission_change;
	self.select_users = select_users
	self.select_zones = select_zones
	self.search_main = search_main;
	self.search_dialog = search_dialog;
	self.query.subscribe(self.search_main);
	self.query_dialog.subscribe(self.search_dialog);
	hclient.zone.zones(self.zones);
	self.add_to_selected_users = function(item, evt){ if(avm.user_dialog_selected().indexOf(item)==-1){avm.user_dialog_selected.push(item)}};
	self.remove_from_selected_users = function(item, evt){ if(avm.user_dialog_selected().indexOf(item)>-1){avm.user_dialog_selected.remove(item)}};
	self.add_to_selected_zones = function(item, evt){ if(avm.zone_dialog_selected().indexOf(item)==-1){avm.zone_dialog_selected.push(item)}};
	self.remove_from_selected_zones = function(item, evt){ if(avm.zone_dialog_selected().indexOf(item)>-1){avm.zone_dialog_selected.remove(item)}};
	self.save_permissions = save_permissions

}

var load_zone = function(item, evt){
	avm.selected_zone(item);
	avm.selected_zone_name(item.name);
	hclient.permissions.get_users(function(data){avm.users(data.users); avm.query.valueHasMutated()})
}

var search_main = function(search_str){
	avm.user_candidates.removeAll();
	if(search_str == ""){
		return;
	}
	var to_search_array = avm.users();
	search(to_search_array, search_str, function(val){
		user = $.extend(true, {}, val)
		user.ptracker = new PermissionTracker(user.username,
											  has_permission(user, avm.selected_zone_name(), "read"),
										      has_permission(user, avm.selected_zone_name(), "write"));
		avm.user_candidates.push(user)
	})

}

var search_dialog = function(search_str){
	avm.user_dialog_candidates([]);
	search(avm.users(), search_str, function(val){
		avm.user_dialog_candidates.push(val)
	})
}

var search = function(to_search_array, search_str, found_func){
	for(i=0;to_search_array.length>i;i++){
		to_search_string = to_search_array[i].username + " " + to_search_array[i].display_name
		if(to_search_string.search(search_str)>-1){
			found_func(to_search_array[i])
		}
	}
}

var has_permission = function(user, zone, permission){
	if(user.permissions.hasOwnProperty(zone)){		
		return user.permissions[zone].indexOf(permission)>-1;
	}
	return false;
}

var get_permission_css = function(user, permission){
	if(user.ptracker[permission]){
		return "glyphicon glyphicon-ok color_green";
	}else{
		return "glyphicon glyphicon-remove color_red";
	}
}

function PermissionTracker(username, initial_read, initial_write){
	this.username = username
	this.initial_read = initial_read;
	this.initial_write = initial_write;
	this.read = initial_read;
	this.write = initial_write;
	this.apply_to_zones = [];
	this.apply_to_users = [];
}
PermissionTracker.prototype.has_changed = function(){
	if(this.apply_to_zones.length>0){
		return true;
	}else if(this.apply_to_users.length>0){
		return true;
	}else if(this.initial_read != this.read){
		return true;
	}else if(this.initial_write != this.write){
		return true;
	}
	return false;
}
PermissionTracker.prototype.get_changed = function(){
	changed = {"revoke": [],
			   "grant": []}
	console.log("-----***")
	var zones = $.extend(true, [], this.apply_to_zones)
	console.log(zones)
	zones.push({"name": avm.selected_zone_name()})
	console.log(zones)
	for(i=0;zones.length>i;i++){
		var zone_name = zones[i].name
		var read_need = ["zone", "read", zone_name]
		if(this.read){
			changed["grant"].push(read_need)
		}else{
			changed["revoke"].push(read_need)
		}
		var write_need = ["zone", "write", zone_name]
		if(this.write){
			changed["grant"].push(write_need)
		}else{
			changed["revoke"].push(write_need)
		}
	}
	
	var revoke = []
	var grant = []
	var users = $.extend(true, [], this.apply_to_users)
	console.log(users)
	users.push({"username": this.username})
	console.log(users)
	for(i=0;users.length>i;i++){
		username = users[i].username
		revoke.push({"username": username,
			         "needs": $.extend(true, [], changed['revoke'])})
	    grant.push({"username": username,
			         "needs": $.extend(true, [], changed['grant'])})
	}
	console.log(revoke)
	console.log(grant)
	return [revoke, grant];
}

var register_pemission_change = function(item, evt){
	var target = $(evt.target);
	target.toggleClass("glyphicon-ok");
	target.toggleClass("glyphicon-remove");
	target.toggleClass("color_green");
	target.toggleClass("color_red");
	item.ptracker[target.data("perm")] = !item.ptracker[target.data("perm")]
	avm.user_candidates.valueHasMutated();
	avm.has_changed($(".folder").length>0);
}

var select_users = function(item, evt){
	load_dialog("/user_selection.html", "Select users to apply permissions", 
			    avm.user_dialog_selected, item, "apply_to_users");
	avm.user_dialog_candidates(avm.users);
	avm.user_dialog_selected([])
	avm.user_dialog_selected($.extend(true, [], item.ptracker.apply_to_users));
}

var select_zones = function(item, evt){
	load_dialog("/zone_selection.html", "Select zones to apply permissions", 
			    avm.zone_dialog_selected, item, "apply_to_zones");
	avm.zone_dialog_candidates(avm.zones);
	avm.zone_dialog_selected([])
	avm.zone_dialog_selected($.extend(true, [], item.ptracker.apply_to_zones));
}

var load_dialog = function(url, title, selected_list, item, ptracker_attr){
	$.get(url, function(data){
		HDialog(title, data, function(){
			apply_to = []
			selected = selected_list()
			for(i=0;selected.length>i;i++){
				apply_to.push($.extend(true, {}, selected[i]))
			}
			console.log(selected)
			console.log(apply_to)
			item.ptracker[ptracker_attr] = apply_to;
			console.log(item.ptracker[ptracker_attr])
			avm.user_candidates.valueHasMutated();
			avm.has_changed($(".folder").length>0);
		});
		ko.applyBindings(avm, $("#dialog-user-list")[0]);
	});
}

var save_permissions = function(){
	avm.pending_permissions([]);
	var users = avm.user_candidates()
	for(idx=0;users.length>idx;idx++){
		if(users[idx].ptracker.has_changed()){
			avm.pending_permissions.push(users[idx].ptracker.get_changed());
		}
	}
	$.get("/confirm_permission.html", function(data){
		HDialog("Are you sure you want to grant these permission", data, function(){
			var pp = avm.pending_permissions()
			for(i=0;pp.length>i;i++){
				hclient.permissions.withdraw(pp[i][0])
				hclient.permissions.grant(pp[i][1])
			}
		}, true)
		ko.applyBindings(avm, $("#dialog-permission")[0]);
	});
}


var avm = new AdminViewModel()
