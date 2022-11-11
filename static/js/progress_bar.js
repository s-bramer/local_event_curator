$(document).ready(function(){
    $('#reload_button').on('submit', function(event){
      event.preventDefault();
        $.ajax({
        url:"/ajaxprogressbar",
        method:"POST",
        data:$(this).serialize(),
        beforeSend:function()
      {
       $('#reload').attr('disabled', 'disabled');
       $('#process').css('display', 'block');
      },
      success:function(data)
      { 
       var percentage = 0;
     
       var timer = setInterval(function(){
        percentage = percentage + 20;
        progress_bar_process(percentage, timer,data);
       }, 1000);
      }
     })
        
     });
       
     function progress_bar_process(percentage, timer,data)
     {
    $('.progress-bar').css('width', percentage + '%');
    if(percentage > 100)
    {
     clearInterval(timer);
     $('#reload_button')[0].reset();
     $('#process').css('display', 'none');
     $('.progress-bar').css('width', '0%');
     $('#reload').attr('disabled', false);
     $('#success_message').html(data);
     setTimeout(function(){
      $('#success_message').html('');
     }, 5000);
    }
     }
       
    });