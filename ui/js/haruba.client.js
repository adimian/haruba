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

var request = function(type, url, form_data, success_func, has_json, error_func){
	if(!error_func){
		error_func = show_error
	}
	data = {
	    url: url,
	    type: type,
	    data: form_data,
	    xhrFields: {
	        withCredentials: true
	    },
	    success: success_func,
	    error: error_func,
	    cache: false,
	};
	if(has_json){
		data.contentType = "application/json";
	};
	console.log(data)
	$.ajax(data);
};

var post = function(url, data, success_func, has_json, error_func){
	console.log(has_json)
	console.log(error_func)
	request('post', url, data, success_func, has_json, error_func)};
var put = function(url, data, success_func, has_json, error_func){
	request('put', url, data, success_func, has_json, error_func)};
var del = function(url, data, success_func, has_json, error_func){
	request('delete', url, data, success_func, has_json, error_func)};
var get = function(url, success_func, error_func){
	request('get', url, [], success_func, false, error_func)};

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
	get(this.get_url("/permissions"), function(data, text, xrh){
		success_func(data)
	});
};
HPermissions.prototype.grant = function(permissions){
	data = JSON.stringify({'permissions': permissions});
	post(this.get_url("/permissions"), data, function(data, text, xrh){
		console.log(data);
	}, true);
};
HPermissions.prototype.withdraw = function(permissions){
	data = JSON.stringify({'permissions': permissions});
	del(this.get_url("/permissions"), data, function(data, text, xrh){
		console.log(data);
	}, true);
};

// -----------------------FOLDER-----------------------
function HFolder(){};
HFolder.prototype = new HRequest();
HFolder.prototype.content = function(group, path, success_func){
	get(this.get_url("/files", group, path), function(data, text, xrh){
		success_func(data);
		zvm.selected_items([]);
		console.log(data);
	});
};
HFolder.prototype.create = function(group, path, success_func){		
	post(this.get_url("/files", group, path), [], function(data, text, xrh){
		success_func();
	});
};
HFolder.prototype.rename = function(group, path, rename_to, success_func){		
	data = {'rename_to': rename_to};
	put(this.get_url("/files", group, path), data, function(data, text, xrh){
		success_func();
	});
};
HFolder.prototype.remove = function(group, path, files, success_func){
	data = JSON.stringify({'files_to_delete': files});
	del(this.get_url("/files", group, path), data, function(data, text, xrh){
		success_func()
	}, true);
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
	get(this.get_url("/myzones"), function(data, text, xrh){
		success_func(data)
		console.log(data);
	});
};
HZone.prototype.zones = function(success_func){		
	get(this.get_url("/zone"), function(data, text, xrh){
		success_func(data);
	});
};
HZone.prototype.create = function(zones, success_func){
	data = JSON.stringify({'zones': zones})
	post(this.get_url("/zone"), data, function(data, text, xrh){
		success_func()
		console.log(data);
	}, true);
};
HZone.prototype.update = function(zones){		
	data = JSON.stringify({'zones': zones})
	put(this.get_url("/zone"), data, function(data, text, xrh){
		console.log(data);
	}, true);
};


// -----------------------CLIENT-----------------------
function HClient(){}
HClient.prototype = new HRequest()
HClient.prototype.am_i_logged_in = function(success_func){
	get(this.get_url("/login"), function(data, text, xrh){
		if(data['authenticated'] == false){
			$.get("/login.html", function(data){
				$("body").append(data);
				$("#password").keypress(function(e) {
				    if(e.which == 13) {
				        $('#login-button').trigger('click')
				    }
				});
			});
		}else{
			success_func(data)
		}
	});
}
HClient.prototype.login = function(username, password, totp){
	data = {"login": username,
			"password": password,
			"totp": totp};
	
	window.login_app.error_message("")
	post(this.get_url("/login"), data, function(data, text, xrh){
		if(!initialised){	
			$.get("/app.html", function(data){
				initialised = true;
				$("body").html(data);
			});
		}else{
			$("#login-fader").remove();
		}
	}, false, function(xhr, ajaxOptions, thrownError){
		console.log(xhr.responseText)
		if(xhr.status == "500"){
			HDialog("An error occured", xhr.responseText, function(){})
			return;
		}
		error_message = JSON.parse(xhr.responseText)['message']
		window.login_app.error_message(error_message)
	});
}
HClient.prototype.logout = function(){
	get(this.get_url("/logout"), function(data, text, xrh){
		$.get("/login.html", function(data){
			$("body").html(data);
		});
	});
}
HClient.prototype.user_details = function(success_func){
	get(this.get_url("/user/details"), function(data, text, xrh){
		console.log(data)
		success_func(data)
	});
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
	data = JSON.stringify({'commands': data})
	post(this.get_url("/command", group, path), data, function(data, text, xrh){
		console.log("executing func")
		success_func();
	}, true)
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
		
		
		
		
		
		
		
		
		
		
		
		
		
		
