
$(document).ready(function(){	

	//masonry pintrest layout style
//	$(function(){
//		$('#masonry_division').masonry({
			// options
//			itemSelector : '.masonry_object'
//	  	});
//	});
	
	
	var $container = $('#masonry_division');
	$container.imagesLoaded(function(){
		$('.loader').fadeOut("fast");
	    $container.masonry({
			itemSelector : '.masonry_object',
            animate: true,
            isFitWidth: true
	    }).fadeTo("default_duration",1);
	    $(".background").fadeTo("default_duration", 1);
	});
	

});



