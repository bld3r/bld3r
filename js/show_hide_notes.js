$(document).ready(
    function() {
        $(function(){
            $("body").on("click","span.see_notes", 
                function(){
                    $('.notes').toggle();              
                }
            );
        });
    }
);
//end of line