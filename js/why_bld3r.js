$(document).ready(
    function() {
        $(function(){
            $("body").on("click",".why_bld3r_outline", 
                function(){
                    $(".why_bld3r_close").fadeOut(500);
                    $(".why_bld3r").animate({"opacity":"0",}, 500);
                    $(".why_bld3r_container").animate({"opacity":"0",}, 500, function() {
                        $(".why_bld3r_reason").animate({"width": "800px"}, 1000);
                        $(".why_bld3r_container").css({"cursor":"auto"});
                        $(".why_bld3r_close").css({
                            "margin-left":"-19px",
                            "margin-top":"1px"
                        });
                        $(".why_bld3r_outline").css({
                            "border":"none",
                            "webkit-box-shadow":"none",
                            "moz-box-shadow":"none",
                            "box-shadow":"none"
                        });
                        $(".why_bld3r_container").animate({"opacity":"1"}, 1, function() {
                            $(".why_bld3r_container").animate({"width":"1160px"}, 1000);
                            $(".why_bld3r_outline").animate({"width":"1160px"}, 1000);
                            $(".why_bld3r_outline").attr("class", ".why_bld3r_nothing");
                            $(".why_bld3r").animate({
                                "height":"209",
                                "font-size":"60px",
                                "padding-right": "50px", 
                                "padding-left": "50px",
                                "padding-top": "150px"
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
                    $(".why_bld3r_close").animate({"opacity":"0",}, 100, function() {
                        $(".why_bld3r_all").animate({"height":"0px",}, 200, function() {
                            $(".why_bld3r_all").remove();
                        });
                    });
                }
            );
        });
    }
);
//end of line