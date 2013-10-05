$(document).ready(
    function() {
        $(function(){
            $("body").on("click","#printshelf_edit_to_print_toggle", 
                function(){
                	obj_id = $(this).attr('class');
                    printshelf_id = $('#printshelf_id').attr('class');
                    $('.printshelf_edit_'+obj_id).fadeToggle('slow');
                    $("body").on("click",".printshelf_edit_button_"+obj_id, 
                        function(){
                            $('.remove_check'+obj_id).fadeOut('slow',
                                function() {
                                    $('.move_to_has_printed_'+obj_id).fadeIn('slow');
                                    $(function(){
                                        $("body").on("click",".move_check_"+obj_id, 
                                            function(){
                                                $('.move_to_has_printed_'+obj_id).fadeOut('slow');
                                                $('.printshelf_edit_'+obj_id).fadeOut('slow');
                                                $('.to_print_obj_'+obj_id).fadeOut('slow',
                                                    function(){
                                                        $clone = $('.obj_data_'+obj_id).clone();
                                                        $('.has_printed_empty').fadeOut('slow',
                                                            function(){
                                                                $(".return_to_rate").fadeIn('slow');
                                                                $(".has_printed_list").prepend("<br>");
                                                                $(".has_printed_list").prepend(
                                                                    $clone.hide().fadeIn('slow')
                                                                );
                                                            }
                                                        );
                                                    }
                                                );
                                                $.post(
                                                    '/printshelf_add/',
                                                    {'obj_id': obj_id, 'printed':'printed'},
                                                    function(){
                                                        $('.printshelf_edit_'+obj_id).remove();
                                                    }
                                                );
                                            }
                                        );
                                    }); 
                                    $(function(){
                                        $("body").on("click",".cancel_check_"+obj_id, 
                                            function(){
                                                $('.move_to_has_printed_'+obj_id).fadeOut('slow');
                                                $('.printshelf_edit_'+obj_id).fadeOut('slow');
                                            }
                                        );
                                    });                                                                       
                                }
                            );
                        }
                    );
                    $("body").on("click",".printshelf_remove_"+obj_id, 
                        function(){
                            $('.move_to_has_printed_'+obj_id).fadeOut('slow',
                                function() {
                                    $('.remove_check'+obj_id).fadeIn('slow');
                                    $(function(){
                                        $("body").on("click",".yes_remove"+obj_id, 
                                            function(){
                                                $('.to_print_obj_'+obj_id).fadeOut('slow',
                                                    function(){
                                                        $('.to_print_obj_'+obj_id).remove();
                                                    }
                                                );
                                                $.post(
                                                    '/printshelf_remove/',
                                                    {'obj_id': obj_id, 'remove':'to_print', 'printshelf_id': printshelf_id}
                                                );
                                            }
                                        );
                                    });
                                    $(function(){
                                        $("body").on("click",".cancel_remove"+obj_id, 
                                            function(){
                                                $('.remove_check'+obj_id).fadeOut('slow');
                                                $('.printshelf_edit_'+obj_id).fadeOut('slow');
                                            }
                                        );
                                    });                                    
                                }
                            );
                        }
                    );
                }
            );
        });
        $(function(){
            $("body").on("click","#printshelf_edit_has_printed_toggle", 
                function(){
                    obj_id = $(this).attr('class');
                    printshelf_id = $('#printshelf_id').attr('class');
                    $('.printshelf_edit_'+obj_id).fadeToggle('slow');

                    $("body").on("click",".printshelf_edit_button_"+obj_id, 
                        function(){
                            $('.remove_check'+obj_id).fadeOut('slow',
                                function() {
                                    $('.move_to_has_printed_'+obj_id).fadeIn('slow');
                                    $(function(){
                                        $("body").on("click",".move_check_"+obj_id, 
                                            function(){
                                                $('.move_to_has_printed_'+obj_id).fadeOut('slow');
                                                $('.printshelf_edit_'+obj_id).fadeOut('slow');
                                                $('.printed_obj_'+obj_id).fadeOut('slow',
                                                    function(){
                                                        $clone = $('.obj_data_'+obj_id).clone();
                                                        $('.to_print_empty').fadeOut('slow',
                                                            function(){
                                                                $(".to_print_list").prepend("<br>");
                                                                $(".to_print_list").prepend(
                                                                    $clone.hide().fadeIn('slow')
                                                                );
                                                            }
                                                        );
                                                    }
                                                );
                                                $.post(
                                                    '/printshelf_add/',
                                                    {'obj_id': obj_id, 'to_print':'to_print'},
                                                    function(){
                                                        $('.printshelf_edit_'+obj_id).remove();
                                                    }
                                                );
                                            }
                                        );
                                    }); 
                                    $(function(){
                                        $("body").on("click",".cancel_check_"+obj_id, 
                                            function(){
                                                $('.move_to_has_printed_'+obj_id).fadeOut('slow');
                                                $('.printshelf_edit_'+obj_id).fadeOut('slow');
                                            }
                                        );
                                    });                                                                       
                                }
                            );
                        }
                    );

                    $("body").on("click",".printshelf_remove_"+obj_id, 
                        function(){
                            $('.move_to_has_printed_'+obj_id).fadeOut('slow',
                                function() {
                                    $('.remove_check'+obj_id).fadeIn('slow');
                                    $(function(){
                                        $("body").on("click",".yes_remove"+obj_id, 
                                            function(){
                                                $('.printed_obj_'+obj_id).fadeOut('slow',
                                                    function(){
                                                        $('.printed_obj_'+obj_id).remove();
                                                    }
                                                );
                                                $.post(
                                                    '/printshelf_remove/',
                                                    {'obj_id': obj_id, 'remove':'has_printed', 'printshelf_id': printshelf_id}
                                                );
                                            }
                                        );
                                    });
                                    $(function(){
                                        $("body").on("click",".cancel_remove"+obj_id, 
                                            function(){
                                                $('.remove_check'+obj_id).fadeOut('slow');
                                                $('.printshelf_edit_'+obj_id).fadeOut('slow');
                                            }
                                        );
                                    });                                    
                                }
                            );
                        }
                    );

                }
            );
        });
    }
);
//end of line