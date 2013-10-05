$(document).ready(
    function() {
/*
        $(function(){
            $("body").on("mouseenter","span.one_star",
                function(){
                    obj_id = $(this).attr('id');
                    $("a#onestar"+obj_id).removeClass("one_star").addClass("star_highlighted");
                }
            ).on("mouseleave","span.one_star",
                function(){
                    obj_id = $(this).attr('id');
                    $("a#onestar"+obj_id).removeClass("star_highlighted").addClass("one_star");
                }
            );
        });

        $(function(){
            $("body").on("mouseenter","span.two_star", 
                function(){
                    obj_id = $(this).attr('id');
                    $("a#onestar"+obj_id).removeClass("one_star").addClass("star_highlighted");
                    $("a#twostar"+obj_id).removeClass("two_star").addClass("star_highlighted");
                }
            ).on("mouseleave","span.two_star",
                function(){
                    obj_id = $(this).attr('id');
                    $("a#onestar"+obj_id).removeClass("star_highlighted").addClass("one_star"); 
                    $("a#twostar"+obj_id).removeClass("star_highlighted").addClass("two_star");
                }
            );
        });


        $(function(){
            $("body").on("mouseenter","span.three_star", 
                function(){
                    obj_id = $(this).attr('id');
                    $("a#onestar"+obj_id).removeClass("one_star").addClass("star_highlighted");
                    $("a#twostar"+obj_id).removeClass("two_star").addClass("star_highlighted");
                    $("a#threestar"+obj_id).removeClass("three_star").addClass("star_highlighted");
                }
            ).on("mouseleave","span.three_star",
                function(){
                    obj_id = $(this).attr('id');
                    $("a#onestar"+obj_id).removeClass("star_highlighted").addClass("one_star");
                    $("a#twostar"+obj_id).removeClass("star_highlighted").addClass("two_star");
                    $("a#threestar"+obj_id).removeClass("star_highlighted").addClass("three_star");
                }
            );
        });

        $(function(){
            $("body").on("mouseenter","span.four_star", 
                function(){
                    obj_id = $(this).attr('id');
                    $("a#onestar"+obj_id).removeClass("one_star").addClass("star_highlighted");
                    $("a#twostar"+obj_id).removeClass("two_star").addClass("star_highlighted");
                    $("a#threestar"+obj_id).removeClass("three_star").addClass("star_highlighted");
                    $("a#fourstar"+obj_id).removeClass("four_star").addClass("star_highlighted");
                }
            ).on("mouseleave","span.four_star",
                function(){
                    obj_id = $(this).attr('id');
                    $("a#onestar"+obj_id).removeClass("star_highlighted").addClass("one_star");
                    $("a#twostar"+obj_id).removeClass("star_highlighted").addClass("two_star");
                    $("a#threestar"+obj_id).removeClass("star_highlighted").addClass("three_star");
                    $("a#fourstar"+obj_id).removeClass("star_highlighted").addClass("four_star");
                }
            );
        });

        $(function(){
            $("body").on("mouseenter","span.five_star",
                function(){
                    obj_id = $(this).attr('id');
                    $("a#onestar"+obj_id).removeClass("one_star").addClass("star_highlighted");
                    $("a#twostar"+obj_id).removeClass("two_star").addClass("star_highlighted");
                    $("a#threestar"+obj_id).removeClass("three_star").addClass("star_highlighted");
                    $("a#fourstar"+obj_id).removeClass("four_star").addClass("star_highlighted");
                    $("a#fivestar"+obj_id).removeClass("five_star").addClass("star_highlighted");
                }
            ).on("mouseleave","span.five_star",
                function(){
                    obj_id = $(this).attr('id');
                    $("a#onestar"+obj_id).removeClass("star_highlighted").addClass("one_star");
                    $("a#twostar"+obj_id).removeClass("star_highlighted").addClass("two_star");
                    $("a#threestar"+obj_id).removeClass("star_highlighted").addClass("three_star");
                    $("a#fourstar"+obj_id).removeClass("star_highlighted").addClass("four_star");
                    $("a#fivestar"+obj_id).removeClass("star_highlighted").addClass("five_star");
                }
            );
        });
//------------------------        
        $(function(){
            $("body").on("mouseenter","span.one_rated",
                function(){
                    obj_id = $(this).attr('id');
                    $("span.one_rated").removeClass("one_rated").addClass("star_highlighted");
                }
            ).on("mouseleave","span.one_rated",
                function(){
                    obj_id = $(this).attr('id');
                    $("a#onestar"+obj_id).removeClass("star_highlighted").addClass("one_rated");
                }
            );
        });

        $(function(){
            $("body").on("mouseenter","span.two_star", 
                function(){
                    obj_id = $(this).attr('id');
                    $("a#onestar"+obj_id).removeClass("one_star").addClass("star_highlighted");
                    $("a#twostar"+obj_id).removeClass("two_star").addClass("star_highlighted");
                }
            ).on("mouseleave","span.two_star",
                function(){
                    obj_id = $(this).attr('id');
                    $("a#onestar"+obj_id).removeClass("star_highlighted").addClass("one_star"); 
                    $("a#twostar"+obj_id).removeClass("star_highlighted").addClass("two_star");
                }
            );
        });


        $(function(){
            $("body").on("mouseenter","span.three_star", 
                function(){
                    obj_id = $(this).attr('id');
                    $("a#onestar"+obj_id).removeClass("one_star").addClass("star_highlighted");
                    $("a#twostar"+obj_id).removeClass("two_star").addClass("star_highlighted");
                    $("a#threestar"+obj_id).removeClass("three_star").addClass("star_highlighted");
                }
            ).on("mouseleave","span.three_star",
                function(){
                    obj_id = $(this).attr('id');
                    $("a#onestar"+obj_id).removeClass("star_highlighted").addClass("one_star");
                    $("a#twostar"+obj_id).removeClass("star_highlighted").addClass("two_star");
                    $("a#threestar"+obj_id).removeClass("star_highlighted").addClass("three_star");
                }
            );
        });

        $(function(){
            $("body").on("mouseenter","span.four_star", 
                function(){
                    obj_id = $(this).attr('id');
                    $("a#onestar"+obj_id).removeClass("one_star").addClass("star_highlighted");
                    $("a#twostar"+obj_id).removeClass("two_star").addClass("star_highlighted");
                    $("a#threestar"+obj_id).removeClass("three_star").addClass("star_highlighted");
                    $("a#fourstar"+obj_id).removeClass("four_star").addClass("star_highlighted");
                }
            ).on("mouseleave","span.four_star",
                function(){
                    obj_id = $(this).attr('id');
                    $("a#onestar"+obj_id).removeClass("star_highlighted").addClass("one_star");
                    $("a#twostar"+obj_id).removeClass("star_highlighted").addClass("two_star");
                    $("a#threestar"+obj_id).removeClass("star_highlighted").addClass("three_star");
                    $("a#fourstar"+obj_id).removeClass("star_highlighted").addClass("four_star");
                }
            );
        });

        $(function(){
            $("body").on("mouseenter","span.five_star",
                function(){
                    obj_id = $(this).attr('id');
                    $("a#onestar"+obj_id).removeClass("one_star").addClass("star_highlighted");
                    $("a#twostar"+obj_id).removeClass("two_star").addClass("star_highlighted");
                    $("a#threestar"+obj_id).removeClass("three_star").addClass("star_highlighted");
                    $("a#fourstar"+obj_id).removeClass("four_star").addClass("star_highlighted");
                    $("a#fivestar"+obj_id).removeClass("five_star").addClass("star_highlighted");
                }
            ).on("mouseleave","span.five_star",
                function(){
                    obj_id = $(this).attr('id');
                    $("a#onestar"+obj_id).removeClass("star_highlighted").addClass("one_star");
                    $("a#twostar"+obj_id).removeClass("star_highlighted").addClass("two_star");
                    $("a#threestar"+obj_id).removeClass("star_highlighted").addClass("three_star");
                    $("a#fourstar"+obj_id).removeClass("star_highlighted").addClass("four_star");
                    $("a#fivestar"+obj_id).removeClass("star_highlighted").addClass("five_star");
                }
            );
        });


*/
//------------------------        
        $(function(){
            $("body").on("click","span#star1", 
                function(){
                    obj_id = $("span#one_star").attr('class');
                    $.post(
                        '/rate/',
                        {'obj_id': obj_id, 'rate': 1},
                        function() {
                            $("a#onestar"+obj_id).html('★');
                            $("a#twostar"+obj_id).html('☆');
                            $("a#threestar"+obj_id).html('☆');
                            $("a#fourstar"+obj_id).html('☆');
                            $("a#fivestar"+obj_id).html('☆');
                            $("span#star1").addClass('user_rated');
                            $("span#star2").removeClass('user_rated');
                            $("span#star3").removeClass('user_rated');
                            $("span#star4").removeClass('user_rated');
                            $("span#star5").removeClass('user_rated');
                        }
                    );              
                }
            );
        });

        $(function(){
            $("body").on("click","span#star2", 
                function(){
                    obj_id = $("span#two_star").attr('class');
                    $("a#onestar"+obj_id).html('★');
                    $("a#twostar"+obj_id).html('★');
                    $("a#threestar"+obj_id).html('☆');
                    $("a#fourstar"+obj_id).html('☆');
                    $("a#fivestar"+obj_id).html('☆');
                    $("span#star1").addClass('user_rated');
                    $("span#star2").addClass('user_rated');
                    $("span#star3").removeClass('user_rated');
                    $("span#star4").removeClass('user_rated');
                    $("span#star5").removeClass('user_rated');                    
                    $.post(
                        '/rate/',
                        {'obj_id': obj_id, 'rate': 2}
                    );              
                }
            );
        });

        $(function(){
            $("body").on("click","span#star3", 
                function(){
                    obj_id = $("span#three_star").attr('class');
                    $("a#onestar"+obj_id).html('★');
                    $("a#twostar"+obj_id).html('★');
                    $("a#threestar"+obj_id).html('★');
                    $("a#fourstar"+obj_id).html('☆');
                    $("a#fivestar"+obj_id).html('☆');
                    $("span#star1").addClass('user_rated');
                    $("span#star2").addClass('user_rated');
                    $("span#star3").addClass('user_rated');
                    $("span#star4").removeClass('user_rated');
                    $("span#star5").removeClass('user_rated');                    
                    $.post(
                        '/rate/',
                        {'obj_id': obj_id, 'rate': 3}
                    );              
                }
            );
        });

        $(function(){
            $("body").on("click","span#star4", 
                function(){
                    obj_id = $("span#four_star").attr('class');
                    $("a#onestar"+obj_id).html('★');
                    $("a#twostar"+obj_id).html('★');
                    $("a#threestar"+obj_id).html('★');
                    $("a#fourstar"+obj_id).html('★');
                    $("a#fivestar"+obj_id).html('☆');
                    $("span#star1").addClass('user_rated');
                    $("span#star2").addClass('user_rated');
                    $("span#star3").addClass('user_rated');
                    $("span#star4").addClass('user_rated');
                    $("span#star5").removeClass('user_rated');                    
                    $.post(
                        '/rate/',
                        {'obj_id': obj_id, 'rate': 4}
                    );              
                }
            );          
        });  

        $(function(){
            $("body").on("click","span#star5", 
                function(){
                    obj_id = $("span#five_star").attr('class');
                    $("a#onestar"+obj_id).html('★');
                    $("a#twostar"+obj_id).html('★');
                    $("a#threestar"+obj_id).html('★');
                    $("a#fourstar"+obj_id).html('★');
                    $("a#fivestar"+obj_id).html('★');
                    $("span#star1").addClass('user_rated');
                    $("span#star2").addClass('user_rated');
                    $("span#star3").addClass('user_rated');
                    $("span#star4").addClass('user_rated');
                    $("span#star5").addClass('user_rated');                    
                    $.post(
                        '/rate/',
                        {'obj_id': obj_id, 'rate': 5}
                    );              
                }
            );
        });                   
    }
);
//end of line