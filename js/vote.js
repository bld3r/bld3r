$(document).ready(
    function() {
        $(function(){
            $("body").on("click","#voteup", 
                function(){
                    obj_id = $(this).attr('class');
                    var theint = parseInt($("#votesum"+obj_id).html());
                    theint++;     
                    $("#vu"+obj_id).html('▲').css("color", "#0077cc");
                    $("#vd"+obj_id).html('▼').css("color", "#999");
                    $(this).removeAttr('id').attr('id', 'votedup');
                    $("."+obj_id+"#votedown").removeAttr('id').attr('id', 'votedown2');   
                    $("#votesum"+obj_id).html(theint);                                               
                    $.post(
                        '/vote/',
                        {'obj_id': obj_id, 'vote': 1}
                    );              
                }
            );
        });

        $(function(){
            $("body").on("click","#votedup", 
                function(){
                    obj_id = $(this).attr('class');
                    var theint = parseInt($("#votesum"+obj_id).html());
                    theint--;     
                    $("#vu"+obj_id).html('▲').css("color", "#999");
                    $("#vd"+obj_id).html('▼').css("color", "#999");
                    $(this).removeAttr('id').attr('id', 'voteup');
                    $("."+obj_id+"#votedown2").removeAttr('id').attr('id', 'votedown');
                    $("#votesum"+obj_id).html(theint);      
                    $.post(
                        '/vote/',
                        {'obj_id': obj_id, 'vote': 0}
                    );              
                }
            );
        });

        $(function(){
            $("body").on("click","#votedown", 
                function(){
                    obj_id = $(this).attr('class');
                    var theint = parseInt($("#votesum"+obj_id).html());
                    theint--;   
                    $("#vd"+obj_id).html('▼').css("color", "#d45e6a");
                    $("#vu"+obj_id).html('▲').css("color", "#999");
                    $(this).removeAttr('id').attr('id', 'voteddown');
                    $("."+obj_id+"#voteup").removeAttr('id').attr('id', 'voteup2');
                    $("#votesum"+obj_id).html(theint);                                                  
                    $.post(
                        '/vote/',
                        {'obj_id': obj_id, 'vote': -1}
                    );              
                }
            );
        });
        $(function(){
            $("body").on("click","#voteddown", 
                function(){
                    obj_id = $(this).attr('class');
                    var theint = parseInt($("#votesum"+obj_id).html());
                    theint++;  
                    $("#vd"+obj_id).html('▼').css("color", "#999");
                    $("#vu"+obj_id).html('▲').css("color", "#999");
                    $(this).removeAttr('id').attr('id', 'votedown');
                    $("."+obj_id+"#voteup2").removeAttr('id').attr('id', 'voteup');
                    $("#votesum"+obj_id).html(theint);                                                
                    $.post(
                        '/vote/',
                        {'obj_id': obj_id, 'vote': 0}
                    );              
                }
            );
        });  

        $(function(){
            $("body").on("click","#voteup2", 
                function(){
                    obj_id = $(this).attr('class');
                    var theint = parseInt($("#votesum"+obj_id).html());
                    theint++;
                    theint++; 
                    $("#vd"+obj_id).html('▼').css("color", "#999");
                    $("#vu"+obj_id).html('▲').css("color", "#0077cc");
                    $(this).removeAttr('id').attr('id', 'votedup');
                    $("."+obj_id+"#voteddown").removeAttr('id').attr('id', 'votedown2');
                    $("#votesum"+obj_id).html(theint);                                       
                    $.post(
                        '/vote/',
                        {'obj_id': obj_id, 'vote': 1}
                    );              
                }
            );
        });  

        $(function(){
            $("body").on("click","#votedown2", 
                function(){
                    obj_id = $(this).attr('class');
                    var theint = parseInt($("#votesum"+obj_id).html());
                    theint--;
                    theint--;           
                    $("#vd"+obj_id).html('▼').css("color", "#d45e6a");
                    $("#vu"+obj_id).html('▲').css("color", "#999");
                    $(this).removeAttr('id').attr('id', 'voteddown');
                    $("."+obj_id+"#votedup").removeAttr('id').attr('id', 'voteup2');
                    $("#votesum"+obj_id).html(theint);                                   
                    $.post(
                        '/vote/',
                        {'obj_id': obj_id, 'vote': -1}
                    );              
                }
            );
        });                                
    }
);
//end of line