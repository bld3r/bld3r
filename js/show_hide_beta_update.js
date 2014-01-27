$(document).ready(
    function() {
        $(function(){
            $("body").on("click",".beta_update", 
                function(){
                    $('.beta_info').toggle();              
                }
            );
        });
    }
);
//end of line