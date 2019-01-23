
$("#id_house_type").change(function() {
  set_default_roof_area();
  set_default_heat_demand();
});

$("#number_of_persons").change(function() {
  set_default_square_meters();
  update_warm_water();
});

// WARMWATER
$("#warmwater_consumption").on('changed.zf.slider', function() {
  update_warm_water();
});

function update_warm_water() {
  warmwater_consumption = $("#warmwater_consumption").children('.slider-handle').attr('aria-valuenow')
  if (isNaN(warmwater_consumption)) {
    warmwater_consumption = 1;
  }
  $.ajax({
    url : "/stemp/ajax/get_warm_water_energy/",
    type : "GET",
    data : {
      persons: $('#number_of_persons').val(),
      warmwater_consumption: warmwater_consumption
    },

    // handle a successful response
    success : function(json) {
      $("#id_warm_water_per_day").val(json.daily_warm_water);
      $("#show_warmwater").text(json.energy);
    }
  });
};

// HEAT DEMAND
$("#heat_option").change(function() {
  update_heat_demand();
});

function update_heat_demand() {
  if ($("#radio_heat_hand").prop("checked")) {
    $("#id_heat_demand").val($("#heat_hand").val());
  } else {
    $("#id_heat_demand").val($("#heat_auto").val());
  }
  $("#show_heat_demand").text($("#id_heat_demand").val());

  // Fire depending tasks
  set_default_roof_area();
};

function set_default_heat_demand() {
  $.ajax({
    url : "/stemp/ajax/get_heat_demand/",
    type : "GET",
    data : {
      sm: $('#id_square_meters').val(),
      house_type: $('#id_house_type').val()
    },

    // handle a successful response
    success : function(json) {
      $("#heat_auto").val(json.heat_demand);
      update_heat_demand();
    }
  });
};

// SQUARE_METERS
$("#sm_option").change(function() {
  update_square_meters();
});

function update_square_meters() {
  if ($("#radio_sm_hand").prop("checked")) {
    $("#id_square_meters").val($("#sm_hand").val());
  } else {
    $("#id_square_meters").val($("#sm_auto").val());
  }

  // Fire depending tasks
  set_default_roof_area();
  set_default_heat_demand();
};

function set_default_square_meters() {
  $.ajax({
    url : "/stemp/ajax/get_square_meters/",
    type : "GET",
    data : {persons: $('#number_of_persons').val()},

    // handle a successful response
    success : function(json) {
      $("#sm_auto").val(json.square_meters);
      update_square_meters();
    }
  });
};

// ROOF-AREA
$("#roof_option").change(function() {
  update_roof_area();
});

function update_roof_area() {
  if ($("#radio_roof_hand").prop("checked")) {
    $("#id_roof_area").val($("#roof_hand").val());
  } else {
    $("#id_roof_area").val($("#roof_auto").val());
  }
  $("#show_roof_area").text($("#id_roof_area").val());
};

function set_default_roof_area() {
  $.ajax({
    url : "/stemp/ajax/get_roof_area/",
    type : "GET",
    data : {
      sm: $('#id_square_meters').val(),
      house_type: $('#id_house_type').val()
    },

    // handle a successful response
    success : function(json) {
      $("#roof_auto").val(json.roof_area);
      update_roof_area();
    }
  });
};

$(document).ready(function() {
  set_default_square_meters();
  update_warm_water();
})
