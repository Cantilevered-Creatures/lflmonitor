$(document).ready(function() {
  // sending a connect request to the server.
  var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + '/currentsong');

  socket.on('songUpdate', function(msg) {
    console.log('Current song updated');
    $('#playingSong').val(msg.name);
  });
});