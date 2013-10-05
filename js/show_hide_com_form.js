$(document).ready(
    function() {
        $(function(){
            $("body").on("click",".showcombox", 
                function(){
                	$('.showcombox_holder').toggle();  
                    $('.combox').toggle();              
                }
            );
        });


    }
);
//end of line