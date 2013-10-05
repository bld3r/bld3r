$(document).ready(
    function() {
        $(function(){
            $("body").on("click","span#flag", 
                function(){
                    obj_id = $(this).attr('class');  
                    var theint = parseInt($("span#flagsum"+obj_id).html());
                    theint++;    
                    $("a#flagup"+obj_id).html('Flagged');  
                    $(this).removeAttr('id').attr('id', 'flagged');
                    $("span#flagsum"+obj_id).html(theint);                                               
                    $.post(
                        '/flag/',
                        {'obj_id': obj_id, 'flag': 1}
                    );              
                }
            );
        });

        $(function(){
            $("body").on("click","span#flagged", 
                function(){
                    obj_id = $(this).attr('class');  
                    var theint = parseInt($("span#flagsum"+obj_id).html());
                    theint--;
                    $("a#flagup"+obj_id).html('unflag');  
                    $(this).removeAttr('id').attr('id', 'flag');
                    $("span#flagsum"+obj_id).html(theint);                                                   
                    $.post(
                        '/flag/',
                        {'obj_id': obj_id, 'flag': 0}
                    );              
                }
            );
        });


    }
);
//end of line