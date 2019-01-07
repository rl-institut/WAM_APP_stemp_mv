
$("#id_profile").change(function() {
  load_hh_summary($('#id_profile').val());
});

function load_hh_summary(hh_id) {
  $.ajax({
      url : "/stemp/ajax/get_household_summary/",
      type : "GET",
      data : {hh_id: hh_id},

      // handle a successful response
      success : function(html) {
        $("#hh_summary").html(html);
      }
    });
}

load_hh_summary($('#id_profile').val());