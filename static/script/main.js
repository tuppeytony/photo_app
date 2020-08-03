$(document).ready(function(){

    $('#myModal').modal({
        keyboard: true,
        backdrop: true,
        show: false
      });
    $('#modalToggle').on('click',function(){
          $('#registration').modal('toggle');
          return false;
    });

    $('#myModal').hide(); 
    $('#modalToggle').on('click',function(e){ 
        e.preventDefault(); jQuery('#registration').modal('toggle'); 
    });

    $('.img-polaroid').magnificPopup({type:'image'});

});