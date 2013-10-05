$(document).ready(
    function() {

        $(function(){
            $("body").on("click",".open_tags_edit", 
                function(){
                    $(".tags_edit").fadeToggle();
                }
            );
            $("body").on("click",".cancel_tag_submit", 
                function(){
                    $(".tags_edit").fadeOut();
                }
            );
        });

        $(function(){
            $("body").on("click",".tag_submit", 
                function(){
                    author_tags = $('#author_tag_edit_tags').val();
                    public_tags = $('#public_tag_edit_tags').val();
                    obj_num = $('#author_tag_edit_obj_id').val();
                    user_id = $('#user_id_input').val();
                    //$(".message_box").animate({'height': "0", opacity:'0'}, 500);
                    //$(".message_box").fadeTo('slow', 0);              

                    $.post(
                        '/ajaxtag/',
                        {'obj_num': obj_num, 
                         'author_tags': author_tags,
                         'public_tags': public_tags,
                         'user_id': user_id}
                        );
                    $('.tag_list').fadeOut(1000);                    
                    $('.tags_edit').fadeOut(1000);
                    $('.tag_list').html(author_tags+' '+public_tags).fadeIn(2000); 
                }
            );
        });


    }
);
//end of line