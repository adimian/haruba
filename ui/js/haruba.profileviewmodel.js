var has = "glyphicon glyphicon-ok color_green"
var has_not = "glyphicon glyphicon-remove color_red";

var sorted = [
              "username",
              "firstname",
              "lastname",
              "displayname",
              "mobile",
              "email",
              "active",
              "api_key",
              "provides",
              ]

var Item = function(key, value){
	this.key = key
	this.val = value
}
Item.prototype.value = function(){
	return this.val
}

var PermLine = function(zone, read, write){
	this.zone = zone
	this.read = read
	this.write = write
}
PermLine.prototype.to_html = function(){
	return "<div class='perm-detail-row'><span>"+this.zone+"</span><span class='"+this.read+"'></span><span class='"+this.write+"'></span></div>"
}

var ListItem = function(key, value){
	this.key = key
	this.val = value
}
ListItem.prototype.value = function(){
	data = this.val
	output = "<div style='font-weight: 600;' class='perm-detail-row'><span>Zone</span><span>Read</span><span>Write</span></div>"
	for(i=0; data.length>i;i++){
		data_line = data[i]
		line = new PermLine(data_line['zone'], has_not, has_not);
		console.log(data_line['access'])
		if(data_line['access'].indexOf('read') > -1){
			console.log('has')
			line.read = has;
		}
		if(data_line['access'].indexOf('write') > -1){
			line.write = has;
		}
		output += line.to_html();
	}
	return output
}

function ProfileViewModel(){
	var self = this;
	self.user_details = ko.observableArray();
	self.current_user = new CurrentUser()
	
	//behaviour
	self.load_admin = function(){$.get("/admin.html", function(data){ $("body").html(data);})};
	self.load_home = function(){$.get("/app.html", function(data){ $("body").html(data);})};
	self.load_profile = function(){$.get("/profile.html", function(data){ $("body").html(data);})};
	self.logout = function(){hclient.logout()};
	self.process_details = function(data){
		$.each(sorted, function(idx, key){
			value = data[key]
			if(Object.prototype.toString.call(value) === '[object Array]'){
				item = new ListItem(key, value)
			}else{
				item = new Item(key, value)
			}
			self.user_details.push(item);	
		});
	}
}


var pvm = new ProfileViewModel()
