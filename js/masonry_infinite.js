$(document).ready(function(){
  $('.long_load').animate({"opacity": "1"}, 10000);
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

  // Infinite Scroll
  $container.infinitescroll({
    debug: false,
    extraScrollPx: 0,
    bufferPx: 0,
    navSelector  : '#navigation',    // selector for the paged navigation 
    nextSelector : '#navigation a',  // selector for the NEXT link (to page 2)
    itemSelector : '.masonry_object',     // selector for all items you'll retrieve
    loading: {
        finishedMsg: null,
        img: "img/loader.gif",
        msg: null,
        msgText: " ",
        speed: 'fast',
      }
    },
    // trigger Masonry as a callback
    function( newElements ) {
      // hide new items while they are loading
      var $newElems = $( newElements ).css({display:"none"},{ opacity: 0 });
      // ensure that images load before adding to masonry layout
      $newElems.imagesLoaded(function(){
        // show elems now they're ready
        
        $container.masonry( 'appended', $newElems, true ); 
        $newElems.show().delay(1000).animate({ opacity: 1 },1000);
      });
    }
  );

});