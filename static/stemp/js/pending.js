
var interval = setInterval(check_if_pending, 10000);

function check_if_pending() {
  $.ajax({
    url : "/stemp/ajax/check_pending/",
    type : "GET",

    success : function(json) {
      alert(json.ready);
      if (json.ready === true) {
        clearInterval(interval);
        $('#pending').html('Simulation abgeschlossen.<br>Bitte <a href="/stemp/result/">hier</a> klicken um Ergebnisse zu laden.');
        alert('cleared');
      }
    }
  });
};
