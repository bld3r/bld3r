$(document).ready(function(){      
  //$('.long_load').animate({"opacity": "1"}, 10000);
  var $container = $('#masonry_division');
  $container.imagesLoaded(function(){
    $('.loader').fadeOut("fast");
    $container.fadeTo("default_duration", 1);
      $container.masonry({
        itemSelector : '.masonry_object',
        isFitWidth: true,
        transitionDuration: 0
      });
    $('.masonry_object img.lazy').lazyload({
        threshold : 10,
        effect: 'fadeIn',
        effectspeed: 1000,
        load: function() {
            // Disable trigger on this image
            $(this).removeClass("lazy");
            $container.masonry();
        }
    });
    //$('.masonry_object img.lazy').trigger('scroll'); 
      // // Custom fading animation (This may not be necessary)
      // $('.masonry_object img').on('load', function() {
      //   $(this).fadeIn(250);
      // }).each(function() {
      //   if(this.complete) {
      //     $(this).load();
      //   }
      // });    
  });



  // Infinite Scroll
  $container.infinitescroll({
    debug: false,
    extraScrollPx: 0,
    bufferPx: 40,
    pixelsFromNavToBottom:10,
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
      var $newElems = $( newElements );
      // ensure that images load before adding to masonry layout
      $newElems.imagesLoaded(function(){
        // show elems now they're ready
        
        $container.masonry( 'appended', $newElems, true ); 
        $('.masonry_object img.lazy').lazyload({
            effect: 'fadeIn',
            effectspeed: 1500 ,
            load: function() {
                // Disable trigger on this image
                $(this).removeClass("lazy");
                $container.masonry();
            }
        });
        //$('.masonry_object img.lazy').trigger('scroll');         
        
        // // Custom fading animation (This may not be necessary)
        // $newElems.on('load', function() {
        //   $(this).fadeIn(250);
        // }).each(function() {
        //   if(this.complete) {
        //     $(this).load();
        //   }
        // });

      });
    }
  );

});