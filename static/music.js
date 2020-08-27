setInterval(function() {
  $.ajax({
    url: location.protocol + '//' + document.domain + ':' + location.port + '/currentsong'
  }).then(function(data){
    $("#playingSong").innerText = data.name;
  });
}, 5000);