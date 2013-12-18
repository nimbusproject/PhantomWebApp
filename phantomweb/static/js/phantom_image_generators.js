var g_cloud_map = {};
var g_arranged_cloud_values = {};
var g_ig_info = {};
var g_unsaved_igs = [];
var g_blank_name = "<new name>";
var g_selected_ig = null;
var g_selected_cloud = null;
var MAX_PUBLIC_IMAGES_ITEMS = 200;

$(document).ready(function() {
    //$("#nav-imagegenerators").addClass("active");

    $("#ig-nav").on("click", "a.image_generator", function() {
        var image_generator = $(this).text();
        phantom_ig_change_ig_internal(image_generator);
        return false;
    });

    $("#cloud_table_body").on('click', 'tr', function(event){
        $(this).parent().children().removeClass("info");
        var cloud_name = $(this).children().first().text();
        phantom_ig_order_selected_click(cloud_name);
        return false;
    });

    var $phantom_ig_common_image_input = $("#phantom_ig_common_image_input").typeahead({
        minLength: 0,
        items: MAX_PUBLIC_IMAGES_ITEMS,
    });

    //enable showing hints on click
    if ($phantom_ig_common_image_input.typeahead.bind) {
        $phantom_ig_common_image_input.on('focus', $phantom_ig_common_image_input.typeahead.bind($phantom_ig_common_image_input, 'lookup'));
        $phantom_ig_common_image_input.on('click', $phantom_ig_common_image_input.typeahead.bind($phantom_ig_common_image_input, 'lookup'));
    }

    $("#phantom_ig_add").click(function() {
        save_ig_values();
        return false;
    });

    $("#phantom_ig_disable_cloud").click(function() {
        phantom_ig_disable_click();
        return false;
    });

    var autosave_cloud_fields = "#phantom_ig_info_area input, #phantom_ig_info_area select, #phantom_ig_info_area";

    $(autosave_cloud_fields).change(function() {
        if (g_arranged_cloud_values[g_selected_cloud]) {
            save_ig_values();
        }
        return false;
    });

    $(autosave_cloud_fields).bind('keyup', function() {
        if (g_arranged_cloud_values[g_selected_cloud]) {
            save_ig_values();
        }
        return false;
    });

    $("#phantom_ig_order_area").on("keyup", "textarea", function() {
        if (g_arranged_cloud_values[g_selected_cloud]) {
            save_ig_values();
        }
        return false;
    });

    $("#phantom_ig_order_area").on("change", "select", function() {
        if (g_arranged_cloud_values[g_selected_cloud]) {
            save_ig_values();
        }
        return false;
    });

    $("#ig-help").popover();

    $("#phantom_ig_button_add").click(function() {
        phantom_ig_add_ig_click();
        return false;
    });

    $("#phantom_ig_delete").click(function() {
        phantom_ig_delete_click();
        return false;
    });

    $("#phantom_image_generator_run").click(function() {
        phantom_image_generator_run();
        return false;
    });

    $("#phantom_ig_save").click(function() {
        var valid = save_ig_values();
        if (valid) {
            phantom_ig_save_click();
        }
        return false;
    });

    $(".context-details").hide();
    $("#phantom_ig_script").parent().show();

    phantom_ig_load();
});

function phantom_ig_buttons(enabled) {

    if (enabled) {
        $("button, input, select").removeAttr("disabled");
        $("#phantom_ig_button_add").removeAttr("disabled")
            .parent().removeClass("disabled");
        phantom_ig_change_image_type();
        $('#loading').hide();
    }
    else {
        $("button, input, select").attr("disabled", true);
        $("#phantom_ig_button_add").attr("disabled", true)
            .parent().addClass("disabled");
        $('#loading').show();
    }
}


function phantom_ig_load_error_func(obj, message) {
    phantom_ig_buttons(true);
    alert(message);
}

function phantom_ig_add_ig_click() {

    var new_ig_name = prompt("Enter a new image generator name:");
    if (new_ig_name === null) {
        return false;
    }

    if (g_ig_info.hasOwnProperty(new_ig_name)) {
        phantom_warning("You already have an image generator called " + new_ig_name);
        return false;
    }

    g_unsaved_igs.push(new_ig_name);
    g_ig_info[new_ig_name] = {};
    g_selected_ig = new_ig_name;
    phantom_ig_load_ig_names();
}

function phantom_ig_select_new_cloud() {
    try
    {
        var cloud_name = $("#phantom_ig_cloud").val();
        phantom_ig_select_new_cloud_internal(cloud_name);
    }
    catch(err)
    {
        alert("There was a problem on the page.  ".concat(err.message));
        $('#loading').hide();
    }
    phantom_ig_buttons(true);
}

function phantom_ig_change_image_type() {
    if ($("#phantom_ig_common_choice_checked").is(':checked')) {
        $("#phantom_ig_common_image_input").removeAttr("disabled", "disabled");
        $("#phantom_ig_user_images_choices").attr("disabled", "disabled");
    }
    else {
        $("#phantom_ig_user_images_choices").removeAttr("disabled", "disabled");
        $("#phantom_ig_common_image_input").attr("disabled", "disabled");
    }
}

function phantom_ig_select_new_cloud_internal(cloud_name) {
    if (!cloud_name) {
        return;
    }
    var cloud_data = g_cloud_map[cloud_name];

    if (!cloud_data || cloud_data['status'] != 0) {
        return;
    }

    var public_images_typeahead = $('#phantom_ig_common_image_input').data('typeahead');
    public_images_typeahead.hide();

    $("#phantom_ig_instance").empty();
    for (instance in cloud_data.instance_types) {
        var i = cloud_data.instance_types[instance];
        var new_opt = $('<option>', {'name': i, value: i, text: i});
        $("#phantom_ig_instance").append(new_opt);
    }
    $("#phantom_ig_common_image_input").val("");

    $("#phantom_ig_user_images_choices").empty();
    for (personal in cloud_data.user_images) {
        var i = cloud_data.user_images[personal];
        var new_opt = $('<option>', {'name': i, value: i, text: i});
        $("#phantom_ig_user_images_choices").append(new_opt);
    }
    if (public_images_typeahead) {
        public_images_typeahead.source = cloud_data.public_images;
    }
}

function phantom_ig_load_cloud_names() {

    for(var site in g_cloud_map) {
        var cloud_data = g_cloud_map[site];
        if (!cloud_data) {
            phantom_alert("There was an error communicating with ".concat(site).concat(". You may still use the remaining clouds. Refresh later when the cloud is available."))        }
        else {
            var new_opt = $('<option>', {'name': site, value: site, text: site});
            $("#phantom_ig_cloud").append(new_opt);
        }
    }
}

function phantom_ig_load_ig_names() {
    $("#phantom_ig_name_input").val("");

    $("#ig-header").nextAll().remove();

    for (var ig_name in g_ig_info) {
        var ig = g_ig_info[ig_name];
        var new_ig = '<li><a href="#" class="image_generator" id="ig-' + ig_name + '">' + ig_name + '</a></li>';
        $("#ig-nav").append(new_ig);
    }
    phantom_ig_change_ig_internal(g_selected_ig);
}

function make_cloud_table_row(site, status) {

    if (status === "Enabled") {
        status = '<span class="label label-success">' + status + '</span>';
    }
    else if (status === "Disabled") {
        status = '<span class="label label-warning">' + status + '</span>';
    }
    else {
        status = '<span class="label">' + status + '</span>';
    }

    var row = "<tr id='cloud-row-" + site + "'>" +
      "<td class='cloud-data-site'>" + site + "</td>" +
      "<td>" + status + "</td>" +
      "</tr>";
    return row;
}

function phantom_ig_change_ig_internal(ig_name) {

    if (!ig_name) {
        $("#phantom_ig_order_area").hide();
        return;
    }

    g_selected_ig = ig_name;
    g_selected_cloud = null;
    var ig = g_ig_info[ig_name];

    $("#image_generator_options_head").text(ig_name + " Image Generator");

    $("a.image_generator").parent().removeClass("active");
    $("a.image_generator").filter(function() { return $(this).text() == ig_name}).parent().addClass("active");

    $("#cloud_options_name").text("cloud");
    $("#cloud_table_body").empty();


    if (ig_name == g_blank_name) {
        // set to blank values
        g_arranged_cloud_values = {};
        $("#phantom_ig_name_input").val("");
        $("#phantom_ig_name_input").text("");
        $("#phantom_ig_order").empty();

    }
    else {
        $("#phantom_ig_name_input").val(ig_name);
        $("#phantom_ig_name_input").text(ig_name);
        g_arranged_cloud_values = ig['cloud_params'];
        if (g_arranged_cloud_values === undefined) {
            g_arranged_cloud_values = {};
        }
        $("#phantom_ig_script").val(ig['script']);
    }

    $("#phantom_ig_order").empty();
    var ordered = Array();
    for (var site in g_arranged_cloud_values) {
        ordered.push(site)
    }

    var table_body = $("#cloud_table_body");

    for(var idx in ordered) {
        var site = ordered[idx];
        var row = make_cloud_table_row(site, "Enabled");
        table_body.append(row);
    }

    for(var site in g_cloud_map) {
        if (ordered.indexOf(site) > -1 || g_cloud_map[site]['status'] != 0) {
            continue;
        }
        var row = make_cloud_table_row(site, "Disabled");
        table_body.append(row);
    }

    for(var ndx in ordered) {
        var site = ordered[ndx];
        var new_opt = $('<option>', {'name': site, value: site, text: site});
        $("#phantom_ig_order").append(new_opt);
    }

    $("#phantom_ig_order_area").show();
    var first_cloud = $("td.cloud-data-site").first().text();
    if (first_cloud) {
        phantom_ig_order_selected_click(first_cloud);
    }
}

function phantom_ig_change_ig_click(ig_name) {
    try {
        phantom_ig_change_ig_internal(ig_name);
    }
    catch(err) {
        phantom_alert(err);
    }
}

function get_hash_ig() {
    var url_id = window.location.hash.substring(1);
    return url_id;
}


function phantom_ig_load_internal() {

    var load_sites_success = function(sites) {

        g_cloud_map = {};
        for(var i=0; i<sites.length; i++) {
            var site = sites[i];
            g_cloud_map[site.id] = {};
            g_cloud_map[site.id]['user_images'] = site['user_images'];
            g_cloud_map[site.id]['public_images'] = site['public_images'];
            g_cloud_map[site.id]['instance_types'] = site['instance_types'];
        }
    }

    var load_credentials_success = function(clouds) {
        for(var i=0; i<clouds.length; i++) {
            var cloud = clouds[i];
            if (!cloud.id in g_cloud_map) {
                g_cloud_map[cloud.id] = {};
            }
            g_cloud_map[cloud.id]['status'] = 0;
        }
    }

    var load_ig_success = function(imagegenerators) {
        try {
            clear_phantom_alerts();
            $("#phantom_ig_name_select").empty();
            $("#phantom_ig_cloud").empty();
            g_ig_info = {};
            for(var i=0; i<imagegenerators.length; i++) {
                var imagegenerator = imagegenerators[i];
                g_ig_info[imagegenerator.name] = imagegenerator;
            }

            phantom_ig_load_ig_names();
            phantom_ig_load_cloud_names();
            var cloud_name = g_selected_cloud;
            phantom_ig_select_new_cloud_internal(cloud_name);
            phantom_ig_change_image_type();

            var ig_name_from_saved = $("#phantom_ig_name_input").val();
            if (ig_name_from_saved) {
                // if it was a saved name load up its value
                $("#phantom_ig_name_select").val(ig_name_from_saved);
            }

            if (g_selected_ig === null) {
                var url_ig = get_hash_ig();
                var first_ig = $("a.image_generator").first().text();

                if (g_ig_info.hasOwnProperty(url_ig)) {
                    g_selected_ig = url_ig;
                    phantom_ig_load_ig_names();
                }
                else if (first_ig) {
                    g_selected_ig = first_ig;
                    phantom_ig_load_ig_names();
                }
                else {
                    $("#phantom_ig_info_area").hide();
                    $("#phantom_ig_order_area").hide();
                }
            }

            phantom_ig_buttons(true);
        }
        catch (err) {
            phantom_alert("There was a problem loading the page.  Please try again later. ".concat(err.message));
            $('#loading').hide();
        }
    }

    var credentials_url = make_url('credentials/sites')
    var cred_request = phantomGET(credentials_url);

    var sites_url = make_url('sites?details=true')
    var sites_request = phantomGET(sites_url)

    var ig_url = make_url('imagegenerators')
    var ig_request = phantomGET(ig_url);

    phantom_ig_buttons(false);
    phantom_info("Loading Image Generators");

    $.when(cred_request, sites_request, ig_request)
        .done(function(credentials, sites, igs) {
            load_sites_success(sites[0]);
            load_credentials_success(credentials[0]);
            load_ig_success(igs[0]);
        })
        .fail(function(err) {
            phantom_alert("There was a problem loading your image generators.  Please try again later. ".concat(err.message));
            $('#loading').hide();
        });
}

function phantom_ig_load() {
    try {
        phantom_ig_load_internal();
    }
    catch(err) {
        alert(err);
    }
}

function save_ig_values() {

    $("#phantom_ig_info_area div").removeClass("error");
    $("#phantom_ig_order_area div").removeClass("error");

    clear_phantom_alerts();
    var ig = g_ig_info[g_selected_ig];
    var cloud_name = g_selected_cloud;
    var chef_runlist = $("#phantom_ig_chef_runlist").val();
    var chef_attributes = $("#phantom_ig_chef_attributes").val();
    var script = $("#phantom_ig_script").val();


    if (cloud_name === null && g_arranged_cloud_values === {}) {
        phantom_warning("You must set up at least one cloud");
        return false;
    }
    else if (cloud_name === null) {
        return true;
    }

    var instance_type = $("#phantom_ig_instance").val().trim();
    var ssh_username = $("#phantom_ig_ssh_username").val().trim();
    var new_image_name = $("#phantom_ig_new_image_name").val().trim();
    var common;
    var image_id = "";
    if ($("#phantom_ig_common_choice_checked").is(':checked')) {
        image_id = $("#phantom_ig_common_image_input").val().trim();
        common = true;
    }
    else {
        image_id = ($("#phantom_ig_user_images_choices").val() || "").trim();
        common = false;
    }

    if (!cloud_name) {
        phantom_warning("You must select a cloud.");
        return false;
    }
    if (!image_id) {
        if ($("#phantom_ig_common_choice_checked").is(":checked")) {
            $("#phantom_ig_common_image_input").parent().addClass("error");
        }
        else {
            $("#phantom_ig_user_images_choices").parent().addClass("error");
        }
        phantom_warning("You must select an image.");
        return false;
    }
    if (!instance_type) {
        $("#phantom_ig_instance").parent().addClass("error");
        phantom_alert("You must select an instance type.");
        return false;
    }
    if (!ssh_username) {
        $("#phantom_ig_ssh_username").parent().addClass("error");
        phantom_alert("You must select an SSH username.");
        return false;
    }
    if (!new_image_name) {
        $("#phantom_ig_new_image_name").parent().addClass("error");
        phantom_alert("You must select a name for the generated image.");
        return false;
    }
    var script = $("#phantom_ig_script").val();
    var entry = {
        'cloud': cloud_name,
        'image_id': image_id,
        'instance_type': instance_type,
        'common': common,
        'ssh_username': ssh_username,
        'new_image_name': new_image_name,
    };

    g_arranged_cloud_values[cloud_name] = entry;

    var new_row = make_cloud_table_row(cloud_name, "Enabled");
    $("#cloud_table_body tr td").filter(function() { return $(this).text() == cloud_name})
      .parent().replaceWith(new_row);
    phantom_ig_order_selected_click(cloud_name);
    return true;
}

function phantom_ig_disable_click() {

    var cloud_name = g_selected_cloud;
    delete g_arranged_cloud_values[cloud_name];

    var new_row = make_cloud_table_row(cloud_name, "Disabled");
    $("#cloud_table_body tr td").filter(function() { return $(this).text() == cloud_name})
      .parent().replaceWith(new_row);
    phantom_ig_order_selected_click(cloud_name);
}


function phantom_ig_save_click_internal() {
    var ig_name = g_selected_ig;
    var ig = g_ig_info[ig_name];
    var ig_script = $("#phantom_ig_script").val();

    var err_msg = null;
    if (!ig_name) {
        err_msg = "You must select an image generator name."
    }

    if (err_msg) {
        phantom_alert(err_msg);
        return;
    }

    var data = {
        'name': ig_name,
        'cloud_params': {},
        'script': ig_script,
    };

    $("#cloud_table_body td.cloud-data-site").each(function(i) {

        var site_name = $(this).text();
        var cloud_data = g_arranged_cloud_values[site_name];

        if (!cloud_data) {
            return true; //each's equivalent of continue;
        }

        data['cloud_params'][site_name] = {};
        var site = data['cloud_params'][site_name];

        site['image_id'] = cloud_data['image_id'];
        site['instance_type'] = cloud_data['instance_type'];
        site['ssh_username'] = cloud_data['ssh_username'];
        site['new_image_name'] = cloud_data['new_image_name'];
        site['common'] = cloud_data['common'];
    });

    var success_func = function(new_ig) {
        g_ig_info[ig_name]['id'] = new_ig['id'];
        clear_phantom_alerts();
        var unsaved_idx = g_unsaved_igs.indexOf(ig_name);
        if (unsaved_idx > -1) {
            g_unsaved_igs.splice(unsaved_idx, 1);
        }
        phantom_ig_buttons(true);
    }

    var error_func = function(obj, message) {
        phantom_alert(message);
        phantom_ig_buttons(true);
    }

    if (g_unsaved_igs.indexOf(ig_name) > -1) {
        var url = make_url("imagegenerators");
        phantomPOST(url, data, success_func, error_func);
    }
    else {
        var ig_id = g_ig_info[ig_name]['id']
        var url = make_url("imagegenerators/" + ig_id);
        phantomPUT(url, data, success_func, error_func);
    }
    phantom_info("Saving " + ig_name + " image generator");
    phantom_ig_buttons(false);
}

function phantom_ig_save_click() {
    try {
        phantom_ig_save_click_internal();
    }
    catch (err) {
        alert(err);
    }
}

function reset_cloud_and_options() {
    $("#cloud_table_body").empty();
    $("#phantom_ig_instance").empty();
    $("#phantom_ig_script").val("");
    $("#phantom_ig_common_image_input").val("");
    $("#phantom_ig_instance").empty();
    $("#phantom_ig_ssh_username").empty();
    $("#phantom_ig_new_image_name").empty();
    $("#phantom_ig_user_images_choices").empty();
    $("#image_generator_options_head").text("Image Generator");
    $("#cloud_options_name").text("Cloud");
}

function phantom_ig_delete_internal(ig_name) {

    var success_func = function(obj) {
        g_selected_ig = null;
        g_selected_cloud = null;
        $("a.image_generator").filter(function() { return $(this).text() == ig_name}).parent().remove();
        reset_cloud_and_options();
        phantom_ig_buttons(true);
        $("#phantom_ig_info_area").hide();
        $("#phantom_ig_order_area").hide();
        clear_phantom_alerts();
    }

    var error_func = function(obj, message) {
        phantom_ig_buttons(true);
        phantom_alert(message);
    }

    var url = make_url("imagegenerators/" + g_ig_info[ig_name]['id']);

    $("#phantom_ig_name_select").empty();
    phantom_ig_buttons(false);

    // If ig hasn't been saved yet
    var unsaved_idx = g_unsaved_igs.indexOf(ig_name);
    if (unsaved_idx > -1) {
        g_unsaved_igs.splice(unsaved_idx, 1);
        success_func();
        return;
    }

    phantom_info("Deleting " + ig_name + " image generator");
    phantomDELETE(url, success_func, error_func);
}

function check_phantom_image_build(ig_id, ib_id) {
    var success_func = function(image_build) {
      if (image_build["ready"] === true) {
        switch (image_build["status"]) {
          case "submitted":
            setTimeout(function() {
              check_phantom_image_build(ig_id, ib_id)
            }, 1000);
            break;
         case "successful":
           phantom_ig_buttons(true);
           if (image_build["returncode"] == 0) {
             phantom_info("Generated image " + image_build["ami_name"] + "on cloud ec2");
           } else {
             clear_phantom_alerts();
             phantom_warning("Failed to generator image: " + image_build["full_output"]);
           }
           break;
         default:
           phantom_warning("Received image build response with status " + image_build["status"])
        }
      } else {
        setTimeout(function() {
          check_phantom_image_build(ig_id, ib_id)
        }, 1000);
      }
    }

    var error_func = function(obj, message) {
      phantom_ig_buttons(true);
      phantom_alert(message);
    }

    var url = make_url("imagegenerators/" + ig_id + "/builds/" + ib_id)
    var image_build = phantomGET(url, success_func, error_func);
}

function phantom_image_generator_run() {
  var ig_name = g_selected_ig;
  if (!ig_name) {
      phantom_warning("You must select an existing image generator name to run.")
      return;
  }

  var ig_id = g_ig_info[ig_name]['id']

  var success_func = function(new_image_build) {
      clear_phantom_alerts();
      phantom_info("Generating images from image generator " + ig_name);
      phantom_ig_buttons(false);
      setTimeout(function() {
        check_phantom_image_build(ig_id, new_image_build['id'])
      }, 1000);
  }

  var error_func = function(obj, message) {
      phantom_alert(message);
      phantom_ig_buttons(true);
  }

  var url = make_url("imagegenerators/" + ig_id + "/builds");
  var data = {}
  phantomPOST(url, data, success_func, error_func);
}

function phantom_ig_delete_click() {

    var ig_name = g_selected_ig;
    if (!ig_name) {
        phantom_warning("You must select an existing image generator name to delete.")
        return;
    }

    var q = "Are you sure you want to delete the image generator ".concat(ig_name).concat("?");
    var doit = confirm(q);
    if(!doit) {
        return;
    }

    try {
        phantom_ig_delete_internal(ig_name);
    }
    catch (err) {
        alert(err);
    }
}

function phantom_ig_order_selected_click(cloud_name) {

    g_selected_cloud = cloud_name;

    $("#phantom_ig_info_area").show();

    $("#cloud_table_body").children().removeClass("info");
    $("#cloud_table_body tr td").filter(function() { return $(this).text() == cloud_name}).parent().addClass("info");

    if (cloud_name.toLowerCase() === "ec2") {
        $("#cloud_options_name").text(cloud_name.toUpperCase());
    }
    else {
        $("#cloud_options_name").text(cloud_name.toProperCase());
    }

    try {
        var cloud_val_dict = g_arranged_cloud_values[cloud_name];
        if (cloud_val_dict) {

            $("#phantom_ig_cloud").val(cloud_name);
            phantom_ig_select_new_cloud_internal(cloud_name);

            $("#phantom_ig_instance").val(cloud_val_dict['instance_type']);
            $("#phantom_ig_ssh_username").val(cloud_val_dict['ssh_username']);
            $("#phantom_ig_new_image_name").val(cloud_val_dict['new_image_name']);

            if (cloud_val_dict['common'] === true) {
                $("#phantom_ig_common_image_input").val(cloud_val_dict['image_id']);
                $("#phantom_ig_common_choice_checked").attr('checked',true);
            }
            else {
                $("#phantom_ig_user_images_choices").val(cloud_val_dict['image_id']);
                $("#phantom_ig_user_choice_checked").attr('checked',true);
            }
            phantom_ig_change_image_type();
            $("#cloud-disable-buttons").show();
            $("#cloud-enable-buttons").hide();
        }
        else {
            phantom_ig_select_new_cloud_internal(cloud_name);
            $("#cloud-disable-buttons").hide();
            $("#cloud-enable-buttons").show();
        }
    }
    catch (err) {
        phantom_alert("There was a problem loading the page.  Please try again later. ".concat(err.message));
    }
}
