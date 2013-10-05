$(document).ready(
    function() {
        $(function(){
            $("body").on("click","div.delete", 
                function(){
                    $("div.check").toggle();
                }
            );
        });
        $(function(){
            $("body").on("click","span.del_yes", 
                function(){
                    obj_id = $(this).attr('id');  
                    $.post(
                        '/admin_del/',
                        {'obj_id': obj_id},
                        function() {
                            $("div.check").fadeOut('slow');
                            $("div.delete").fadeOut('slow',
                                function(){
                                    $("div.delete").html("this object has been deleted");
                                    $("div.delete").fadeIn('slow');
                                }
                            );
                        }
                    );
                }
            );
        });
        $(function(){
            $("body").on("click","span.cancel", 
                function(){
                    $("div.check").toggle();              
                }
            );
        });

    }
);
//end of line