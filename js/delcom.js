$(document).ready(
    function() {
        $(function(){
            $("body").on("click",".delete", 
                function(){
                    com_id = $(this).attr('id');                    
                    $(".check_delete_" + com_id).toggle();
                    $("body").on("click",".yes_delete_" + com_id, 
                        function(){
                            com_id = $(this).attr('id')
                            $.post(
                                '/delcom/',
                                {'com_id': com_id},
                                function() {
                                    $(".comment_"+com_id).fadeOut('slow', 
                                        function() {
                                            $(".comment_text_"+com_id).fadeOut('slow', 
                                                function() {
                                                    $(".comment_text_"+com_id).html("deleted");
                                                    $(".comment_text_"+com_id).fadeIn('slow');
                                                });
                                            $(".comment_data_"+com_id).remove();
                                            $(".comment_"+com_id).fadeIn('slow');
                                        });
                                            
                                          
                                }
                            ); 
                        }
                    );
                }
            );
        });
        $(function(){
            $("body").on("click",".cancel_delete", 
                function(){
                    com_id = $(this).attr('id');                    
                    $(".check_delete_" + com_id).toggle();
                }
            );
        });


    }
);
//end of line