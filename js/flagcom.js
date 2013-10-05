$(document).ready(
    function() {
        $(function(){
            $("body").on("click","span#flagcom", 
                function(){
                    com_id = $(this).attr('class');  
                    var theint = parseInt($("span#flagsumcom"+com_id).html());
                    theint++;
                    $("a#flagupcom"+com_id).html('⚑');
                    $(this).removeAttr('id').attr('id','flaggedcom');
                    $("span#flagsumcom"+com_id).html(theint);  
                    $.post(
                        '/flagcom/',
                        {'com_id': com_id, 'flagcom': 1},
                        function() {
               
                        }
                    );
                }
            );
        });
        $(function(){
            $("body").on("click","span#flaggedcom", 
                function(){
                    com_id = $(this).attr('class');  
                    var theint = parseInt($("span#flagsumcom"+com_id).html());
                    theint--;                            
                    $("a#flagupcom"+com_id).html('⚐');  
                    $(this).removeAttr('id').attr('id','flagcom');
                    $("span#flagsumcom"+com_id).html(theint);
                    $.post(
                        '/flagcom/',
                        {'com_id': com_id, 'flagcom': 0},
                        function() {

                        }
                    );
                }
            );
        });
    }
);
//end of line