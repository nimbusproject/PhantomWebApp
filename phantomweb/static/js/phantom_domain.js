var g_domain_data = {};
var g_launch_config_names = {};
var g_domain_details = {};
var g_decision_engines_by_name = {'Sensor': 'sensor', 'Multi Cloud': 'multicloud'};
var g_decision_engines_by_type = {'sensor': 'Sensor', 'multicloud': 'Multi Cloud'};
var DEFAULT_DECISION_ENGINE = 'Multi Cloud';

$(document).ready(function() {

    $("#phantom_domain_main_combined_pane_inner").hide();

    $("#phantom_domain_de_choice").val(DEFAULT_DECISION_ENGINE)
    phantom_select_de(DEFAULT_DECISION_ENGINE);

    phantom_domain_load();

    $("body").click(function() {
        phantom_domain_noncontext_mouse_down();
    })

    $("#phantom_domain_update_button").click(function() {
        phantom_domain_update_click();
    })

    $("#phantom_domain_de_choice").change(function() {
        phantom_select_de($("#phantom_domain_de_choice").val());
    });

    $("#phantom_domain_button_add").click(function() {
        phantom_add_domain_click();
    });

    $("#phantom_domain_list_domains").change(function() {
        phantom_domain_select_domain();
    });

    $("#phantom_domain_list_domains option").click(function() {
        phantom_domain_select_domain();
    });

    $("#phantom_domain_button_start").click(function() {
        phantom_domain_start_click();
    });

    $("#phantom_domain_button_resize").click(function() {
        phantom_domain_resize_click();
    });

    $("#phantom_domain_button_terminate").click(function() {
        phantom_domain_terminate_click();
    });
});


function phantom_domain_buttons(enabled) {

    if (enabled) {
        $("input, select").removeAttr("disabled");
        $('#phantom_domain_loading_image').hide();
    }
    else {
        $("input, select").attr("disabled", true);
        $('#phantom_domain_loading_image').show();
    }
}

function phantom_add_domain_click() {
    var new_domain_name = prompt("Enter a new domain name:");
    g_domain_data[new_domain_name] = {};
    phantom_domain_load_domain_names();

    $("#phantom_domain_list_domains").val(new_domain_name);
    phantom_domain_select_domain();
}

function phantom_domain_load_lc_names() {
    $("#phantom_domain_lc_choice").empty();

    for(var lc_name in g_launch_config_names) {
        lc_name = g_launch_config_names[lc_name];
        var new_opt = $('<option>', {'name': lc_name, value: lc_name, text: lc_name});
        $("#phantom_domain_lc_choice").append(new_opt);
    }
}

function phantom_domain_load_domain_names() {
    var previously_selected_domain = $("#phantom_domain_list_domains").val();
    $("#phantom_domain_list_domains").empty();

    for(var domain_name in g_domain_data) {
        var new_opt = $('<option>', {'name': domain_name, value: domain_name, text: domain_name});
        $("#phantom_domain_list_domains").append(new_opt);
    }

    $("#phantom_domain_list_domains").val(previously_selected_domain);
}

function phantom_domain_load_de_names() {
    $("#phantom_domain_de_choice").empty();

    for(var decision_engine in g_decision_engines_by_name) {
        var new_opt = $('<option>', {'name': decision_engine, value: decision_engine, text: decision_engine});
        $("#phantom_domain_de_choice").append(new_opt);
    }
}

function phantom_select_de(decision_engine) {
    var current_de = $("#phantom_domain_de_choice").val();

    if (decision_engine === "Sensor") {
        $("#phantom_domain_de_choice").val("Sensor");
        $(".phantom_domain_de_pref").hide().filter("#phantom_domain_sensor_preferences").show();
        $("#phantom_domain_sensor_preferences").show();
    }
    else if (decision_engine === "Multi Cloud") {
        $("#phantom_domain_de_choice").val("Multi Cloud");
        $(".phantom_domain_de_pref").hide().filter("#phantom_domain_multicloud_preferences").show();
    }
    else {
        console.log("Don't know de type: " + decision_engine);
    }
}

function phantom_domain_load_internal() {

    var success_func = function(obj) {
        $("#phantom_domain_instance_details").empty();

        g_domain_data = obj.domains;
        g_launch_config_names = obj.launchconfigs;

        phantom_domain_load_lc_names();
        phantom_domain_load_domain_names();
        phantom_domain_load_de_names();
        phantom_domain_buttons(true);
    };

    var error_func = function(obj, message) {
        alert(message);
        $('#phantom_domain_loading_image').hide();
    }

    var url = make_url('api/domain/load')
    phantom_domain_buttons(false);
    phantomAjaxPost(url, {}, success_func, error_func);
}

function phantom_domain_load() {
    try {
        phantom_domain_load_internal();
    }
    catch(err) {
        alert(err);
    }
}

// TODO: refactor for DRY with resize
function phantom_domain_start_click_internal() {
    var url = make_url('api/domain/start');
    var lc_name = $("#phantom_domain_lc_choice").val();
    var domain_name = $("#phantom_domain_name_label").text();
    var de_name = g_decision_engines_by_name[$("#phantom_domain_de_choice").val()];

    // Multicloud attrs
    var vm_count = $("#phantom_domain_size_input").val();

    // Sensor attrs
    var metric = $("#phantom_domain_metric_input").val();
    var cooldown = $("#phantom_domain_cooldown_input").val();
    var minimum_vms = $("#phantom_domain_minimum_input").val();
    var maximum_vms = $("#phantom_domain_maximum_input").val();
    var scale_up_threshold = $("#phantom_domain_scale_up_threshold_input").val();
    var scale_up_vms = $("#phantom_domain_scale_up_n_vms_input").val();
    var scale_down_threshold = $("#phantom_domain_scale_down_threshold_input").val();
    var scale_down_vms = $("#phantom_domain_scale_down_n_vms_input").val();

    var error_msg = undefined;

    if (lc_name == undefined || lc_name == "" || lc_name == null) {
        error_msg = "You must select a launch configuration name";
    }
    if (domain_name == undefined || domain_name == "" || domain_name == null) {
        error_msg = "You must specify a domain name";
    }

    var data = {"name": domain_name, "lc_name": lc_name, "de_name": de_name};

    if (de_name == "multicloud") {
        if (! vm_count) {
            error_msg = "You must specify a total number of vms";
        }

        data["vm_count"] = vm_count;
    }
    else if (de_name == "sensor") {
        if (! metric) {
            error_msg = "You must specify a metric";
        }
        if (! cooldown) {
            error_msg = "You must specify a cooldown";
        }
        if (! minimum_vms) {
            error_msg = "You must specify a minimum number of vms";
        }
        if (! maximum_vms) {
            error_msg = "You must specify a maximum number of vms";
        }
        if (! scale_up_threshold) {
            error_msg = "You must specify a scale up threshold";
        }
        if (! scale_up_vms) {
            error_msg = "You must specify a number of vms to scale up by";
        }
        if (! scale_down_threshold) {
            error_msg = "You must specify a scale down threshold";
        }
        if (! scale_down_vms) {
            error_msg = "You must specify a number of vms to scale down by";
        }

        data["sensor_metric"] = metric;
        data["sensor_cooldown"] = cooldown;
        data["sensor_minimum_vms"] = minimum_vms;
        data["sensor_maximum_vms"] = maximum_vms;
        data["sensor_scale_up_threshold"] = scale_up_threshold;
        data["sensor_scale_up_vms"] = scale_up_vms;
        data["sensor_scale_down_threshold"] = scale_down_threshold;
        data["sensor_scale_down_vms"] = scale_down_vms;
    }

    if (error_msg != undefined) {
        alert(error_msg);
        return;
    }

    var success_func = function(obj) {
        phantom_domain_load_internal();
        $("#phantom_domain_start_buttons").hide();
        $("#phantom_domain_running_buttons").show();
        $("#phantom_domain_list_domains").val(domain_name);
        phantom_domain_details_internal();
    }

    var error_func = function(obj, message) {
        alert(message);
        phantom_domain_buttons(true);
    }

    phantom_domain_buttons(false);
    phantomAjaxPost(url, data, success_func, error_func);
}

function phantom_domain_start_click() {
    try {
        phantom_domain_start_click_internal();
    }
    catch(err) {
        alert(err);
    }
}

function phantom_domain_resize_click_internal() {
    var url = make_url('api/domain/resize');
    var lc_name = $("#phantom_domain_lc_choice").val();
    var domain_name = $("#phantom_domain_name_label").text();
    var de_name = g_decision_engines_by_name[$("#phantom_domain_de_choice").val()];

    // Multicloud attrs
    var vm_count = $("#phantom_domain_size_input").val();

    // Sensor attrs
    var metric = $("#phantom_domain_metric_input").val();
    var cooldown = $("#phantom_domain_cooldown_input").val();
    var minimum_vms = $("#phantom_domain_minimum_input").val();
    var maximum_vms = $("#phantom_domain_maximum_input").val();
    var scale_up_threshold = $("#phantom_domain_scale_up_threshold_input").val();
    var scale_up_vms = $("#phantom_domain_scale_up_n_vms_input").val();
    var scale_down_threshold = $("#phantom_domain_scale_down_threshold_input").val();
    var scale_down_vms = $("#phantom_domain_scale_down_n_vms_input").val();

    var error_msg = undefined;

    if (! lc_name) {
        error_msg = "You must select a launch configuration name";
    }
    if (! domain_name) {
        error_msg = "You must specify a domain name";
    }

    var data = {"name": domain_name, "lc_name": lc_name, "de_name": de_name};

    if (de_name == "multicloud") {
        if (! vm_count) {
            error_msg = "You must specify a total number of vms";
        }

        data["vm_count"] = vm_count;
    }
    else if (de_name == "sensor") {
        if (! metric) {
            error_msg = "You must specify a metric";
        }
        if (! cooldown) {
            error_msg = "You must specify a cooldown";
        }
        if (! minimum_vms) {
            error_msg = "You must specify a minimum number of vms";
        }
        if (! maximum_vms) {
            error_msg = "You must specify a maximum number of vms";
        }
        if (! scale_up_threshold) {
            error_msg = "You must specify a scale up threshold";
        }
        if (! scale_up_vms) {
            error_msg = "You must specify a number of vms to scale up by";
        }
        if (! scale_down_threshold) {
            error_msg = "You must specify a scale down threshold";
        }
        if (! scale_down_vms) {
            error_msg = "You must specify a number of vms to scale down by";
        }

        data["sensor_metric"] = metric;
        data["sensor_cooldown"] = cooldown;
        data["sensor_minimum_vms"] = minimum_vms;
        data["sensor_maximum_vms"] = maximum_vms;
        data["sensor_scale_up_threshold"] = scale_up_threshold;
        data["sensor_scale_up_vms"] = scale_up_vms;
        data["sensor_scale_down_threshold"] = scale_down_threshold;
        data["sensor_scale_down_vms"] = scale_down_vms;
    }

    var success_func = function(obj) {
        //("#phantom_domain_size_input").val("");
        //$("#phantom_domain_list_domains").val(domain_name);
        phantom_domain_load_internal();
        //phantom_domain_select_domain();
    }

    var error_func = function(obj, message) {
        alert(message);
        phantom_domain_buttons(true);
    }

    phantom_domain_buttons(false);
    phantomAjaxPost(url, data, success_func, error_func);
}

function phantom_domain_resize_click() {
    try {
        phantom_domain_resize_click_internal();
    }
    catch(err) {
        alert(err);
    }
}

function phantom_domain_terminate_click_internal() {
    var url = make_url('api/domain/terminate');
    var domain_name = $("#phantom_domain_name_label").text();

    var error_msg = undefined;

    if(domain_name == undefined || domain_name == "" || domain_name == null) {
        error_msg = "You must specify a domain name";
    }
    if (error_msg != undefined) {
        alert(error_msg);
        return;
    }

    var data = {'name': domain_name}

    var success_func = function(obj) {
        delete g_domain_data[domain_name];
        $("#phantom_domain_name_label").text("");
        $("#phantom_domain_lc_choice").val("");
        $("#phantom_domain_size_input").val("");
        $("#phantom_domain_list_domains option[name*=" + domain_name + "]").remove();
        phantom_domain_deselect_domain();
        phantom_domain_buttons(true);
    }

    var error_func = function(obj, message) {
        alert(message);
        phantom_domain_buttons(true);
    }

    phantom_domain_buttons(false);
    phantomAjaxPost(url, data, success_func, error_func);

}

function phantom_domain_terminate_click() {
    try {
        phantom_domain_terminate_click_internal();
    }
    catch(err) {
        alert(err);
    }
}

function phantom_domain_select_domain_internal() {

    var domain_name = $("#phantom_domain_list_domains").val();
    if (!domain_name) {
        return;
    }

    $("#phantom_domain_main_combined_pane_inner").show();
    $("#phantom_domain_instance_details").empty();

    var domain_data = g_domain_data[domain_name];
    $("#phantom_domain_name_label").text(domain_name);

    if (Object.keys(domain_data).length == 0) {
        phantom_select_de(DEFAULT_DECISION_ENGINE);
        $("#phantom_domain_start_buttons").show();
        $("#phantom_domain_running_buttons").hide();
    }
    else {

        $("#phantom_domain_lc_choice").val(domain_data.lc_name);
        $("#phantom_domain_start_buttons").hide();
        $("#phantom_domain_running_buttons").show();
        phantom_select_de(g_decision_engines_by_type[domain_data.de_name]);

        if (domain_data.de_name == "multicloud") {
            $("#phantom_domain_size_input").val(domain_data.vm_size);
        }
        else if (domain_data.de_name == "sensor") {
            $("#phantom_domain_metric_input").val(domain_data.metric);
            $("#phantom_domain_cooldown_input").val(domain_data.sensor_cooldown);
            $("#phantom_domain_minimum_input").val(domain_data.sensor_minimum_vms);
            $("#phantom_domain_maximum_input").val(domain_data.sensor_maximum_vms);
            $("#phantom_domain_scale_up_threshold_input").val(domain_data.sensor_scale_up_threshold);
            $("#phantom_domain_scale_up_n_vms_input").val(domain_data.sensor_scale_up_vms);
            $("#phantom_domain_scale_down_threshold_input").val(domain_data.sensor_scale_down_threshold);
            $("#phantom_domain_scale_down_n_vms_input").val(domain_data.sensor_scale_down_vms);
        }
        phantom_domain_details_internal();
    }
}


function phantom_domain_select_domain() {
    try {
        phantom_domain_select_domain_internal();
    }
    catch(err) {
        alert(err);
    }
}

function phantom_domain_deselect_domain() {
    $("#phantom_domain_main_combined_pane_inner").show();
    $("#phantom_domain_instance_details").empty();
    $("#phantom_domain_main_combined_pane_inner").hide();
}

function phantom_domain_update_click() {
    try {
        phantom_domain_details_internal();
    }
    catch(err) {
        alert(err);
    }
}

function phantom_domain_load_instances() {

    $("#phantom_domain_instance_details").empty();
    for(var i in g_domain_details) {
        var instance = g_domain_details[i];

        var fields = new Array();
        fields[0] = instance.lifecycle_state;
        fields[1] = instance.cloud;
        fields[2] = instance.health_status;
        fields[3] = instance.hostname;
        fields[4] = instance.image_id;
        fields[5] = instance.instance_type;
        fields[6] = instance.keyname;
        var parsed_sensor_data = sensor_data_to_string(instance.sensor_data);
        if (parsed_sensor_data !== "") {
            fields[7] = instance.metric + ": " + sensor_data_to_string(instance.sensor_data);
        }

        var filter = $("#phantom_domain_filter_list").val();
        if (filter != "All") {
            if(filter == "Healthy" && (fields[0].indexOf("RUNNING") > 0 || fields[0].indexOf("PENDING") > 0 || fields[0].indexOf("REQUESTING") > 0)) {
            }
            else if (fields[0].indexOf(filter) < 0) {
                continue;
            }
        }

        var li = $("<li></li>");
        $("#phantom_domain_instance_details").append(li);
        var div = $('<div></div>').addClass('phantom_domain_instance_status_div');
        var h4 = $('<h4></h4>').addClass('phantom_domain_instance_status_name');
        h4.html(instance.instance_id);
        var ul = $('<ul></ul>').addClass('phantom_domain_instance_status_details_list');
        li.append(div);
        div.append(h4);
        div.append(ul);
        li.attr("id", instance.instance_id);
        li.click({param1: instance.instance_id, param2: instance.cloud}, phantom_domain_context_menu);

        for(var j = 0; j < fields.length; j++) {
            var subli = $('<li></li>').addClass('phantom_domain_instance_status_details_item');
            subli.html(fields[j]);
            ul.append(subli);
        }
    }
}

function sensor_data_to_string(sensor_data) {

    var str = "";
    for (var sensor_type in sensor_data) {
        if (sensor_type === "Series") {
            // Ignore series data because it is ugly :)
            continue;
        }
        str += sensor_type + ": " + sensor_data[sensor_type] + " ";
    }
    return str;
}

function phantom_domain_details_internal() {

    var domain_name = $("#phantom_domain_name_label").text();

    var url = make_url("api/domain/details");
    var data = {'name': domain_name};

    var success_func = function(obj) {
        var lc_name = obj.lc_name;
        var vm_count = obj.domain_size;

        g_domain_details = obj.instances;
        $("#phantom_domain_size_input").val(vm_count);
        $("#phantom_domain_lc_choice").val(lc_name);

        phantom_domain_load_instances();
        phantom_domain_buttons(true);
    }

    var error_func = function(obj, message) {
        alert(message);
        phantom_domain_buttons(true);
    }

    phantom_domain_buttons(false);
    phantomAjaxPost(url, data, success_func, error_func);
}


function phantom_domain_context_menu(e) {
    var obj = $("#phantom_domain_instance_context_menu");

    var o = {
                left: e.pageX,
                top: e.pageY
            };

    function nestedterminateClick() {
        try{
            phantom_domain_instance_terminate_click(e.data.param1, e.data.param2);
        }
        catch(err) {
            alert(err);
        }
    }
    obj.unbind("click");
    obj.click(nestedterminateClick);

    e.stopPropagation();
    obj.css(o);
    obj.show();
    obj.css('zIndex', 2000);
}

function phantom_domain_instance_terminate_click(instanceid, cloudname) {
    //phantom/
    var url = make_url('api/instance/termiante');

    var obj = $("#phantom_domain_instance_context_menu");
    var msg = "Do you want to kill the VM instance ".concat(instanceid).concat("?");
    var answer = confirm (msg);

    if (!answer) {
        return;
    }

    var success_func = function(obj){
        phantom_domain_details_internal();
    }

    var error_func = function(obj, message) {
        alert(message);
        phantom_domain_buttons(true);
    }

    var data = {'instance': instanceid, "adjust": false};
    phantom_domain_buttons(false);
    phantomAjaxPost(url, data, success_func, error_func);
}

function phantom_domain_noncontext_mouse_down() {
    var obj = $("#phantom_domain_instance_context_menu");
    if (obj.is(':visible') ) {
        obj.hide();
    }
}
