var dialog_template = '<div class="dialog_container">'+
					  '  <div class="dtitle_container">:TITLE:<span class="glyphicon glyphicon-remove"><span></div>'+
					  '  <div class="dtext_container">:TEXT:</div>'+
					  '</div>'


var HDialog = function(title, text, confirm_func, is_confirm){
	var remove = function(){fader.remove()}
	
	var fader = $("<div class='fader'></div>");
	var dialog_container = $(dialog_template.replace(":TITLE:", title).replace(":TEXT:", text))
	var cancel_btn = $('<button type="button" class="btn btn-danger">Cancel</button>');
	var confirm_btn = $('<button type="button" class="btn btn-success">Ok</button>');
	$(dialog_container.find(".glyphicon")).on('click', remove);
	
	dialog_container.appendTo(fader);
	confirm_btn.appendTo(dialog_container);
	if(is_confirm){		
		cancel_btn.appendTo(dialog_container);
	}
	
	
	confirm_btn.on('click', function(){confirm_func(); fader.remove()});
	cancel_btn.on('click', remove);
	$('body').append(fader);
	var left =  ($( window ).width() / 2) - (dialog_container.outerWidth()/2)
	dialog_container.css({'left': left})
	dialog_container.find(".dtext_container").css({'max-height': $( window ).height()-200})
	
	confirm_btn.keyup(function(e){
	    if(e.keyCode == 13)
	    {
	    	confirm_btn.trigger('click')
	    }
	});
	confirm_btn.focus();
}