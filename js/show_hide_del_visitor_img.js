$(document).ready(
    function() {
        $(function(){
            $("body").on("click",".delete_visitor_img",
                function(){
                	text = $(this).attr('id');
                    $("div."+text).fadeToggle("slow");            
                }
            );
        });
    }
);
//end of line