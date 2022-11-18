// $(document).ready(function(){
//     $('#reload_button').on('submit', function(event){
//       event.preventDefault();
//         $.ajax({
//         url:"/ajaxprogressbar",
//         method:"POST",
//         data:$(this).serialize(),
//         beforeSend:function()
//       {
//        $('#reload').attr('disabled', 'disabled');
//        $('#process').css('display', 'block');
//       },
//       success:function(data)
//       { 
//        var percentage = 0;
     
//        var timer = setInterval(function(){
//         percentage = percentage + 20;
//         progress_bar_process(percentage, timer,data);
//        }, 1000);
//       }
//      })
        
//      });
       
//      function progress_bar_process(percentage, timer,data)
//      {
//     $('.progress-bar').css('width', percentage + '%');
//     if(percentage > 100)
//     {
//      clearInterval(timer);
//      $('#reload_button')[0].reset();
//      $('#process').css('display', 'none');
//      $('.progress-bar').css('width', '0%');
//      $('#reload').attr('disabled', false);
//      $('#success_message').html(data);
//      setTimeout(function(){
//       $('#success_message').html('');
//      }, 5000);
//     }
//      }
       
//     });


// var timeout;

// async function getStatus() {

//   let get;
  
//   try {
//     const res = await fetch("/status");
//     get = await res.json();
//   } catch (e) {
//     console.error("Error: ", e);
//   }
  
//   document.getElementById("innerStatus").innerHTML = get.status * 10 + "&percnt;";
  
//   if (get.status == 10){
//     document.getElementById("innerStatus").innerHTML += " Done.";
//     clearTimeout(timeout);
//     return false;
//   }
   
//   timeout = setTimeout(getStatus, 1000);
// }

// getStatus();


//MAIN CODE

// $('#reload_button').on('submit', async function getStatus() {

//   let get;
//   alert("reload function started")
//   try {
//     const res = await fetch("/status");
//     get = await res.json();
//   } catch (e) {
//     console.error("Error: ", e);
//   }
  
//   document.getElementById("innerStatus").innerHTML = get.status * 10 + "&percnt;";
  
//   if (get.status == 10){
//     document.getElementById("innerStatus").innerHTML += " Done.";
//     clearTimeout(timeout);
//     return false;
//   }
    
//   timeout = setTimeout(getStatus, 1000);
// })

// getStatus();


// $( document ).ready(function() {
//     $('#test').click(function(){
//     // document.getElementById("test").textContent="Submit";
//     $(this).prop("value", "DISABLED!!");
//     $(this).toggleClass("active"); 
//     // $(this).prop("disabled",true);
// })});

// $( document ).ready(function() {
// if ($(this).prop("value") == "DISABLED!!"){
// setTimeout(function(){
//     $(this).prop("value", "ACTIVE!!");
// }, 1000);
// }
// });

