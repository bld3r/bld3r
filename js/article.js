
$(document).ready(function(){	
//long polling
var timestamp = null;
var userid = $('.all').attr('id');	
function waitForMsg(){
	$.ajax({
		type: "GET",
		url: "getData.php",
		data: "timestamp=" + timestamp +"&userid=" + userid,
		async: true,
		cache: false,
		
		success: function(data){
			var json = eval('(' + data + ')');
			if (json['msg'] != "") {

				$('#hatnote').fadeIn().html(json['msg']);
				document.title="("+(json['msg'])+") Indeedly | Article in Context";
				
			}
			
			timestamp = json['timestamp'];

		},
		error: function(XMLHttpRequest, textStatus, errorThrown){

		}
	});
}




waitForMsg();


//date
var d=new Date();
var weekday=new Array(7);
weekday[0]="Sunday";
weekday[1]="Monday";
weekday[2]="Tuesday";
weekday[3]="Wednesday";
weekday[4]="Thursday";
weekday[5]="Friday";
weekday[6]="Saturday";

var month=new Array(12);
month[0]="January";
month[1]="February";
month[2]="March";
month[3]="April";
month[4]="May";
month[5]="June";
month[6]="July";
month[7]="August";
month[8]="September";
month[9]="October";
month[10]="November";
month[11]="December";


//comment reply
$("body").on("click",".reply", function(){
		var id = $(this).attr('id');
		$("#parent_id").attr("value", id);
		$("#longcomment"+id).toggle();
	});

//newsticker
$(function()
{
    $('#ticker').each(function()
    {
        var ticker = $(this);
        var fader = $('<span class="fader">&nbsp;</span>').css({display:'inline-block'});
        var links = ticker.find('ul>li>a');
        ticker.find('ul').replaceWith(fader);

        var counter = 0;
        var curLink;
        var fadeSpeed = 600;
        var showLink = function()
            {
                var newLinkIndex = (counter++) % links.length;
                var newLink = $(links[newLinkIndex]);
                var fadeInFunction = function()
                    {
                        curLink = newLink;
                        fader.append(curLink).fadeIn(fadeSpeed);
                    };
                if (curLink)
                {
                    fader.fadeOut(fadeSpeed, function(){
                        curLink.remove();
                        setTimeout(fadeInFunction, 0);
                    });
                }
                else
                {
                    fadeInFunction();
                }
            };

        var speed = 5500;
        var autoInterval;

        var startTimer = function()
        {
            autoInterval = setInterval(showLink, speed);
        };
        ticker.hover(function(){
            clearInterval(autoInterval);
        }, startTimer);

        fader.fadeOut(0, function(){
            fader.text('');
            showLink();
        });
        startTimer();

    });
});


//subject mysql polling
$("input#friendtrack").autocomplete({
		source: "friendlist.php",
		minLength: 2,
});

$("input#msgto").autocomplete({
		source: "friendlist.php",
		minLength: 2,
});
$("input#subject").autocomplete({
		source: "subjectlist.php",
		minLength: 3,
});
$("input#artorisubject").autocomplete({
		source: "subjectlist.php",
		minLength: 3,
});
$("input#query").autocomplete({
		source: "subjectlist.php",
		minLength: 3,
});
$("input#querytrack").autocomplete({
		source: "subjectlist.php",
		minLength: 3,
});						


//voting
$(function(){

	$("body").on("click","span.vote_up", function(){
	//get the id
	the_id = $(this).attr('id');
	
	//fadeout the vote-count 
	$("span#votes_count"+the_id).fadeOut("fast");
	
	//the main ajax request
		$.ajax
		({
			type: "POST",
			data: "action=vote_up&id="+$(this).attr("id"),
			url: "votes.php",
			success: function(msg)
			{
				$("a#vu"+the_id).css('border-bottom','10px solid #13ab4b');
				$("span#votes_count"+the_id).fadeOut();
				$("span#votes_count"+the_id).html(msg);
				$("span#votes_count"+the_id).fadeIn();
				$("span#votes_countsmall"+the_id).fadeOut();
				$("span#votes_countsmall"+the_id).html(msg);
				$("span#votes_countsmall"+the_id).fadeIn();	
				waitForMsg();
			}
		});
	});
	
	
	$("body").on("click","span.vote_down",function(){
	//get the id
	the_id = $(this).attr('id');
		$.ajax
		({
			type: "POST",
			data: "action=vote_down&id="+$(this).attr("id"),
			url: "votes.php",
			success: function(msg)
			{						
				$("span#votes_count"+the_id).fadeOut();
				$("span#votes_count"+the_id).html(msg);
				$("span#votes_count"+the_id).fadeIn();
				$("span#votes_countsmall"+the_id).fadeOut();
				$("span#votes_countsmall"+the_id).html(msg);
				$("span#votes_countsmall"+the_id).fadeIn();	
				$("a#vd"+the_id).css('border-top','10px solid #ff0000');
			}
		});
	});
});		



//voting small
$(function(){
	$("body").on("click","span.vote_upsmall",function(){
	//get the id
	the_id = $(this).attr('id');
	
	//fadeout the vote-count 
	$("span#votes_countsmall"+the_id).fadeOut("fast");

	
	//the main ajax request
		$.ajax
		({
			type: "POST",
			data: "action=vote_upsmall&id="+$(this).attr("id"),
			url: "votessmall.php",
			success: function(msg)
			{
				$("a#vu"+the_id).css('border-bottom','10px solid #13ab4b');			
				$("a#vus"+the_id).css('border-bottom','5px solid #13ab4b');			
				$("span#votes_countsmall"+the_id).fadeOut();
				$("span#votes_countsmall"+the_id).html(msg);
				$("span#votes_countsmall"+the_id).fadeIn();	
				$("span#votes_count"+the_id).fadeOut();
				$("span#votes_count"+the_id).html(msg);
				$("span#votes_count"+the_id).fadeIn();	
			}
		});
	});
	
	$("body").on("click","span.vote_downsmall",function(){
	//get the id
	the_id = $(this).attr('id');
		$.ajax
		({
			type: "POST",
			data: "action=vote_downsmall&id="+$(this).attr("id"),
			url: "votessmall.php",
			success: function(msg)
			{
				$("span#votes_countsmall"+the_id).fadeOut();
				$("span#votes_countsmall"+the_id).html(msg);
				$("span#votes_countsmall"+the_id).fadeIn();
				$("span#votes_count"+the_id).fadeOut();
				$("span#votes_count"+the_id).html(msg);
				$("span#votes_count"+the_id).fadeIn();	
				$("a#vd"+the_id).css('border-top','10px solid #ff0000');
				$("a#vds"+the_id).css('border-top','5px solid #ff0000');
			}
		});
	});
});		


//hiding and resizing

	$('.longcomment').hide();
	$('#invalidurl').hide();
	$('#validurl').hide();
	$('#tagguide').hide();
	$('#commentguide').hide();

	$('textarea#comments').autoResize({
		maxHeight: 250,
    	minHeight: 80
	});
	
	$('textarea.comment_body').autoResize({
		maxHeight: 250,
    	minHeight: 80
	});

	$('textarea.comment_bodyC').autoResize({
		maxHeight: 250,
    	minHeight: 80
	});	
	
	$('textarea#msgbody').autoResize({
		maxHeight: 250,
    	minHeight: 80
	});

	$('textarea#artoribody').autoResize({
		maxHeight: 250,
    	minHeight: 80
	});

//not logged in
$(function(){
	
	$("body").on('click','.votenotlogged', function() {
		$("span.loggedout").hide();
		$("span.logtovote").hide();
		$("span.logtovote").fadeIn();
	});
});	


	$('#notloggedtopbar').click(function(){
	$("span.loggedout").hide();
	$("span.logtovote").hide();
	$("span.logtovote").fadeIn();
	});
	
	
	$('.notloggedcomment').click(function(){
	$("span.loggedout").hide();
	$("span.logtovote").hide();
	$("span.logtovote").fadeIn();
	});
	
	$('span.menuitemnotlogged').click(function(){
	$("span.loggedout").hide();
	$("span.logtovote").hide();
	$("span.logtovote").fadeIn();
	});	
	
	
//show one div
	$('#topbar').click(function(){
		$('#boxfirst').slideToggle();
		$('#messages').hide();
 	    $('#notifications').hide();
		$('#mailopen').hide();
		$('#mail').show();
		$('#hattip').hide();
		$('#hat').show();
		$('#addfollow').hide();
		$('#about').hide();
		$('#moreabout').hide();	
		$('#register').hide();
		$('#login').hide();
		$('#logdrop').hide();	
		
	});
	
	$('.boxsharetoggle').click(function(){
	$('#boxfirst').slideToggle();
	});
	
	
	$('#shorten').click(function(){
	$('.topbar').width(200);
	$('.topbar').height(95);
	$('.titlegroup2').toggle();
	$('.addlink').toggle();
	$('.topsearch').toggle();
	$('#regloglong').toggle();
	$('#regloglongbarright').toggle();
	$('#shorten').toggle();
	$('#lengthen').toggle();
	$('#lengthenhide').toggle();
	});

	$('#lengthen').click(function(){
	$('.topbar').width(1030);
	$('.topbar').height(52);
	$('.titlegroup2').toggle();
	$('.addlink').toggle();
	$('.topsearch').toggle();
	$('#regloglong').toggle();
	$('#regloglongbarright').toggle();
	$('#shorten').toggle();
	$('#lengthen').toggle();
	$('#lengthenhide').toggle();
	});
	

	$('#weburl').click(function(){
	$('.arterror').hide();
	$('.artsuccess').hide();	
	$('.artfailure').hide();	
	$('#testform').show();
	$('#weburl').css({       
        'background':'white',
        'border-top':'1px solid #E8E8E8',
        'border-right':'1px solid #E8E8E8',
        'border-left':'1px solid #E8E8E8'
        });	
	$('#originalarticle').hide();	
	$('#original').css({       
        'background':'#FCFCFC',
        'border-top':'0px',
        'border-right':'0px',
        'border-left':'0px',
        });		
	});
	
	$('#original').click(function(){
	$('.blanksubject').hide();		
	$('#testform').hide();
	$('#weburl').css({       
        'background':'#FCFCFC',
        'border-top':'0px',
        'border-right':'0px',
        'border-left':'0px'
        });			
	$('#originalarticle').show();	
	$('#original').css({       
        'background':'white',
        'border-top':'1px solid #E8E8E8',
        'border-right':'1px solid #E8E8E8',
        'border-left':'1px solid #E8E8E8'
        });			
	});	
		
	
$(document).ready(function()
{

    $('.dropdown').hover(function(){ 
        mouse_is_inside=true; 
    }, function(){ 
        mouse_is_inside=false; 
    });

    $("body").mouseup(function(){ 
        if(! mouse_is_inside) $('.dropdown').hide();
        	$('#mailopen').hide();
        	$('#hattip').hide();
			$('#mail').show();
			$('#hat').show();
    });
});


	
	
	$('#hat').click(function(){
	$('#hattip').toggle();
	$('#hat').toggle();
	$('#notifications').slideToggle();
	$('#hattip').css({       
		'padding-top':'3px',
        'padding-bottom':'8px',
        'background':'#666',
        'border-right':'1px solid #AAAAAA'
        });
	$('#hatnote').hide();

    $('#messages').hide();
	$('#mailopen').hide();
	$('#mail').show();
	$('#addfollow').hide();
	$('#about').hide();
	$('#moreabout').hide();	
	$('#register').hide();
	$('#login').hide();
	$('#boxfirst').hide();
	$('#logdrop').hide();	
	
	});

	
	$('#hattip').click(function(){
	$('#hat').toggle();
	$('#hattip').toggle();
	$('#notifications').slideToggle();
	$('#about').hide();
	$('#moreabout').hide();	
	$('#register').hide();
	$('#login').hide();
	$('#boxfirst').hide();
	$('#logdrop').hide();	
	
	});
	
	$('#mail').click(function(){
	$('#mailopen').toggle();
	$('#mailopen').css({       
		'padding-top':'3px',
        'padding-bottom':'8px',
        'background':'#666',
        'border-right':'1px solid #AAAAAA'
        });
	$('#mail').toggle();
	$('#messages').slideToggle();
    $('#notifications').hide();
	$('#hattip').hide();
	$('#hat').show();
	$('#addfollow').hide();
	$('#about').hide();
	$('#moreabout').hide();	
	$('#register').hide();
	$('#login').hide();
	$('#boxfirst').hide();
	$('#logdrop').hide();	
	
	});	


	$('#mailopen').click(function(){
	$('#mailopen').toggle();
	$('#mail').toggle();
	$('#messages').slideToggle();
	$('#about').hide();
	$('#moreabout').hide();	
	$('#register').hide();
	$('#login').hide();
	$('#boxfirst').hide();
	$('#logdrop').hide();	
	
	});		
	
	$('#addfollowtoggle').click(function(){
	$('#addfollow').slideToggle();
	$('#notifications').hide();
	$('#messages').hide();
	$('#mailopen').hide();
	$('#hattip').hide();
	$('#mail').show();
	$('#hat').show();
	$('#about').hide();
	$('#moreabout').hide();	
	$('#register').hide();
	$('#login').hide();
	$('#boxfirst').hide();
	$('#logdrop').hide();	
	
	});
	
	$('#addfollowclose').click(function(){
	$('#addfollow').slideToggle();
	});
	
	$('#abouttoggle').click(function(){
	$('#about').slideToggle();
	$('#moreabout').hide();	
	$('#register').hide();
	$('#login').hide();
	$('#addfollow').hide();
	$('#messages').hide();
	$('#notifications').hide();
	$('#mailopen').hide();
	$('#mail').show();
	$('#hattip').hide();
	$('#hat').show();
	$('#boxfirst').hide();
	$('#logdrop').hide();	
	
	});
	
	$('#abouttoggleclose').click(function(){
	$('#about').slideToggle();
	});
	
	$('#userlog').click(function(){
	$('#logdrop').slideToggle();
	$('#moreabout').hide();	
	$('#register').hide();
	$('#login').hide();
	$('#addfollow').hide();
	$('#messages').hide();
	$('#notifications').hide();
	$('#mailopen').hide();
	$('#mail').show();
	$('#hattip').hide();
	$('#hat').show();
	$('#boxfirst').hide();
	});	
	
	$('#log').click(function(){
	$('#login').slideToggle();
	$('#about').hide();
	$('#moreabout').hide();	
	$('#register').hide();
	$('#addfollow').hide();
	$('#messages').hide();
	$('#notifications').hide();
	$('#mailopen').hide();
	$('#mail').show();
	$('#hattip').hide();
	$('#hat').show();
	$('#boxfirst').hide();
	$('#logdrop').hide();	
	
	});
	



	$('.registerbutton').click(function(){
	$('#register').slideToggle();
	$('#about').hide();
	$('#moreabout').hide();	
	$('#login').hide();
	$('#addfollow').hide();
	$('#messages').hide();
	$('#notifications').hide();
	$('#mailopen').hide();
	$('#mail').show();
	$('#hattip').hide();
	$('#hat').show();
	$('#boxfirst').hide();
	});
	

	
	$('.mabout').click(function(){
	$('#moreabout').slideToggle();
	});




	$("body").on("click",".contextcollapse", function(){
	$("#ccollapse").hide();
	$("#copen").show();
	$(".interacthide").show();
	$(".context").hide();
	$(".commentsreturn").hide();
	var idarticlecontext = $(this).attr('id');
	$("#articlecontextdecontext"+idarticlecontext).hide();
	$('.hiddenbox').css({ 
		'padding-bottom':'0px'
		});		
	$('.info').css({   
        'width':'742px',
        'height':'auto',        
        'border-right':'solid 1px white'
        });		
	$('.commentsreturn').css({       
        'border-top':'solid 1px white'
        });		       
	});
	
	
	$("body").on("click",".contextopen", function(){
	$("#ccollapse").show();
	$("#copen").hide();
	$(".interacthide").hide();
	$(".context").show();
	$(".commentsreturn").show();
	$('.hiddenbox').css({ 
		'padding-bottom':'10px'
		});			
	$('.info').css({  
        'width':'457px',
        'height':'350px',        
        });		
	$('.commentsreturn').css({       
        });		       
	});	
	

	$("body").on("click",".articlecontextopen", function(){
	var idarticlecontext = $(this).attr('id');
	$("#articlecontextinteracthide"+idarticlecontext).hide();
	$("#articlecontext"+idarticlecontext).show();
	$("#articlecontextcommentsreturn"+idarticlecontext).show();
	$("#articlecontextdecontext"+idarticlecontext).show();
	$('.hiddenbox').css({ 
		'padding-bottom':'10px'
		});		
	$('#articlecontextinfo'+idarticlecontext).css({       
        'width':'457px',
        'height':'350px',        
        });		
	$("#articlecontextcommentsreturn"+idarticlecontext).css({       
        });		       
	});		
	
	$("body").on ("click",".subjecthead",function () {
	$("#showmoresubjects").css({       
        'height':'auto'
        });		       
	});		


	$("body").on ("click",".friendhead",function () {
	$("#showmorefriends").css({       
        'height':'auto'
        });		       
	});		

	$("body").on ("click",".sourcehead",function () {
	$("#showmoresources").css({       
        'height':'auto'
        });		       
	});		
	$("body").on ("hover",".flag",function () {
	var idflag = $(this).attr('id');
	$("#flaghover"+idflag).fadeToggle();  
	});
	
	$("body").on ("hover",".flagdisplay",function () {
	var idflagdisplay = $(this).attr('id');
	$(".flagdisplayhover"+idflagdisplay).fadeToggle();  
	});	
	
	
	$("body").on ("hover",".userdisplayhover",function () {
	var iduserdisplay = $(this).attr('id');
	$(".userdisplayhoverover"+iduserdisplay).fadeToggle();  
	});		
	
	
	$("body").on ("hover",".removehover",function () {
	var ctxtid = $(this).attr('id');
	$("#remove"+ctxtid).fadeToggle();  
	});
			
	
	$("#sort").click(function () {
	$("#sortby").toggle();  
	});	

//show comment button 
$(function(){
	
	$("body").on('click','.comment_body', function() {
		var commentbody = $(this).attr('id');
		$("#submit_button"+commentbody).show();
	});
});	
	




//check notifications
$(function(){
	
	$("body").on('click','.hat', function() {
		var sessionuser = $(this).attr('id');
		$.ajax({
		type: "POST",
		url: "notificationread.php",
		data: "sessionuser="+sessionuser,
		success: function(checked){
		if(checked)
		{
		$('#hatnote').hide();
		document.title="Indeedly | Article in Context";
		}
		else
		{
		$('#hatnote').show();
		}
		}
		});		
	});
});	



//save an article
$(function(){
	
	$("body").on('click','.saved', function() {
		var saving = $(this).attr('id');
		$.ajax({
		type: "POST",
		url: "addsaved.php",
		data: "saving="+saving,
		success: function(saves){
		if(saves)
		{
		$("a#saved"+saving).hide();
		$("a#nowsaved"+saving).show();
		}
		else
		{
		$("a#saved"+saving).show();
		$("a#nowsaved"+saving).hide();
		}
		}
		});		
	});
});	


//friend
$(function(){
	
	$("body").on('click','.userdisplayhover', function() {
		var friend = $(this).attr('id');
		$.ajax({
		type: "POST",
		url: "addfriend.php",
		data: "friend="+friend,
		success: function(friending){
		if(friending)
		{	
		$("span.userdisplayhoverover"+friend).html('Friend Added');
		}
		else
		{
		$("span.userdisplayhoverover"+friend).hide();		
		}
		}
		});		
	});
});	


//flag an article
$(function(){
	
	$("body").on('click','.flagged', function() {
		var flagging = $(this).attr('id');
		$.ajax({
		type: "POST",
		url: "addflag.php",
		data: "flagging="+flagging,
		success: function(flags){
		if(flags)
		{
		$("a#flaghover"+flagging).hide();
		$("span#flagdisplay"+flagging).hide();
		$("span#flagdisplayhover"+flagging).hide();
		$("span#flagged"+flagging).show();		
		
		}
		else
		{
		$("a#flaghover"+flagging).show();
		}
		}
		});		
	});
});	

//delete an article
$(function(){
	
	$("body").on('click','.delete', function() {
		var deleting = $(this).attr('id');
		$.ajax({
		type: "POST",
		url: "adddelete.php",
		data: "deleting="+deleting,
		success: function(deletes){
		if(deletes)
		{
		$("a#delete"+deleting).hide();
		$("a#nowdeleted"+deleting).show();
		}
		else
		{
		$("a#delete"+deleting).show();
		$("a#nowdeleted"+deleting).hide();
		}
		}
		});		
	});
});	

//articlelinkhover
	$("body").on ("hover","span.articlelink",function () {
	var id = $(this).attr('id');
	$("span#hint"+id).fadeToggle();  
	});		
	
//register form
$(function() {
$("#registersubmit").click(function(event) {
event.preventDefault();
var dataString = $("#registerclick").serialize();

	if (document.registerclick.user.value.length ==0) 
	{
		$('.error').show();
		document.registerclick.user.focus();
		return (false);
	}	
	if (document.registerclick.password.value.length <8)
	{
		$('.error').show();
		document.registerclick.user.focus();
		return (false);
	}		
	if (document.registerclick.user.value.length < 4)
	{
		$('.error').show();
		document.registerclick.user.focus();
		return (false);	
	}
	else
	{
		$.ajax({
		type: "POST",
		url: "register.php",
		data: dataString,
		success: function(reg){
		if(!reg)
		{
        $('.userexists').show();
        $('.secreterror').hide();
		$('.error').hide();
        $('.success').hide();
		$('input#user').val('');
		$('input#password').val('');
		$('input#email').val('');
		}
		else
		{
		$('.userexists').hide();
        $('.secreterror').hide();
        $('.success').fadeOut(200).show(); 	
		$('.error').hide();
		$('input#userlogin').val(document.registerclick.user.value);
		$('input#passwordlogin').val(document.registerclick.password.value);
		document.getElementById('log').click();
		document.getElementById('signin').click();
		$('input#email').val('');		
	
		}
		}
		});
	}
return false;

});
});



//add following (note that remove = add labels)
	
	
$(function(){
	
	$("body").on('click','.removehide', function() {
		var rmv = $(this).attr('id');
		$.ajax({
		type: "POST",
		url: "addfollowsub.php",
		data: "remove="+rmv,
		success: function(rmvd){
		if(rmvd)
		{
		$("#removehide"+rmv).html('Added'); 
		}
		else
		{
		$("a#removehide"+rmv).show();		

		}
		}
		});		
	});
});	


//login form
$(function() {
$("#signin").click(function() {

	if (document.loginform.userlogin.value.length ==0 || document.loginform.passwordlogin.value.length ==0) 
	{
		$('.errorlogin').show();
		document.loginform.userlogin.focus();
		return (false);
	}	
	if (document.loginform.userlogin.value.length >0 || document.loginform.passwordlogin.value.length >0) 
	{
		$('.errorlogin').hide();
	}		
return true;

});
});
				
				
//followup form
$(function() {
$("#followsubjectsubmit").click(function() {

var followdataString = $("#addfollowform").serialize();

	if (document.addfollowform.followsubject.value.length ==0  ||document.addfollowform.followsubject.value.length >50) 
	{
		$('.errorfollowing').show();
		document.addfollowform.followsubject.focus();
		return (false);
	}	
	
	else
	{
		$.ajax({
		type: "POST",
		url: "addfollow.php",
		data: followdataString,
		success: function(foll){
		if(!foll)
		{
		$('.followupexists').hide();
		$('.errorfollowing').hide();
		$('.successfollowing').fadeOut(200).show(); 	
		var followsubjectvalue = $('#followsubject').val();
		var follow_append = '<a href="context.php?query='+followsubjectvalue+'">&nbsp;<span class="followup">'+followsubjectvalue+'</span>&nbsp;</a>·';
		var follow_appends = '<a href="context.php?query='+followsubjectvalue+'">&nbsp;<span class="followup">'+followsubjectvalue+'</span>&nbsp;</a>!';

		$('#regloglongbar').append(follow_append);
		$('.successfollowing').append(follow_appends);
		$('input#followsubject').val('');
		}
		else
		{
		$('.followupexists').show();
		$('.errorfollowing').hide();
		$('input#followsubject').val('');	
		}
		}
		});
	}
return false;

});
});			


//new message form
$(function() {
$("#msgsend").click(function() {
$('.msgsuccess').hide(); 	
var msgdataString = $("#newmsg").serialize();

	if (document.newmsg.msgto.value.length ==0) 
	{
		$('.msgerror').show();
		document.newmsg.msgto.focus();
		return (false);
	}	
	if (document.newmsg.msgbody.value.length ==0)
	{
		$('.msgerror').show();
		document.newmsg.msgbody.focus();
		return (false);
	}		
	else
	{
		$.ajax({
		type: "POST",
		url: "newmsg.php",
		data: msgdataString,
		success: function(nmsg){
		if(!nmsg)
		{
		$('.msgerror').hide();	
		$('.msgfailure').fadeOut(200).show(); 
		}
		else
		{
		$('.msgerror').hide();
		$('.msgsuccess').fadeOut(200).show(); 	
		$('input#msgto').val('');
		$('input#msgsubject').val('');
		$('textarea#msgbody').val('');	
		}
		}
		});
	}
return false;

});
});

// button click event

	$('#attach').click(function(){	
		if (document.testform.subject.value.length == 0 || document.testform.subject.value.length > 50  || document.testform.url.value.length==0)
		{
		$('#blanksubject').show();
		document.testform.subject.focus();
		return (false);
		}

		if(isValidURL($('#url').val()))
		{
			$('#load').fadeIn('fast');
			$('#boxfirst').slideUp('fast');
			var commentcontents = $('#comments').val();
			var brcontents = commentcontents.replace(/\n/g, '<br>');
			$formattedcomments = brcontents;
			var eurl = $('#url').val();
			var esubject = $('#subject').val();
			var ecomment = $formattedcomments;
			$eurl = encodeURIComponent(eurl);
			$esubject = encodeURIComponent(esubject);
			$ecomment = encodeURIComponent(ecomment);
			$.post("includes/fetch.php?url="+$eurl+"&subject="+$esubject,{
				}, function(response){
					$.ajax({
						url: "ajaxUpdate.php",
						type: "POST",
						data: "url="+$eurl+"&comments="+$ecomment+"&subject="+$esubject,	
					});					
					$('#posts').prepend($(response).slideDown('fast'));
					$('.images img').fadeOut('fast');
					var commentcontents = $('#comments').val();
					var brcontents = commentcontents.replace(/\n/g, '<br>');
					var comment_post = '<div class="ment">' + brcontents + '</div></div>';
					$('#ment').append(comment_post);
					var subjectcontents = $('#subject').val();
					var brcontents = subjectcontents.replace(/\n/g, '<br>');
					var subject_post = '<div class="subtag">' + brcontents + '</div></div>';
					$('#tag').append(subject_post);
					$('#load').fadeOut('fast');
					$('#subject').val('');
					$('#url').val('');
					$('#comments').val('');
				});
		}
		else
		{
			var contents = $('#comments').val();
			var brcontents = contents.replace(/\n/g, '<br>');
			var wall_post = '<li><div class="hiddenboxfirst"><div class="hiddenbox"><div class="postitem"><div class="votes"><div class="arrow-up"></div>63<div class="arrow-down"></div></div><div class="img"></div><div class="status" id="status">' + brcontents + '</div></div></div></div></li>';
				if (contents != '') 
				{
					$('textarea#url').val('Post an article or submit an idea');
					$('ul#posts').prepend(wall_post);
					$('#comments').val('');
					$('#boxfirst').slideUp('fast');
				}
					
				else
				{
					return false;
				}
				return false;
		}
		});	


	});	
	
//original article
$(function() {
$("#attach2").click(function() {
$('.artsuccess').hide(); 	
var artdataString = $("#originalarticle").serialize();

	if (document.originalarticle.artorisubject.value.length ==0  || document.originalarticle.artorisubject.value.length>50)  
	{
		$('.arterror').show();
		document.originalarticle.artorisubject.focus();
		return (false);
	}	
	if (document.originalarticle.artorititle.value.length ==0)
	{
		$('.arterror').show();
		document.originalarticle.artorititle.focus();
		return (false);
	}	
	if (document.originalarticle.artoribody.value.length ==0)
	{
		$('.arterror').show();
		document.originalarticle.artoribody.focus();
		return (false);
	}		
	
	else
	{
		$.ajax({
		type: "POST",
		url: "originalarticle.php",
		data: artdataString,
		success: function(art){
		if(art)
		{
		$('.arterror').hide();
		$('.artsuccess').fadeOut(200).show(); 	
		$('input#artorisubject').val('');
		$('input#artorititle').val('');
		$('textarea#artoribody').val('');
		}
		else
		{
		$('.arterror').hide();	
		$('.artfailure').fadeOut(200).show(); 
		}
		}
		});
	}
return false;

});
});	
	
	function isValidURL(url){
		var RegExp = /(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/;
	
		if(RegExp.test(url)){
			return true;
		}else{
			return false;
		}
	}

	function SelectAll(id)
{
    document.getElementById(id).focus();
    document.getElementById(id).select();
}
	

