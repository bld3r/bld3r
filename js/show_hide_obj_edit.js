$(document).ready(
    function() {
        $(function(){
            $("body").on("click","div.description_current", 
                function(){
                    $('.description_edit').toggle();   
                    $('.description_current').toggle(); 
                }
            );
        });
        $(function(){
            $("body").on("click","span.description_cancel", 
                function(){
                    $('.description_edit').toggle();   
                    $('.description_current').toggle(); 
                }
            );
        });  
    }
);
//end of line