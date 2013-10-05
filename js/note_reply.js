$(document).ready(
    function() {
        $(function(){
            $("body").on("click","div.note_reply", 
                function(){
                    thing_id = $(this).attr('id');
                    $("." + thing_id).fadeIn('slow');
                }
            );
        });
        $(function(){
            $("body").on("click","#cancel", 
                function(){
                    cancel_id = $(this).attr('class');
                    $("." + cancel_id).fadeOut('slow');
                }
            );
        });
    }
);
//end of line