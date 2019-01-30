
var interval = setInterval(check_if_pending, 2000);

function check_if_pending() {
  $.ajax({
    url : "/stemp/ajax/check_pending/",
    type : "GET",

    success : function(json) {
      if (json.ready === true) {
        clearInterval(interval);
        $('#loader').toggle();
        $('#started').toggle();
        $('#finished').toggle();
      }
    }
  });
};
