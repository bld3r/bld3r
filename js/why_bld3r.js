$(document).ready(
    function() {
        $(function(){
            $("body").on("click",".why_bld3r_button", 
                function(){
                    $(".why_bld3r_all").show();
                    $(".why_bld3r_button").fadeOut(500);
                    $(".why_bld3r_container").animate({"opacity":"0",}, 500, function() {
                        $(".why_bld3r_reason").animate({"width": "800px"}, 1000);
                        $(".why_bld3r_container").css({"cursor":"auto"});
                        $(".why_bld3r_container").animate({"opacity":"1"}, 1, function() {
                            $(".why_bld3r").animate({
                                "opacity":"1"
                            }, 1000, function() {
                                $(".why_bld3r_close").fadeIn(2000);
                                $(".why_bld3r").animate({"opacity":"1",}, 2000, function() {
                                    $(".why_bld3r_reason_1").fadeIn(2000, function() {
                                        $(".why_bld3r_reason_2").fadeIn(2000, function() {
                                            $(".why_bld3r_reason_3").fadeIn(2000, function() {
                                                $(".why_bld3r_reason_4").fadeIn(2000, function() {
                                                    $(".why_bld3r").animate({"height":"209"}, 4000, function() {
                                                        $(".why_bld3r").animate({"height":"280"}, 1000, function() {
                                                            $(".why_bld3r_reason_5").fadeIn(500);
                                                        });
                                                    });
                                                });
                                            });
                                        });
                                    });
                                });
                            });
                        });
                    });
                }
            );
        });
        $(function(){
            $("body").on("click",".why_bld3r_close", 
                function(){
                    $(".why_bld3r_close").remove();
                    $(".why_bld3r_all").remove();
                }
            );
        });
    }
);
//end of line