$(document).ready(
    function() {
        $(function(){
            $("body").on("click","#block_toggle", 
                function(){
                	blockee_id = $(this).attr('class');
                    $('.check_block').fadeToggle('slow');
			        $(function(){
			            $("body").on("click",".yes_block", 
			                function(){
            					$('.check_block').fadeOut('slow');
			                    $('.block_box').fadeOut('slow',
			                    	function(){
			                    		$('.unblock_box').fadeIn('slow');
			                    	}
			                    );
			                    $.post(
			                        '/block/',
			                        {'blockee_id': blockee_id, 'block':'block'},
                                    function(){
                                        $('#block_toggle').remove();
                                    }
			                    );
			                }
			            );
			        });
                }
            );
        });
        $(function(){
            $("body").on("click",".cancel_block", 
                function(){
                    $('.check_block').fadeOut('slow');
                }
            );
        });
        $(function(){
            $("body").on("click","#unblock_toggle", 
                function(){
                	blockee_id = $(this).attr('class');
                    $('.check_unblock').fadeToggle('slow');
			        $(function(){
			            $("body").on("click",".yes_unblock", 
			                function(){
            					$('.check_unblock').fadeOut('slow');
			                    $('.unblock_box').fadeOut('slow',
			                    	function(){
			                    		$('.block_box').fadeIn('slow');
			                    	}
			                    );
			                    $.post(
			                        '/block/',
			                        {'blockee_id': blockee_id, 'unblock': 'unblock'},
                                    function(){
                                        $('#unblock_toggle').remove();
                                    }
			                    );
			                }
			            );
			        });
                }
            );
        });
        $(function(){
            $("body").on("click",".cancel_unblock", 
                function(){
                    $('.check_unblock').fadeOut('slow');
                }
            );
        });
    }
);
//end of line