$(document).ready(
    function() {
        $(function(){
            $("body").on("click",".edit_comment", 
                function(){
                    com_id = $(this).attr('id');                                        
                    $(".comment_text_" + com_id).fadeOut('slow',
                        function() {
                            $(".comment_edit_textbox_" + com_id).fadeIn('slow');
                        }
                    );
                    $(this).fadeOut('slow',
                        function() {
                            $(this).removeClass('edit_comment').addClass('trash_edits');
                            $(this).html('cancel edits');
                            $(this).fadeIn('slow');
                            
                            
                        }
                    );
                    $(function() {
                        $("body").on("click",".save_edit",
                            function() {
                                save_id = $(this).attr('id');
                                text = $('.text_changes_to_' + save_id).val();
                                verify = $('.verify_user').attr('id');
                                $(".comment_edit_textbox_" + save_id).fadeOut('slow',
                                    function() {
                                        $(".comment_text_" + save_id).html(text);
                                        $(".comment_text_" + save_id).fadeIn('slow');
                                    }
                                );
                                var cancel_edit_div = '.comment_data_'+ save_id;
                                cancel_edit_div += " .trash_edits";
                                $(cancel_edit_div).fadeOut('slow',
                                    function() {
                                        $(this).removeClass('trash_edits').addClass('edit_comment');
                                        $(this).html('edit');
                                        $(this).fadeIn('slow');
                                    }
                                );
                                $.post(
                                    '/editcom/',
                                    {'save_id': save_id, 'text': text, 'verify': verify},
                                    function(){
                                        
                                    }
                                );
                            }
                        );
                    });
                }
            );
        });
        $(function(){
            $("body").on("click",".trash_edits", 
                function(){
                    com_id = $(this).attr('id');                    
                    $(".comment_edit_textbox_" + com_id).fadeOut('slow',
                        function() {
                            $(".comment_text_" + com_id).fadeIn('slow');
                            $(this).removeClass('trash_edits').addClass('edit_comment');
                        }
                    );
                    $(this).fadeOut('slow',
                        function() {
                            $(this).removeClass('trash_edits').addClass('edit_comment');
                            $(this).html('edit');
                            $(this).fadeIn('slow');
                        }
                    );
                }
            );
        });
    }
);
//end of line