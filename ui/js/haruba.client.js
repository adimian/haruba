var CurrentUser = function(){
	self = this
	self.authenticated = ko.observable(false);
	self.admin = ko.observable(false);
	hclient.am_i_logged_in(function(data){
		self.authenticated(data['authenticated'])
		self.admin(data['admin'])
	})
}

var show_error = function(xhr, ajaxOptions, thrownError){
	if(xhr.status == "500"){
		HDialog("An error occured", xhr.responseText, function(){})
		return;
	}
	error_message = JSON.parse(xhr.responseText)['message']
	if(xhr.status == "401" && error_message == "token has expired"){
		hclient.am_i_logged_in(function(){})
	}else{		
		HDialog("An error occured", error_message, function(){})
	}
};

var request = function(args){
	args = $.extend({type: 'get',
					 url: '',
					 data: [],
					 success_func: function(data){console.log(data)},
					 error_func: show_error,
					 has_json: false}, args);

	data = {
	    url: args['url'],
	    type: args['type'],
	    data: args['data'],
	    xhrFields: {
	        withCredentials: true
	    },
	    success: args['success_func'],
	    error: args['error_func'],
	    cache: false,
	};
	if(args['has_json']){
		data.contentType = "application/json";
	};
	$.ajax(data);
};

var post = function(args){
	args.type = 'post'
	request(args)};
var put = function(args){
	args.type = 'put'
	request(args)};
var del = function(args){
	args.type = 'delete'
	request(args)};
var get = function(args){
	args.type = 'get'
	request(args)};

function HRequest(){
	this.service_url = HARUBA_API_URL;
};

HRequest.prototype.get_url = function(base, group, path){
	var full_path = this.service_url + base
	console.log(full_path)
	if(group){
		full_path += "/" + group
	}
	if(path){
		full_path += path
	}
	return full_path;
};

// ---------------------PERMISSIONS---------------------
function HPermissions(){};
HPermissions.prototype = new HRequest();
HPermissions.prototype.get_users = function(success_func){
	args = {
		url: this.get_url("/permissions"), 
		success_func: function(data, text, xrh){
				 	  	success_func(data)
			   		  }
	};
	get(args);
};
HPermissions.prototype.grant = function(permissions){
	args = {
		url: this.get_url("/permissions"),
		data: JSON.stringify({'permissions': permissions}),
		has_json: true
	};
	post(args);
};
HPermissions.prototype.withdraw = function(permissions){
	args = {
		url: this.get_url("/permissions"),
		data: JSON.stringify({'permissions': permissions}),
		has_json: true
	};
	del(args);
};

// -----------------------FOLDER-----------------------
function HFolder(){};
HFolder.prototype = new HRequest();
HFolder.prototype.content = function(group, path, success_func){
	args = {
		url: this.get_url("/files", group, path),
		success_func: function(data, text, xrh){
			success_func(data);
			zvm.selected_items([]);
			console.log(data);
		}
	}
	get(args);
};
HFolder.prototype.create = function(group, path, success_func){	
	args = {
		url: this.get_url("/files", group, path),
		success_func: function(data, text, xrh){
			success_func();
		},
	}
	post(args);
};
HFolder.prototype.rename = function(group, path, rename_to, success_func){		
	args = {
			url: this.get_url("/files", group, path),
			data: {'rename_to': rename_to},
			success_func: function(data, text, xrh){
				success_func();
			},
		};
	put(args);
};
HFolder.prototype.remove = function(group, path, files, success_func){
	args = {
		url: this.get_url("/files", group, path),
		data: JSON.stringify({'files_to_delete': files}),
		success_func: function(data, text, xrh){
			success_func();
		},
		has_json: true,
	};
	del(args);
};

//-----------------------DOWNLOAD-----------------------
function HDownload(){};
HDownload.prototype = new HRequest();
HDownload.prototype.single = function(group, path){
	window.location = this.get_url("/download", group, path);
};
HDownload.prototype.multi = function(group, path, files){
	url = this.get_url("/download", group, path);
    var form = $('<form></form>').attr('action', url).attr('method', 'post');
    form.append($("<input></input>").attr('type', 'hidden').attr('name', "filenames").attr('value', files));
    form.appendTo('body').submit().remove();
};

//-----------------------ZONES-----------------------
function HZone(){};
HZone.prototype = new HRequest();
HZone.prototype.myzones = function(success_func){
	args = {
		url: this.get_url("/myzones"),
		success_func: function(data, text, xrh){
			success_func(data)
			console.log(data);
		},
	};
	get(args);
};
HZone.prototype.zones = function(success_func){
	args = {
		url: this.get_url("/zone"),
		success_func: function(data, text, xrh){
			success_func(data);
		}
	}
	get(args);
};
HZone.prototype.create = function(zones, success_func){
	args = {
		url: this.get_url("/zone"),
		data: JSON.stringify({'zones': zones}),
		success_func: function(data, text, xrh){
			success_func()
			console.log(data);
		},
		has_json: true,
	}
	post(args);
};
HZone.prototype.update = function(zones){		
	args = {
		url: this.get_url("/zone"),
		data:  JSON.stringify({'zones': zones}),
		has_json: true, 
	}
	put(args);
};


// -----------------------CLIENT-----------------------
function HClient(){}
HClient.prototype = new HRequest()
HClient.prototype.am_i_logged_in = function(success_func){
	args = {
		url: this.get_url("/login"),
		success_func:  function(data, text, xrh){
			if(data['authenticated'] == false){
				$.get("/login.html", function(data){
					$("body").append(data);
				});
			}else{
				success_func(data)
			}
		}
	};
	get(args);
}
HClient.prototype.login = function(username, password, totp){
	data = {"login": username,
			"password": password,
			"totp": totp};
	
	window.login_app.error_message("")
	
	args = {
		url: this.get_url("/login"),
		data: data,
		success_func: function(data, text, xrh){
			if(!initialised){	
				$.get("/app.html", function(data){
					initialised = true;
					$("body").html(data);
				});
			}else{
				$("#login-fader").remove();
			}
		},
		error_func: function(xhr, ajaxOptions, thrownError){
			console.log(xhr.responseText)
			if(xhr.status == "500"){
				HDialog("An error occured", xhr.responseText, function(){})
				return;
			}
			error_message = JSON.parse(xhr.responseText)['message']
			window.login_app.error_message(error_message)
		},
	}
	post(args);
}
HClient.prototype.logout = function(){
	args = {
		url: this.get_url("/logout"),
		success_func: function(data, text, xrh){
			$.get("/login.html", function(data){
				$("body").append(data);
			});
		}
	}
	get(args);
}
HClient.prototype.user_details = function(success_func){
	args = {
		url: this.get_url("/user/details"),
		success_func: function(data, text, xrh){
			success_func(data)
		}
	}
	get(args);
}
HClient.prototype.upload = function(group, path, files, extra_data, progress_func, setui_func, success_func){
	for (var i = 0; i < files.length; i++)
	{
		var file = files[i]
		el = setui_func(file);
		bind = success_func.bind(null, el, file)

		var formData = new FormData();
		formData.append("files", file);
		$.each(extra_data, function(key, value){
			formData.append(key, value);
		});
	    $.ajax({
	        url: this.get_url("/upload", group, path),  
	        type: 'POST',
	        xhr: function() { 
	            var myXhr = $.ajaxSettings.xhr();
	            if(myXhr.upload){
	            	myXhr.upload.el = el
	                myXhr.upload.addEventListener('progress', progress_func , false); // For handling the progress of the upload
	            }
	            return myXhr;
	        },
	        success: bind,
	        error: function(xhr, ajaxOptions, thrownError){el.remove(); show_error(xhr, ajaxOptions, thrownError)},
	        data: formData,
	        cache: false,
	        contentType: false,
	        processData: false
	    });
	}
}
HClient.prototype.command = function(group, path, data, success_func){
	args = {
		url: this.get_url("/command", group, path),
		data: JSON.stringify({'commands': data}),
		success_func:function(data, text, xrh){
			console.log("executing func")
			success_func();
		},
		has_json: true,
	}
	post(args)
},
HClient.prototype.permissions = new HPermissions()	
HClient.prototype.folder = new HFolder()
HClient.prototype.download = new HDownload()
HClient.prototype.zone = new HZone()

var initialised = false;
var hclient = new HClient()
hclient.am_i_logged_in(function(){
	$.get("/app.html", function(data){
		initialised = true;
		$("body").html(data);
		init_dragdrop();
	});
})
