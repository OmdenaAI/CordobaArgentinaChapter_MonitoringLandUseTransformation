function selectInput() {
  var sel = document.getElementById("selInput");
  if(sel.selectedIndex == 1) {
    document.getElementById("inpLongFrom").value = -75.0849;
    document.getElementById("inpLongTo").value = -75.035;
    document.getElementById("inpLatFrom").value = -8.295;
    document.getElementById("inpLatTo").value = -8.245;
    document.getElementById("inpT1").value = "2015-08-04";
    document.getElementById("inpT2").value = "2015-09-10";
  } else if(sel.selectedIndex == 2) {
    document.getElementById("inpLongFrom").value = -61.149;
    document.getElementById("inpLongTo").value = -61.05;
    document.getElementById("inpLatFrom").value = -21.79;
    document.getElementById("inpLatTo").value = -21.7;
    document.getElementById("inpT1").value = "2018-01-24";
    document.getElementById("inpT2").value = "2019-12-24";
  } else if(sel.selectedIndex == 3) {
    document.getElementById("inpLongFrom").value = -62.28;
    document.getElementById("inpLongTo").value = -62.15;
    document.getElementById("inpLatFrom").value = -21.79;
    document.getElementById("inpLatTo").value = -21.7;
    document.getElementById("inpT1").value = "2019-01-24";
    document.getElementById("inpT2").value = "2019-12-24";
  }
}

function runPrediction() {
  let xhr = new XMLHttpRequest();
  xhr.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      let retData = JSON.parse(this.responseText);
      var rgb00 = document.getElementById("imgRgb00");
      rgb00.src = retData["rgb_paths"][0];
      var rgb01 = document.getElementById("imgRgb01");
      rgb01.src = retData["rgb_paths"][1];
      var prediction = document.getElementById("imgPrediction");
      prediction.src = retData["prediction_path"];
    }
  };
  xhr.open('POST', '/run_prediction');
  let formData = new FormData(document.getElementById("formData"));
  xhr.send(formData);
}
