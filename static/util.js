function getUrlParameter(sParam) {
  var sPageURL = window.location.search.substring(1),
      sURLVariables = sPageURL.split("&"),
      sParameterName

  sURLVariables.forEach(element => {
      sParameterName = element.split("=");

      if (sParameterName[0] === sParam) {
          return sParameterName[1] == "" ? true : decodeURIComponent(sParameterName[1])
      }
  })
}
