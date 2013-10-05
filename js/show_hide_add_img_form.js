$(document).ready(
    function() {
        $(function(){
            $("body").on("click",".add_img", 
                function(){
                    $('.add_img_box').toggle();              
                }
            );
        });

        $(function(){
            $("body").on("click",".delete_img", 
                function(){
                    $('.delete_img_box').toggle();              
                }
            );
        });        


    }
);
//end of line