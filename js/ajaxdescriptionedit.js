$(document).ready(
    function() {
        $(function(){
            $("body").on("click",".open_info_edit_slide", 
                function(){
                    $(".info_edit_slide").slideToggle('fast');
                }
            );
        });

        $(function(){
            $("body").on("click",".open_description_edit_slide", 
                function(){
                    $(".info_edit_slide").slideToggle('fast');
                    $(".description_edit").fadeIn();
                }
            );
            $("body").on("click",".cancel_description_submit", 
                function(){
                    $(".description_edit").hide();
                }
            );
        });

        $(function(){
            $("body").on("click",".description_submit", 
                function(){
                    description_text = $('#description_text').val();
                    description_obj_id = $('#description_obj_id').val();
                    description_user_id = $('#description_user_id').val();
                    description_verify = $('#description_verify').val();
                    //$(".message_box").animate({'height': "0", opacity:'0'}, 500);
                    //$(".message_box").fadeTo('slow', 0);              
                    $.post(
                        '/ajaxdescription/',
                        {"description_text": description_text, 
                         "description_obj_id": description_obj_id,
                         "description_user_id": description_user_id,
                         "verify": description_verify
                        }
                        );
                    $('.description_text_holder').fadeOut(1000);
                    $('.description_edit').hide();   
                    $(".description_none_default").show();                                     
                    $('.description_text_holder').fadeIn(2000).html(description_text);                
                }
            );
        });


    }
);
//end of line