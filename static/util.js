function getUrlParameter(sParam) {
  var sPageURL = window.location.search.substring(1),
    sParameter = sPageURL.split("&").map((sURLVar) => sURLVar.split("=")).find((sParamName) => { return sParamName[0] === sParam; });

  return sParameter ? sParameter[1] : sParameter;
}
