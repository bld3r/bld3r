$(document).ready(
    function() {
        $(function(){
            $("body").on("click","div.email_current", 
                function(){
                    $('.email_current').fadeOut("slow", function() {
                        $('.email_edit').fadeIn("slow");   
                    }); 
                }
            );
        });
        $(function(){
            $("body").on("click","span#email_cancel", 
                function(){
                    $('.email_edit').fadeOut("slow", function() {
                        $('.email_current').fadeIn("slow");   
                    });
                }
            );
        });  
               $(function(){
            $("body").on("click","div.summary_current", 
                function(){
                    $('.summary_current').fadeOut("slow", function() {
                        $('.summary_edit').fadeIn("slow");   
                    });
                }
            );
        });
        $(function(){
            $("body").on("click","span#summary_cancel", 
                function(){
                    $('.summary_edit').fadeOut("slow", function() {
                        $('.summary_current').fadeIn("slow");   
                    });
                }
            );
        });  
        
        $(function(){
            $("body").on("click","div.location_current", 
                function(){
                    $('.location_current').fadeOut("slow", function() {
                        $('.location_edit').fadeIn("slow");   
                    });
                }
            );
        });
        $(function(){
            $("body").on("click","span#location_cancel", 
                function(){
                    $('.location_edit').fadeOut("slow", function() {
                        $('.location_current').fadeIn("slow");   
                    });
                }
            );
        });   
        $(function(){
            $("body").on("click","div.printer_current", 
                function(){
                    $('.printer_current').fadeOut("slow", function() {
                        $('.printer_edit').fadeIn("slow");   
                    });
                }
            );
        });
        $(function(){
            $("body").on("click","span#printer_cancel", 
                function(){
                    $('.printer_edit').fadeOut("slow", function() {
                        $('.printer_current').fadeIn("slow");   
                    });
                }
            );
        });
        $(function(){
            $("body").on("click","div.slicer_current", 
                function(){
                    $('.slicer_current').fadeOut("slow", function() {
                        $('.slicer_edit').fadeIn("slow");   
                    });
                }
            );
        });
        $(function(){
            $("body").on("click","span#slicer_cancel", 
                function(){
                    $('.slicer_edit').fadeOut("slow", function() {
                        $('.slicer_current').fadeIn("slow");   
                    });
                }
            );
        });        
        $(function(){
            $("body").on("click","div.software_current", 
                function(){
                    $('.software_current').fadeOut("slow", function() {
                        $('.software_edit').fadeIn("slow");   
                    });
                }
            );
        });
        $(function(){
            $("body").on("click","span#software_cancel", 
                function(){
                    $('.software_edit').fadeOut("slow", function() {
                        $('.software_current').fadeIn("slow");   
                    });
                }
            );
        });
        $(function(){
            $("body").on("click","div.filament_brand_current", 
                function(){
                    $('.filament_brand_current').fadeOut("slow", function() {
                        $('.filament_brand_edit').fadeIn("slow");   
                    });
                }
            );
        });
        $(function(){
            $("body").on("click","span#filament_brand_cancel", 
                function(){
                    $('.filament_brand_edit').fadeOut("slow", function() {
                        $('.filament_brand_current').fadeIn("slow");   
                    });
                }
            );
        });
    }


);
//end of line