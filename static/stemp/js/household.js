$("#heat_by_option").change(function() {
  $("#square").attr("hidden", !$("#heat_by_sm").prop("checked"));
  if ($("#heat_by_hand").prop("checked")) {
    $("#hand").attr("hidden", false);
  } else {
    $("#hand").attr("hidden", true);
  }
  update_energy();
});

$("#id_house_type").change(function() {
  update_energy();
  set_energy(
    'person',
    $('#number_of_persons').val(),
    $('#id_house_type').val(),
    true
  );
});

function update_energy() {
  switch ($("input[name=heat_by]:checked").val()) {
    case 'person':
      set_energy(
        'person',
        $('#number_of_persons').val(),
        $('#id_house_type').val()
      );
      break;
    case 'square':
      set_energy(
        'square',
        $('#id_square_meters').val(),
        $('#id_house_type').val()
      );
      break;
    case 'hand':
      $("#id_heat_demand").val($("#energy_hand").val())
      break;
  }
};

$("#energy_hand").change(function() {
  update_energy();
});

$("#id_warm_water_per_day").change(function() {
  update_warm_water();
});

$("#number_of_persons_slider").on('changed.zf.slider', function() {
  update_energy();
  set_square_meters($('#number_of_persons').val());
  set_energy(
    'person',
    $('#number_of_persons').val(),
    $('#id_house_type').val(),
    true
  );
  update_warm_water();
});

function set_energy_by_hand() {
  $("#id_heat_demand").val($("#energy_hand").val())
};

function adapt_energy_hand(value) {
  $('#energy_hand').val(value);
  $('#hand_update').html('');
  set_energy_by_hand();
};

function adapt_square_meters(value) {
  $('#id_square_meters').val(value);
  $('#square_update').html('');
  update_energy();
};

function update_warm_water() {
  $.ajax({
    url : "/stemp/ajax/get_warm_water_energy/",
    type : "GET",
    data : {
      persons: $('#number_of_persons').val(),
      liter: $('#id_warm_water_per_day').val()
    },

    // handle a successful response
    success : function(json) {
      $("#warm_water").val(json.energy);
    }
  });
};

function set_energy(choice, value, house_type, virtual=false) {
  $.ajax({
    url : "/stemp/ajax/get_energy/",
    type : "GET",
    data : { choice: choice, value: value, house_type: house_type},

    // handle a successful response
    success : function(json) {
      if (virtual) {
        if ($("#energy_hand").val() != json.energy) {
          var href = "javascript:adapt_energy_hand(" + json.energy + ");";
          $('#hand_update').html('<a href="' + href + '"><i class="icon ion-refresh"></i></a>');
        } else {
          $('#hand_update').html('');
        }
      } else {
        $("#id_heat_demand").val(json.energy);
      }
    }
  });
};

function set_square_meters(value) {
  $.ajax({
    url : "/stemp/ajax/get_square_meters/",
    type : "GET",
    data : {value: value},

    // handle a successful response
    success : function(json) {
      if ($("#id_square_meters").val() != json.square_meters) {
        var href = "javascript:adapt_square_meters(" + json.square_meters + ");";
        $('#square_update').html('<a href="' + href + '"><i class="icon ion-refresh"></i></a>');
      } else {
        $('#square_update').html('');
      }
    }
  });
};
