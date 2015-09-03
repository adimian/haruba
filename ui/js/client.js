var LOGGED_IN = false;

var show_error = function(xhr, ajaxOptions, thrownError){
	error_message = JSON.parse(xhr.responseText)['message']
	HDialog("An error occured", error_message, function(){})
};

var request = function(type, url, form_data, success_func, has_json){
	data = {
	    url: url,
	    type: type,
	    data: form_data,
	    xhrFields: {
	        withCredentials: true
	    },
	    success: success_func,
	    error: show_error,
	    cache: false,
	};
	if(has_json){
		data.contentType = "application/json";
	};
	console.log(data)
	$.ajax(data);
};

var post = function(url, data, success_func, has_json){
	request('post', url, data, success_func, has_json)};
var put = function(url, data, success_func, has_json){
	request('put', url, data, success_func, has_json)};
var del = function(url, data, success_func, has_json){
	request('delete', url, data, success_func, has_json)};
var get = function(url, success_func){
	request('get', url, [], success_func)};

function HRequest(){
	this.service_url = "http://localhost:5000";
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
HPermissions.prototype.get_users = function(){
	get(this.get_url("/permissions"), function(data, text, xrh){
		console.log(data);
	});
};
HPermissions.prototype.grant = function(username, needs){
	data = JSON.stringify({'permissions': [{'username': username,
							 				'needs': needs}]});
	post(this.get_url("/permissions"), data, function(data, text, xrh){
		console.log(data);
	}, true);
};
HPermissions.prototype.withdraw = function(username, needs){
	data = JSON.stringify({'permissions': [{'username': username,
		 					 				'needs': needs}]});
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
HZone.prototype.zones = function(){		
	get(this.get_url("/zone"), function(data, text, xrh){
		console.log(data);
	});
};
HZone.prototype.create = function(zones){
	data = JSON.stringify({'zones': zones})
	post(this.get_url("/zone"), data, function(data, text, xrh){
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
HClient.prototype.am_i_logged_in = function(){
	get(this.get_url("/login"), function(data, text, xrh){
		if(data == false){
			$.get("/login.html", function(data){
				$("body").html(data);
			});
		}else{
			$.get("/app.html", function(data){
				$("body").html(data);
				init_dragdrop();
			});
		}
		LOGGED_IN = data;
	});
}
HClient.prototype.login = function(username, password){
	data = {"login": username,
			"password": password};
	
	post(this.get_url("/login"), data, function(data, text, xrh){
		LOGGED_IN = true;
		console.log("logged in")
		$.get("/app.html", function(data){
			$("body").html(data);
		});
	});
}
HClient.prototype.logout = function(){
	get(this.get_url("/logout"), function(data, text, xrh){
		LOGGED_IN = false;
		$.get("/login.html", function(data){
			$("body").html(data);
		});
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
	        error: show_error,
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
	
var hclient = new HClient()
hclient.am_i_logged_in()
		
		
		
		
		
		
		
		
		
		
		
		
		
		
