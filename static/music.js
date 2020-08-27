setInterval(function() {
  $.ajax({
    url: location.protocol + '//' + document.domain + ':' + location.port + '/currentsong'
  }).then(function(data){
    $("#playingSong")[0].innerText = data.name;
  });
}, 5000);