$(document).ready(
    function() {
        $(function(){
            $("body").on("click",".is_author", 
                function(){
                    $('#sublicense').hide().animate({height: '0px', opacity: '0'}, 800);
                }
            );
        });
        $(function(){
            $("body").on("click","#not_author", 
                function(){
                    $('#sublicense').show().animate({height: '300px', opacity: '1'}, 800);
                }
            );
        });  
    }
);
//end of line