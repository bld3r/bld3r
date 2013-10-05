$(document).ready(
    function() {


        $(function(){
            $("body").on("click",".message_submit", 
                function(){
                    the_message = $('#the_textarea').val();
                    userpage_num = $('#userpage_num').html();
                    $(".message_box").animate({'height': "0", opacity:'0'}, 500);
                    //$(".message_box").fadeTo('slow', 0);              

                    $.post('/sendmessage/',{"message": the_message, "userpage_num": userpage_num});
                }
            );
        });


    }
);
//end of line