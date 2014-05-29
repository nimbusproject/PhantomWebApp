var g_cloud_map = {};
var g_arranged_cloud_values = {};
var g_ig_info = {};
var g_ib_info = {};
var g_unsaved_igs = [];
var g_blank_name = "<new name>";
var g_selected_ig = null;
var g_selected_cloud = null;
var g_current_builds_timer = null;
var g_current_builds_request = null;
var MAX_PUBLIC_IMAGES_ITEMS = 200;
var BUILDS_TIMER_MS = 5000;

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

    $("#image_build_table_body").on('click', 'tr', function(event){
        $(this).parent().children().removeClass("info");
        var image_build_id = $(this).children().first().text();
        show_image_build_details(image_build_id);
    });

    phantom_ig_load();
});


function get_image_build(image_generator_id, image_build_id) {
    var image_build = null;
    image_build = g_ib_info[image_generator_id][image_build_id];
    return image_build;
}


function show_image_build_details(image_build_id) {
    function make_row(key, value) {
      return "<tr><td><strong>" + key + ":</strong></td><td>" + value + "</td></tr>";
    }

    if (image_build_id === null) {
        return;
    }

    $("#image_build_table_body").children().removeClass("info");
    var matched_row = $("#image_build_table_body tr td:contains('" + image_build_id + "')")
      .parent().addClass("info");

    // If this image build isn't shown right now, we don't want to display it.
    // This could happen when image builds are filtered
    // Unused at the moment
    if (matched_row.length === 0) {
        return;
    }

    var table = $("#image_build_details_table_body").empty();
    var image_generator = g_ig_info[g_selected_ig];
    var image_build = get_image_build(image_generator["id"], image_build_id)
    if (image_build === null) {
      return;
    }

    g_selected_image_build = image_build_id;
    var status = image_build["status"]
    var returncode = image_build["returncode"]

    var data = make_row("Image build", image_build["id"]) +
      make_row("Status", image_build["status"]);

    if (status != "submitted") {
      if (returncode == -1) {
        data += make_row("Error message", image_build["full_output"]);
      } else if (returncode == 0) {
        var artifacts = image_build["artifacts"]
        var image_list = "<ul>"
        for (var cloud_name in artifacts) {
          image_list += "<li>" + cloud_name + ": " + artifacts[cloud_name] + "</li>";
        }
        image_list += "</ul>"
        data += make_row("Return code", returncode) +
          make_row("Image names", image_list) +
          make_row("Full output", "<pre>" + image_build["full_output"] + "</pre>");
      } else {
        data += make_row("Return code", returncode) +
          make_row("Full output", "<pre>" + image_build["full_output"] + "</pre>");
      }
    }

    table.append(data);
}

function phantom_ig_buttons(enabled) {
    if (enabled) {
        //$("button, input, select").removeAttr("disabled");
        $("#phantom_ig_button_add").removeAttr("disabled")
            .parent().removeClass("disabled");
        phantom_ig_change_image_type();
        $('#loading').hide();
    }
    else {
        //$("button, input, select").attr("disabled", true);
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
    $("#phantom_ig_ssh_username").val("");
    $("#phantom_ig_new_image_name").val("");

    if (cloud_data.type != "nimbus") {
      // Disable the public image checkbox
      if ($("#phantom_ig_public_image").is(':checked')) {
        $("#phantom_ig_public_image").attr('checked', false);
      }
      $("#phantom_ig_public_image").attr("disabled", "disabled");
    } else {
      $("#phantom_ig_public_image").removeAttr("disabled");
    }

    if (cloud_data.type != "ec2") {
      // Disable the instance type selection field
      $("#phantom_ig_instance").attr("disabled", "disabled");
    } else {
      for (instance in cloud_data.instance_types) {
          var i = cloud_data.instance_types[instance];
          var new_opt = $('<option>', {'name': i, value: i, text: i});
          $("#phantom_ig_instance").append(new_opt);
      }
    }
    $("#phantom_ig_common_image_input").val("");

    $("#phantom_ig_user_images_choices").empty();
    for (personal in cloud_data.user_images) {
        var i = cloud_data.user_images[personal];
        var new_opt = $('<option>', {'name': i, value: i, text: i});
        $("#phantom_ig_user_images_choices").append(new_opt);
    }

    if (public_images_typeahead) {
      if (cloud_data.type != "openstack") {
        public_images_typeahead.source = cloud_data.public_images;
      } else {
        public_images_typeahead.source = null;
      }
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

function make_image_build_table_row(image_build) {
    var status = image_build["status"]
    var id = image_build["id"]
    if (status === "successful") {
        status = '<span class="label label-success">' + status + '</span>';
    }
    else if (status === "submitted") {
        status = '<span class="label label-warning">' + status + '</span>';
    }
    else if (status === "failed") {
        status = '<span class="label label-important">' + status + '</span>';
    }
    else {
        status = '<span class="label">' + status + '</span>';
    }

    var row = "<tr id='image-build-row-" + id + "'>" +
      "<td class='image-build-id'>" + id + "</td>" +
      "<td>" + status + "</td>" +
      "</tr>";
    return row;
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

function phantom_image_builds_abort() {
    if (g_current_builds_request !== null) {
        try {
            g_current_builds_request.abort();
        }
        catch (e) {
        }
        g_current_builds_request = null;
    }
    if (g_current_builds_timer !== null) {
        window.clearInterval(g_current_builds_timer);
        g_current_builds_timer = null;
    }
    //phantom_domain_details_buttons(true);
}

function phantom_image_builds_internal() {
    phantom_image_builds_abort();
    //phantom_domain_details_buttons(false);
    $("#image_build_table_body").empty();

    ig = g_ig_info[g_selected_ig];

    var table_body = $("#image_build_table_body");

    for (var ibx in g_ib_info[ig["id"]]) {
      image_build = g_ib_info[ig["id"]][ibx];
      var row = make_image_build_table_row(image_build);
      table_body.append(row);
    }

    //var domain_name = $("#phantom_domain_name_label").text();
    //if (!domain_name || ! g_domain_data[domain_name]) {
        //return;
    //}

    //var domain_id = g_domain_data[domain_name]['id'];
    //if (!domain_id) {
        //return;
    //}

    //if (domain_name in g_domain_details_cache) {
        //g_domain_details = g_domain_details_cache[domain_name];
        //phantom_domain_load_instances();
        //show_instance_details(g_selected_instance);
        //show_domain_details(domain_name);
    //}

    //var data = {'name': domain_name};

    //var success_func = function(instances) {
        //g_current_details_request = null;
        //$("#phantom_domain_instance_details").empty();

        //g_domain_details = {
            //'instances': instances
        //}
        //g_domain_details_cache[domain_name] = g_domain_details;

        //phantom_domain_load_instances();
        //phantom_domain_buttons(true);
        //phantom_domain_details_buttons(true);
        //show_instance_details(g_selected_instance);
        //show_domain_details(domain_name);
    //}

    //var error_func = function(obj, message) {
        //g_current_details_request = null;
        //phantom_domain_buttons(true);
        //phantom_domain_details_buttons(true);
    //}

    //var url = make_url("domains/" + domain_id + "/instances");
    //g_current_details_request =  phantomGET(url, success_func, error_func);
    //
    if ("id" in ig) {
      get_phantom_image_builds(ig["id"]);
    }
}

function phantom_start_builds_timer() {
    g_current_builds_timer = window.setTimeout(phantom_image_builds_internal, BUILDS_TIMER_MS);
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
    $("#image_build_details_table_body").empty();

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

    phantom_image_builds_internal();

    //var ib_url = make_url("imagegenerators/" + ig["id"] + "/builds")
    //var image_builds = phantomGET(ib_url, success_func, error_func);
    //setTimeout(function() {
      //check_phantom_image_build(ig_id, new_image_build['id'])
    //}, 1000);
}

function get_phantom_image_builds(ig_id) {
    var success_func = function(image_builds) {
      try {
          clear_phantom_alerts();
          //$("#phantom_ig_name_select").empty();
          //$("#phantom_ig_cloud").empty();
          g_ib_info[ig_id] = {}
          for (var i = 0; i < image_builds.length; i++) {
              var image_build = image_builds[i];
              g_ib_info[ig_id][image_build["id"]] = image_build;
          }
          phantom_start_builds_timer();

          //phantom_ig_load_ig_names();
          //phantom_ig_load_cloud_names();
          //var cloud_name = g_selected_cloud;
          //phantom_ig_select_new_cloud_internal(cloud_name);
          //phantom_ig_change_image_type();

          //var ig_name_from_saved = $("#phantom_ig_name_input").val();
          //if (ig_name_from_saved) {
              //// if it was a saved name load up its value
              //$("#phantom_ig_name_select").val(ig_name_from_saved);
          //}

          //if (g_selected_ig === null) {
              //var url_ig = get_hash_ig();
              //var first_ig = $("a.image_generator").first().text();

              //if (g_ig_info.hasOwnProperty(url_ig)) {
                  //g_selected_ig = url_ig;
                  //phantom_ig_load_ig_names();
              //}
              //else if (first_ig) {
                  //g_selected_ig = first_ig;
                  //phantom_ig_load_ig_names();
              //}
              //else {
                  //$("#phantom_ig_info_area").hide();
                  //$("#phantom_ig_order_area").hide();
              //}
          //}

          phantom_ig_buttons(true);
      }
      catch (err) {
          phantom_alert("There was a problem loading the page.  Please try again later. ".concat(err.message));
          $('#loading').hide();
      }
      // FIXME
      //if (image_build["ready"] === true) {
        //switch (image_build["status"]) {
          //case "submitted":
            //setTimeout(function() {
              //check_phantom_image_build(ig_id, ib_id)
            //}, 1000);
            //break;
         //case "successful":
           //phantom_ig_buttons(true);
           //if (image_build["returncode"] == 0) {
             //phantom_info("Generated image " + image_build["ami_name"] + " on cloud " + image_build["cloud_name"]);
           //} else {
             //clear_phantom_alerts();
             //phantom_warning("Failed to generator image: " + image_build["full_output"]);
           //}
           //break;
         //case "failed":
           //phantom_ig_buttons(true);
           //clear_phantom_alerts();
           //phantom_warning("Failed to generate image: " + image_build["full_output"]);
           //break;
         //default:
           //phantom_warning("Received image build response with status " + image_build["status"])
        //}
      //} else {
        //setTimeout(function() {
          //get_phantom_image_builds(ig_id)
        //}, 1000);
      //}
    }

    var error_func = function(obj, message) {
      phantom_ig_buttons(true);
      phantom_alert(message);
    }

    var url = make_url("imagegenerators/" + ig_id + "/builds")
    var image_builds = phantomGET(url, success_func, error_func);
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
            if (site['image_generation']) {
              g_cloud_map[site.id] = {};
              g_cloud_map[site.id]['user_images'] = site['user_images'];
              g_cloud_map[site.id]['public_images'] = site['public_images'];
              g_cloud_map[site.id]['instance_types'] = site['instance_types'];
              g_cloud_map[site.id]['type'] = site['type'];
            }
        }
    }

    var load_credentials_success = function(clouds) {
        for(var i=0; i<clouds.length; i++) {
            var cloud = clouds[i];
            if (cloud.id in g_cloud_map) {
                g_cloud_map[cloud.id]['status'] = 0;
            }
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
                get_phantom_image_builds(imagegenerator["id"])
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

    var cloud_data = g_cloud_map[cloud_name];
    if (!cloud_data || cloud_data['status'] != 0) {
        return false;
    }

    var instance_type = ($("#phantom_ig_instance").val() || "").trim();
    var ssh_username = $("#phantom_ig_ssh_username").val().trim();
    var new_image_name = $("#phantom_ig_new_image_name").val().trim();
    var public_image = $("#phantom_ig_public_image").is(':checked');
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
      if (cloud_data.type == "ec2") {
         $("#phantom_ig_instance").parent().addClass("error");
         phantom_alert("You must select an instance type.");
         return false;
      }
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
        'public_image': public_image,
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
        site['public_image'] = cloud_data['public_image'];
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
    g_ig_info[g_selected_ig]['cloud_params'] = g_arranged_cloud_values
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
    $("#phantom_ig_ssh_username").val("");
    $("#phantom_ig_new_image_name").val("");
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

    delete g_ig_info[ig_name]
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
             phantom_info("Generated image " + image_build["ami_name"] + " on cloud " + image_build["cloud_name"]);
           } else {
             clear_phantom_alerts();
             phantom_warning("Failed to generator image: " + image_build["full_output"]);
           }
           break;
         case "failed":
           phantom_ig_buttons(true);
           clear_phantom_alerts();
           phantom_warning("Failed to generate image: " + image_build["full_output"]);
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
      phantom_info("Starting image generator " + ig_name);
      phantom_ig_buttons(false);
      //setTimeout(function() {
        //check_phantom_image_build(ig_id, new_image_build['id'])
      //}, 1000);
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
            $("#phantom_ig_public_image").attr('checked', cloud_val_dict['public_image']);

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
