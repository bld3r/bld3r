$(document).ready(
    function() {
        $(function(){
            $("body").on("click","#voteupcom", 
                function(){
                    com_id = $(this).attr('class');
                    var theint = parseInt($("#votesumcom"+com_id).html());
                    theint++;
                    $("#vucom"+com_id).html('▲').css("color", "#0077cc");
                    $("#vdcom"+com_id).html('▼').css("color", "#999");
                    $(this).removeAttr('id').attr('id','votedupcom');
                    $("."+com_id+"#votedowncom").removeAttr('id').attr('id','votedown2com');                            
                    $("#votesumcom"+com_id).html(theint);                            
                    $.post(
                        '/votecom/',
                        {'com_id': com_id, 'votecom': 1},
                        function() {

                        }
                    );              
                }
            );
        });

        $(function(){
            $("body").on("click","#votedupcom", 
                function(){
                    com_id = $(this).attr('class');
                    var theint = parseInt($("#votesumcom"+com_id).html());
                    theint--;                            
                    $("#vucom"+com_id).html('▲').css("color", "#999");
                    $("#vdcom"+com_id).html('▼').css("color", "#999");
                    $(this).removeAttr('id').attr('id','voteupcom');
                    $("."+com_id+"#votedown2com").removeAttr('id').attr('id','votedowncom');
                    $("#votesumcom"+com_id).html(theint);
                    $.post(
                        '/votecom/',
                        {'com_id': com_id, 'votecom': 0},
                        function() {

                        }
                    );              
                }
            );
        });

        $(function(){
            $("body").on("click","#votedowncom", 
                function(){
                    com_id = $(this).attr('class');
                    var theint = parseInt($("#votesumcom"+com_id).html());
                    theint--;                       
                    $("#vdcom"+com_id).html('▼').css("color", "#d45e6a");
                    $("#vucom"+com_id).html('▲').css("color", "#999");
                    $(this).removeAttr('id').attr('id','voteddowncom');
                    $("."+com_id+"#voteupcom").removeAttr('id').attr('id','voteup2com');
                    $("#votesumcom"+com_id).html(theint);
                    $.post(
                        '/votecom/',
                        {'com_id': com_id, 'votecom': -1},
                        function() {

                        }
                    );              
                }
            );
        });
        $(function(){
            $("body").on("click","#voteddowncom", 
                function(){
                    com_id = $(this).attr('class');
                    var theint = parseInt($("#votesumcom"+com_id).html());
                    theint++;                       
                    $("#vdcom"+com_id).html('▼').css("color", "#999");
                    $("#vucom"+com_id).html('▲').css("color", "#999");
                    $(this).removeAttr('id').attr('id','votedowncom');
                    $("."+com_id+"#voteup2com").removeAttr('id').attr('id','voteupcom');
                    $("#votesumcom"+com_id).html(theint);
                    $.post(
                        '/votecom/',
                        {'com_id': com_id, 'votecom': 0},
                        function() {

                        }
                    );              
                }
            );
        });  

        $(function(){
            $("body").on("click","#voteup2com", 
                function(){
                    com_id = $(this).attr('class');
                    var theint = parseInt($("#votesumcom"+com_id).html());
                    theint++;
                    theint++;                       
                    $("#vdcom"+com_id).html('▼').css("color", "#999");
                    $("#vucom"+com_id).html('▲').css("color", "#0077cc");
                    $(this).removeAttr('id').attr('id','votedupcom');
                    $("."+com_id+"#voteddowncom").removeAttr('id').attr('id','votedown2com');
                    $("#votesumcom"+com_id).html(theint);
                    $.post(
                        '/votecom/',
                        {'com_id': com_id, 'votecom': 1},
                        function() {

                        }
                    );              
                }
            );
        });  

        $(function(){
            $("body").on("click","#votedown2com", 
                function(){
                    com_id = $(this).attr('class');
                    var theint = parseInt($("#votesumcom"+com_id).html());
                    theint--;
                    theint--;                       
                    $("#vdcom"+com_id).html('▼').css("color", "#d45e6a");
                    $("#vucom"+com_id).html('▲').css("color", "#999");
                    $(this).removeAttr('id').attr('id','voteddowncom');
                    $("."+com_id+"#votedupcom").removeAttr('id').attr('id','voteup2com');
                    $("#votesumcom"+com_id).html(theint);
                    $.post(
                        '/votecom/',
                        {'com_id': com_id, 'votecom': -1},
                        function() {

                        }
                    );              
                }
            );
        });                                
    }
);
//end of line