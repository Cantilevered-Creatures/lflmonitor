function refreshPlayingSong(){
  $.ajax({
    url: location.protocol + '//' + document.domain + ':' + location.port + '/currentsong'
  }).then(function(data){
    $("#playingSong")[0].innerText = data.name;
  });
}

function submitPlayList(){
  var playListItems = $("#playList button");
  var playList = [];
  
  for(let pli of playListItems){
    playList.push(pli.value);
  }
  
  $('<input>').attr({
    type: 'hidden',
    id: 'playList',
    name: 'playList',
    value: playList
  }).appendTo('form');
}

$(function () {
  $(".songList, .playList").sortable({
    connectWith: ".connected"
  });
  $(".connected").disableSelection();
  $("#updatePlayList").click(function() {
    submitPlayList();
  });
  refreshPlayingSong();
});

setInterval(function() {
  refreshPlayingSong();
}, 5000);