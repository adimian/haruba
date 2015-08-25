var file_template = '<div class="list-row">'+
					'  <div class="row-item width-5">&nbsp;</div>'+
   					'  <div class="row-item width-70">:NAME:</div>'+
   					'  <div class="progress-bar progress-bar-info progress-bar-striped"></div>'+
   					'</div>'

var init_dragdrop = function(){	
	var holder = $('body')[0];
	console.log(holder)
	
	$('.upload-marker').click(function(){
		$('.upload-marker').removeClass("upload-visible");
		return false;
	});

	holder.ondragover = function () {
		if(current_zone){			
			$('.upload-marker').addClass("upload-visible");
		}
		return false; 
	};
	holder.ondragend = function () { 
		$('.upload-marker').removeClass("upload-visible");
		return false; 
	};
	
	$('.upload-marker')[0].ondrop = function(e) {
		$('.upload-marker').removeClass("upload-visible");
	    e.preventDefault();  
	    e.stopPropagation();
	    var files = e.dataTransfer.files;
	    make_upload(files);
	};
}

var make_upload = function(files){
    hclient.upload(current_zone, current_path, files, [], 
  	      function(e){
  	    	if(e.lengthComputable){
  	    		max = e.total
              	loaded = e.loaded
              	progress = el.outerWidth() * loaded/max
              	this.el.find('.progress-bar').css("width", progress + "px")
              }
  	    },function(file){
  	    	var el = $(file_template.replace(":NAME:", file.name))
  	    	el.appendTo(".listing");
  	    	pos = el.position()
  	    	console.log(pos)
  	    	el.find('.progress-bar').css(pos)
  	    	return el;
  	    }, function(el, file){
  	    	data = {"name": file.name,
  	    		    "is_dir": false,
  	    		    "size": file.size,
  	    		    "modif_date": "",
  	    		    "extension": file.name.split('.').pop()}
  	    	var folder = zvm.folder()
  	    	folder.push(data)
  	    	console.log(folder)
  	    	zvm.folder(folder)
  	    });
}