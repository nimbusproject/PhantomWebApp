var g_cloud_map = {};
var g_arranged_cloud_values = {};
var g_lc_info = {};
var g_unsaved_lcs = [];
var g_blank_name = "<new name>";
var g_selected_lc = null;
var g_selected_cloud = null;
var MAX_PUBLIC_IMAGES_ITEMS = 200;

$(document).ready(function() {
    $("#nav-launchconfig").addClass("active");

    $("#lc-nav").on("click", "a.launch_config", function() {
        var launch_config = $(this).text();
        phantom_lc_change_lc_internal(launch_config);
        return false;
    });

    $("#cloud_table_body").on('click', 'tr', function(event){
        $(this).parent().children().removeClass("info");
        var cloud_name = $(this).children().first().text();
        phantom_lc_order_selected_click(cloud_name);
    });

    $("#cloud_table_body").sortable({
        helper: function(e, tr)
          {
            var $originals = tr.children();
            var $helper = tr.clone();
            $helper.children().each(function(index)
            {
              // Set helper cell sizes to match the original sizes
              $(this).width($originals.eq(index).width())
            });
            return $helper;
          },
    });

    var $phantom_lc_common_image_input = $("#phantom_lc_common_image_input").typeahead({
        minLength: 0,
        items: MAX_PUBLIC_IMAGES_ITEMS,
    });

    //enable showing hints on click
    if ($phantom_lc_common_image_input.typeahead.bind) {
        $phantom_lc_common_image_input.on('focus', $phantom_lc_common_image_input.typeahead.bind($phantom_lc_common_image_input, 'lookup'));
        $phantom_lc_common_image_input.on('click', $phantom_lc_common_image_input.typeahead.bind($phantom_lc_common_image_input, 'lookup'));
    }


    $("#phantom_lc_add").click(function() {
        save_lc_values();
        return false;
    });

    $("#phantom_lc_disable_cloud").click(function() {
        phantom_lc_disable_click();
        return false;
    });

    var autosave_cloud_fields = "#phantom_lc_info_area input, #phantom_lc_info_area select, #phantom_lc_info_area";

    $(autosave_cloud_fields).change(function() {
        if (g_arranged_cloud_values[g_selected_cloud]) {
            save_lc_values();
        }
        return false;
    });

    $(autosave_cloud_fields).bind('keyup', function() {
        if (g_arranged_cloud_values[g_selected_cloud]) {
            save_lc_values();
        }
        return false;
    });

    $("#phantom_lc_order_area").on("keyup", "textarea", function() {
        save_lc_values();
        return false;
    });

    $("#phantom_lc_order_area").on("change", "select", function() {
        save_lc_values();
        return false;
    });

    $("#phantom_lc_max_vm").keydown(function(event) {
        // Allow: backspace, delete, tab, escape, and enter
        if ( event.keyCode == 46 || event.keyCode == 8 || event.keyCode == 9 ||
             event.keyCode == 27 || event.keyCode == 13 || event.keyCode == 189 ||
             // Allow: Ctrl+A
            (event.keyCode == 65 && event.ctrlKey === true) ||
             // Allow: home, end, left, right
            (event.keyCode >= 35 && event.keyCode <= 39)) {
                 // let it happen, don't do anything
                 return;
        }
        else {
            // Ensure that it is a number and stop the keypress
            if (event.shiftKey || (event.keyCode < 48 || event.keyCode > 57) && (event.keyCode < 96 || event.keyCode > 105 )) {
                event.preventDefault();
            }
        }
    });

    $("#lc-help").popover();

    $("#phantom_lc_button_add").click(function() {
        phantom_lc_add_lc_click();
        return false;
    });

    $("#phantom_lc_delete").click(function() {
        phantom_lc_delete_click();
        return false;
    });

    $("#phantom_lc_save").click(function() {
        phantom_lc_save_click();
        return false;
    });

    $("#phantom_lc_contextualization").change(function() {
        var context_type = $(this).val();
        select_contextualization_method(context_type);
    });

    phantom_lc_load();
});

function select_contextualization_method(context_type) {

    if (context_type == "chef") {
        $(".context-details").hide();
        $("#phantom_lc_chef_runlist").parent().show();
        $("#phantom_lc_chef_attributes").parent().show();
        $("#phantom_lc_contextualization").val("chef");
    }
    else if (context_type == "user_data") {
        $(".context-details").hide();
        $("#phantom_lc_userdata").parent().show();
        $("#phantom_lc_contextualization").val("user_data");
    }
    else {
        $(".context-details").hide();
        $("#phantom_lc_contextualization").val("none");
    }

}

function phantom_lc_buttons(enabled) {

    if (enabled) {
        $("button, input, select").removeAttr("disabled");
        $("#phantom_lc_button_add").removeAttr("disabled")
            .parent().removeClass("disabled");
        phantom_lc_change_image_type();
        $('#loading').hide();
    }
    else {
        $("button, input, select").attr("disabled", true);
        $("#phantom_lc_button_add").attr("disabled", true)
            .parent().addClass("disabled");
        $('#loading').show();
    }
}


function phantom_lc_load_error_func(obj, message) {
    phantom_lc_buttons(true);
    alert(message);
}

function phantom_lc_add_lc_click() {

    var new_lc_name = prompt("Enter a new launch config name:");
    if (new_lc_name === null) {
        return false;
    }

    if (g_lc_info.hasOwnProperty(new_lc_name)) {
        phantom_warning("You already have a launch config called " + new_lc_name);
        return false;
    }

    g_unsaved_lcs.push(new_lc_name);
    g_lc_info[new_lc_name] = {};
    g_selected_lc = new_lc_name;
    phantom_lc_load_lc_names();
}

function phantom_lc_select_new_cloud() {
    try
    {
        var cloud_name = $("#phantom_lc_cloud").val();
        phantom_lc_select_new_cloud_internal(cloud_name);
    }
    catch(err)
    {
        alert("There was a problem on the page.  ".concat(err.message));
        $('#loading').hide();
    }
    phantom_lc_buttons(true);
}

function phantom_lc_change_image_type() {
    if ($("#phantom_lc_common_choice_checked").is(':checked')) {
        $("#phantom_lc_common_image_input").removeAttr("disabled", "disabled");
        $("#phantom_lc_user_images_choices").attr("disabled", "disabled");
    }
    else {
        $("#phantom_lc_user_images_choices").removeAttr("disabled", "disabled");
        $("#phantom_lc_common_image_input").attr("disabled", "disabled");
    }
}

function phantom_lc_select_new_cloud_internal(cloud_name) {
    if (!cloud_name) {
        return;
    }
    var cloud_data = g_cloud_map[cloud_name];

    if (!cloud_data || cloud_data.status != 0) {
        return;
    }

    var public_images_typeahead = $('#phantom_lc_common_image_input').data('typeahead');
    public_images_typeahead.hide();

    $("#phantom_lc_max_vm").val("");
    $("#phantom_lc_instance").empty();
    for (instance in cloud_data.instance_types) {
        var i = cloud_data.instance_types[instance];
        var new_opt = $('<option>', {'name': i, value: i, text: i});
        $("#phantom_lc_instance").append(new_opt);
    }
    $("#phantom_lc_common_image_input").val("");

    $("#phantom_lc_user_images_choices").empty();
    for (personal in cloud_data.user_images) {
        var i = cloud_data.user_images[personal];
        var new_opt = $('<option>', {'name': i, value: i, text: i});
        $("#phantom_lc_user_images_choices").append(new_opt);
    }
    if (public_images_typeahead) {
        public_images_typeahead.source = cloud_data.public_images;
    }
}

function phantom_lc_load_cloud_names() {

    for(var site in g_cloud_map) {
        var cloud_data = g_cloud_map[site];
        if (!cloud_data) {
            phantom_alert("There was an error communicating with ".concat(site).concat(". You may still use the remaining clouds. Refresh later when the cloud is available."))        }
        else {
            var new_opt = $('<option>', {'name': site, value: site, text: site});
            $("#phantom_lc_cloud").append(new_opt);
        }
    }
}

function phantom_lc_load_lc_names() {
    $("#phantom_lc_name_input").val("");

    $("#lc-header").nextAll().remove();

    for (var lc_name in g_lc_info) {
        var lc = g_lc_info[lc_name];
        var new_lc = '<li><a href="#" class="launch_config" id="lc-' + lc_name + '">' + lc_name + '</a></li>';
        $("#lc-nav").append(new_lc);
    }
    phantom_lc_change_lc_internal(g_selected_lc);
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
      "<td>" + status + "<i class='icon-align-justify move-icon pull-right'></i></td>" +
      "</tr>";
    return row;
}

function phantom_lc_change_lc_internal(lc_name) {

    if (!lc_name) {
        $("#phantom_lc_order_area").hide();
        return;
    }

    g_selected_lc = lc_name;
    g_selected_cloud = null;
    var lc = g_lc_info[lc_name];

    $("#launch_config_options_head").text(lc_name + " Launch Configuration");

    $("a.launch_config").parent().removeClass("active");
    $("a.launch_config").filter(function() { return $(this).text() == lc_name}).parent().addClass("active");

    $("#cloud_options_name").text("cloud");
    $("#cloud_table_body").empty();


    if (lc_name == g_blank_name) {
        // set to blank values
        g_arranged_cloud_values = {};
        $("#phantom_lc_name_input").val("");
        $("#phantom_lc_name_input").text("");
        $("#phantom_lc_order").empty();

    }
    else {
        $("#phantom_lc_name_input").val(lc_name);
        $("#phantom_lc_name_input").text(lc_name);
        g_arranged_cloud_values = lc['cloud_params'];
        if (g_arranged_cloud_values === undefined) {
            g_arranged_cloud_values = {};
        }
        

        if (! ('contextualization_method' in lc)) {
            $("#phantom_lc_userdata").val(lc['user_data']);
            select_contextualization_method('user_data');
        }
        else if (lc['contextualization_method'] == 'user_data') {
            $("#phantom_lc_userdata").val(lc['user_data']);
            select_contextualization_method('user_data');
        }
        else if (lc['contextualization_method'] == 'chef') {
            $("#phantom_lc_chef_runlist").val(lc['chef_runlist']);
            $("#phantom_lc_chef_attributes").val(lc['chef_attributes']);
            select_contextualization_method('chef');
        }
        else {
            select_contextualization_method('none');
        }
    }

    $("#phantom_lc_max_vm").val("");
    
    $("#phantom_lc_order").empty();
    var ordered = Array();
    for (var site in g_arranged_cloud_values) {
        var s = g_arranged_cloud_values[site]
        var ndx = s.rank;
        if (ndx) {
            ordered[ndx - 1] = site;
        }
        else {
            ordered.push(site);
        }
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
        $("#phantom_lc_order").append(new_opt);
    }

    $("#phantom_lc_order_area").show();
}

function phantom_lc_change_lc_click(lc_name) {
    try {
        phantom_lc_change_lc_internal(lc_name);
    }
    catch(err) {
        phantom_alert(err);
    }
}

function phantom_lc_load_internal() {
    phantom_lc_buttons(false);
    var load_lc_success = function(launchconfigs) {
        try {
            $("#alert-container").empty();
            $("#phantom_lc_name_select").empty();
            $("#phantom_lc_cloud").empty();
            g_lc_info = {};
            for(var i=0; i<launchconfigs.length; i++) {
                var launchconfig = launchconfigs[i];
                g_lc_info[launchconfig.name] = launchconfig;
            }

            phantom_lc_load_lc_names();
            phantom_lc_load_cloud_names();
            var cloud_name = g_selected_cloud;
            phantom_lc_select_new_cloud_internal(cloud_name);
            phantom_lc_change_image_type();

            var lc_name_from_saved = $("#phantom_lc_name_input").val();
            if (lc_name_from_saved) {
                // if it was a saved name load up its value
                $("#phantom_lc_name_select").val(lc_name_from_saved);
            }

            if (g_selected_lc === null) {
                var first_lc = $("a.launch_config").first().text();
                if (first_lc) {
                    g_selected_lc = first_lc;
                    phantom_lc_load_lc_names();
                }
                else {
                    $("#phantom_lc_info_area").hide();
                    $("#phantom_lc_order_area").hide();
                }
            }

            phantom_lc_buttons(true);
        }
        catch (err) {
            phantom_alert("There was a problem loading the page.  Please try again later. ".concat(err.message));
            $('#loading').hide();
        }
    }

    var load_sites_success = function(sites) {

        for(var i=0; i<sites.length; i++) {
            var site = sites[i];
            if (!g_cloud_map.hasOwnProperty(site.id)) {
                g_cloud_map[site.id] = {};
            }
            g_cloud_map[site.id]['user_images'] = site['user_images'];
            g_cloud_map[site.id]['public_images'] = site['public_images'];
            g_cloud_map[site.id]['instance_types'] = site['instance_types'];
        }

        var lc_url = make_url('launchconfigurations')
        phantomGET(lc_url, load_lc_success, phantom_lc_load_error_func);
        phantom_info("Loading Launch Configurations");
    }

    var load_sites_failure = function(clouds) {

        phantom_alert("There was a problem loading your clouds.  Please try again later. ".concat(err.message));
        $('#loading').hide();
    }

    var load_credentials_success = function(clouds) {
        g_cloud_map = {};
        for(var i=0; i<clouds.length; i++) {
            var cloud = clouds[i];
            if (!g_cloud_map.hasOwnProperty(cloud.id)) {
                g_cloud_map[cloud.id] = {};
            }
            g_cloud_map[cloud.id]['status'] = 0;
            //TODO: add attrs from creds?
        }

        var sites_url = make_url('sites?details=true')
        phantomGET(sites_url, load_sites_success, load_sites_failure);
    }

    var load_credentials_failure = function(err) {
        phantom_alert("There was a problem loading your cloud credentials.  Please try again later. ".concat(err.message));
        $('#loading').hide();
    }

    var credentials_url = make_url('credentials/sites')
    phantomGET(credentials_url, load_credentials_success, load_credentials_failure);
}

function phantom_lc_load() {
    try {
        phantom_lc_load_internal();
    }
    catch(err) {
        alert(err);
    }
}

function save_lc_values() {

    $("#phantom_lc_info_area div").removeClass("error");

    var lc = g_lc_info[g_selected_lc];
    var cloud_name = g_selected_cloud;
    var contextualization_method = $("#phantom_lc_contextualization").val().trim();
    var chef_runlist = $("#phantom_lc_chef_runlist").val();
    var chef_attributes = $("#phantom_lc_chef_attributes").val();
    var user_data = $("#phantom_lc_userdata").val();

    if (contextualization_method == 'chef') {
        lc['contextualization_method'] = 'chef';
        lc['chef_runlist'] = chef_runlist;
        lc['chef_attributes'] = chef_attributes;
        delete lc['user_data'];
    }
    else if(contextualization_method == 'user_data') {
        lc['user_data'] = user_data;
        delete lc['chef_runlist'];
        delete lc['chef_attributes'];
    }
    else {
        lc['contextualization_method'] = 'none';
        delete lc['chef_runlist'];
        delete lc['chef_attributes'];
        delete lc['user_data'];
    }


    if (cloud_name === null) {
        return;
    }

    var max_vm = $("#phantom_lc_max_vm").val().trim();
    var instance_type = $("#phantom_lc_instance").val().trim();
    var common;
    var image_id = "";
    if ($("#phantom_lc_common_choice_checked").is(':checked')) {
        image_id = $("#phantom_lc_common_image_input").val().trim();
        common = true;
    }
    else {
        image_id = ($("#phantom_lc_user_images_choices").val() || "").trim();
        common = false;
    }

    if (!cloud_name) {
        phantom_warning("You must select a cloud.");
        return;
    }
    if (!max_vm) {
        $("#phantom_lc_max_vm").parent().addClass("error");
        phantom_warning("You must select a maximum number of VMs for this cloud.");
        return;
    }
    if (!image_id) {
        if ($("#phantom_lc_common_choice_checked").is(":checked")) {
            $("#phantom_lc_common_image_input").parent().addClass("error");
        }
        else {
            $("#phantom_lc_user_images_choices").parent().addClass("error");
        }
        phantom_warning("You must select an image.");
        return;
    }
    if (!instance_type) {
        $("#phantom_lc_instance").parent().addClass("error");
        phantom_alert("You must select an instance type.");
        return;
    }
    if (max_vm < -1 || max_vm > 32000) {
        $("#phantom_lc_max_vm").parent().addClass("error");
        phantom_warning("You must specify a maximum number of VMs between -1 (infinity) and 32000.");
        return;
    }

    var entry = {
        'cloud': cloud_name,
        'max_vms': max_vm,
        'image_id': image_id,
        'instance_type': instance_type,
        'common': common,
    };


    g_arranged_cloud_values[cloud_name] = entry;

    var new_row = make_cloud_table_row(cloud_name, "Enabled");
    $("#cloud_table_body tr td").filter(function() { return $(this).text() == cloud_name})
      .parent().replaceWith(new_row);
    phantom_lc_order_selected_click(cloud_name);

}

function phantom_lc_disable_click() {

    var cloud_name = g_selected_cloud;
    delete g_arranged_cloud_values[cloud_name];

    var new_row = make_cloud_table_row(cloud_name, "Disabled");
    $("#cloud_table_body tr td").filter(function() { return $(this).text() == cloud_name})
      .parent().replaceWith(new_row);
    phantom_lc_order_selected_click(cloud_name);
}


function phantom_lc_save_click_internal() {
    var lc_name = g_selected_lc;
    var lc = g_lc_info[lc_name];

    var err_msg = null;
    if (!lc_name) {
        err_msg = "You must select a launch configuration name."
    }

    if (err_msg) {
        phantom_alert(err_msg);
        return;
    }

    var data = {
        'name': lc_name,
        'cloud_params': {},
    };

    if (! ('contextualization_method' in lc)) {
        data['contextualization_method'] = 'user_data';
        data['user_data'] = lc['user_data'];
    }
    else if (lc['contextualization_method'] == 'user_data') {
        data['contextualization_method'] = 'user_data';
        data['user_data'] = lc['user_data'];
    }
    else if (lc['contextualization_method'] == 'chef') {
        data['contextualization_method'] = 'chef';
        data['chef_runlist'] = lc['chef_runlist'];
        data['chef_attributes'] = lc['chef_attributes'];
    }
    else {
        data['contextualization_method'] = 'none';
    }

    $("#cloud_table_body td.cloud-data-site").each(function(i) {

        var site_name = $(this).text();
        var cloud_data = g_arranged_cloud_values[site_name];

        if (!cloud_data) {
            return true; //each's equivalent of continue;
        }
        data['cloud_params'][site_name] = {};
        var site = data['cloud_params'][site_name];

        var ndx = i + 1;

        site['rank'] = ndx;
        site['image_id'] = cloud_data['image_id'];
        site['instance_type'] = cloud_data['instance_type'];
        site['max_vms'] = cloud_data['max_vms'];
        site['common'] = cloud_data['common'];

    });

    var success_func = function(obj) {
        $("#alert-container").empty();
        var unsaved_idx = g_unsaved_lcs.indexOf(lc_name);
        if (unsaved_idx > -1) {
            g_unsaved_lcs.splice(unsaved_idx, 1);
        }
        phantom_lc_buttons(true);
    }

    var error_func = function(obj, message) {
        phantom_alert(message);
        phantom_lc_buttons(true);
    }

    if (g_unsaved_lcs.indexOf(lc_name) > -1) {
        var url = make_url("launchconfigurations");
        phantomPOST(url, data, success_func, error_func);
    }
    else {
        var lc_id = g_lc_info[lc_name]['id']
        var url = make_url("launchconfigurations/" + lc_id);
        phantomPUT(url, data, success_func, error_func);
    }
    phantom_info("Saving " + lc_name + " launch configuration");
    phantom_lc_buttons(false);
}

function phantom_lc_save_click() {
    try {
        phantom_lc_save_click_internal();
    }
    catch (err) {
        alert(err);
    }
}

function reset_cloud_and_options() {
    $("#cloud_table_body").empty();
    $("#phantom_lc_instance").empty();
    $("#phantom_lc_max_vm").val("");
    $("#phantom_lc_userdata").val("");
    $("#phantom_lc_common_image_input").val("");
    $("#phantom_lc_instance").empty();
    $("#phantom_lc_user_images_choices").empty();
    $("#launch_config_options_head").text("Launch Configuration");
    $("#cloud_options_name").text("Cloud");
}

function phantom_lc_delete_internal(lc_name) {

    var success_func = function(obj) {
        g_selected_lc = null;
        g_selected_cloud = null;
        $("a.launch_config").filter(function() { return $(this).text() == lc_name}).parent().remove();
        reset_cloud_and_options();
        phantom_lc_buttons(true);
        $("#phantom_lc_info_area").hide();
        $("#phantom_lc_order_area").hide();
    }

    var error_func = function(obj, message) {
        phantom_lc_buttons(true);
        phantom_alert(message);
    }

    var url = make_url("launchconfigurations/" + g_lc_info[lc_name]['id']);

    $("#phantom_lc_name_select").empty();
    phantom_lc_buttons(false);

    // If lc hasn't been saved yet
    var unsaved_idx = g_unsaved_lcs.indexOf(lc_name);
    if (unsaved_idx > -1) {
        g_unsaved_lcs.splice(unsaved_idx, 1);
        success_func();
        return;
    }

    phantom_info("Deleting " + lc_name + " launch configuration");
    phantomDELETE(url, success_func, error_func);
}

function phantom_lc_delete_click() {

    var lc_name = g_selected_lc;
    if (!lc_name) {
        phantom_warning("You must select an existing launch configuration name to delete.")
        return;
    }

    var q = "Are you sure you want to delete the launch configuration ".concat(lc_name).concat("?");
    var doit = confirm(q);
    if(!doit) {
        return;
    }

    try {
        phantom_lc_delete_internal(lc_name);
    }
    catch (err) {
        alert(err);
    }
}

function phantom_lc_order_selected_click(cloud_name) {

    g_selected_cloud = cloud_name;

    $("#phantom_lc_info_area").show();

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

            $("#phantom_lc_cloud").val(cloud_name);
            phantom_lc_select_new_cloud_internal(cloud_name);

            $("#phantom_lc_max_vm").val(cloud_val_dict['max_vms']);
            $("#phantom_lc_instance").val(cloud_val_dict['instance_type']);


            if (cloud_val_dict['common']) {
                $("#phantom_lc_common_image_input").val(cloud_val_dict['image_id']);
                $("#phantom_lc_common_choice_checked").attr('checked',true);
            }
            else {
                $("#phantom_lc_user_images_choices").val(cloud_val_dict['image_id']);
                $("#phantom_lc_user_choice_checked").attr('checked',true);
            }
            phantom_lc_change_image_type();
            $("#cloud-disable-buttons").show();
            $("#cloud-enable-buttons").hide();
        }
        else {
            phantom_lc_select_new_cloud_internal(cloud_name);
            $("#cloud-disable-buttons").hide();
            $("#cloud-enable-buttons").show();
        }
    }
    catch (err) {
        phantom_alert("There was a problem loading the page.  Please try again later. ".concat(err.message));
    }
}
