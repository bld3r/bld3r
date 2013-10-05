$(document).ready(
    function() {
        $(function(){
            $("body").on("click","span.showsubcombox", 
                function(){
                    com_id = $(this).attr('id');                    
                    $("#subcombox"+com_id).toggle();    
                }
            );
        });


    }
);
//end of line