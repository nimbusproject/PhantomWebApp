var g_domain_data = {};
var g_launch_config_names = {};
var g_domain_details = {};

function phantom_domain_buttons(enabled) {

    var component_array = [
        "#phantom_domain_name_input",
        "#phantom_domain_size_input",
        "#phantom_domain_lc_choice",
        "#phantom_domain_button_start",
        "#phantom_domain_button_resize",
        "#phantom_domain_button_terminate",
        "#phantom_domain_button_list_choices",
        "#phantom_domain_filter_list",
        "#phantom_domain_update_button",
        "#phantom_domain_instance_details",
        "#phantom_domain_list_domains"
    ];

    if (enabled) {
        for (var comp in component_array) {
            comp = component_array[comp];
            $(comp).removeAttr("disabled", "disabled");
        }
        $('#phantom_domain_loading_image').hide();
    }
    else {
        for (var comp in component_array) {
            comp = component_array[comp];
            $(comp).attr("disabled", "disabled");
        }
        $('#phantom_domain_loading_image').show();
    }
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
    $("#phantom_domain_list_domains").empty();

    for(var domain_name in g_domain_data) {
        var new_opt = $('<option>', {'name': domain_name, value: domain_name, text: domain_name});
        $("#phantom_domain_list_domains").append(new_opt);
    }
}

function phantom_domain_load_internal() {

    var success_func = function(obj) {
        $("#phantom_domain_instance_details").empty();

        g_domain_data = obj.domains;
        g_launch_config_names = obj.launchconfigs;

        phantom_domain_load_lc_names();
        phantom_domain_load_domain_names();
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


function phantom_domain_start_click_internal() {
    var url = make_url('api/domain/start');
    var lc_name = $("#phantom_domain_lc_choice").val();
    var domain_name = $("#phantom_domain_name_input").val();
    var vm_count = $("#phantom_domain_size_input").val();

    var error_msg = undefined;

    if(lc_name == undefined || lc_name == "" || lc_name == null) {
        error_msg = "You must select a launch configuration name";
    }
    if(domain_name == undefined || domain_name == "" || domain_name == null) {
        error_msg = "You must specify a domain name";
    }
    if(vm_count == undefined || vm_count == "" || vm_count == null) {
        error_msg = "You must specify a total number of vms";
    }

    if (error_msg != undefined) {
        alert(error_msg);
        return;
    }

    var data = {'name': domain_name, "lc_name": lc_name, "vm_count": vm_count}

    var success_func = function(obj) {
        phantom_domain_load_internal();
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
     var domain_name = $("#phantom_domain_name_input").val();
     var new_size = $("#phantom_domain_size_input").val();

     var error_msg = undefined;

     if(domain_name == undefined || domain_name == "" || domain_name == null) {
        error_msg = "You must specify a domain name";
     }
     if(new_size == undefined || new_size == "" || new_size == null) {
        error_msg = "You must specify a new size";
     }
     if (error_msg != undefined) {
         alert(error_msg);
         return;
     }

     var data = {'name': domain_name, 'vm_count': new_size}

     var success_func = function(obj) {
         $("#phantom_domain_size_input").val("");
         phantom_domain_load_internal();
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
    var domain_name = $("#phantom_domain_name_input").val();

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
        $("#phantom_domain_name_input").val("");
        $("#phantom_domain_lc_choice").val("");
        $("#phantom_domain_size_input").val("");
        phantom_domain_load_internal();
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

    var domain_data = g_domain_data[domain_name];
    $("#phantom_domain_name_input").val(domain_name);
    $("#phantom_domain_size_input").val(domain_data.vm_size);
    $("#phantom_domain_lc_choice").val(domain_data.lc_name);

    phantom_domain_details_internal();
}


function phantom_domain_select_domain() {
    try {
        phantom_domain_select_domain_internal();
    }
    catch(err) {
        alert(err);
    }
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

function phantom_domain_details_internal() {

    var domain_name = $("#phantom_domain_list_domains").val();

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
