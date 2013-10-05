$(document).ready(
    function() {
        $(function(){
            $("body").on("click","#printshelf_toggle", 
                function(){
                	obj_id = $(this).attr('class');
                    $('.printshelf_select').slideToggle('fast');
			        $(function(){
			            $("body").on("click",".to_print", 
			                function(){
            					$('.printshelf').slideToggle('fast');
			                    $.post(
			                        '/printshelf_add/',
			                        {'obj_id': obj_id, 'to_print':'to_print'},
                                    function(){
                                        $('.printshelf').remove();
                                        $('.refresh_info').slideToggle('fast');
                                    }
			                    );
			                }
			            );
			        });
                    $(function(){
                        $("body").on("click",".printed", 
                            function(){
                                $('.printshelf').fadeOut('slow',
                                    function(){
                                        $('.printshelf').remove();
                                        $('.refresh_info').fadeIn('fast');
                                    }

                                );
                                $('.rating_area').fadeOut('fast',
                                    function () {
                                        $('.refresh_to_rate').fadeIn('fast');
                                    }
                                );
                                $.post(
                                    '/printshelf_add/',
                                    {'obj_id': obj_id, 'printed':'printed'}
                                );
                            }
                        );
                    });
                }
            );
        });
    }
);
//end of line