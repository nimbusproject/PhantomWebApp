var available_launch_configs = [];

$(document).ready(function() {

    $("#public_lc_table > tr").hide();
    $("#show-all-lc").hide();
    load_public_lcs();

    $("a.lc_id").click(function() {
        return false;
    });

    $("#show-all-lc").click(function() {
        window.location.hash = '';
        return false;
    });

    $(window).on('hashchange', function() {
        select_from_hash();
    });
});


function load_public_lcs() {

    var load_lc_success = function(launchconfigs) {
        for (var i=0; i<launchconfigs.length; i++) {
            var lc = launchconfigs[i];
            available_launch_configs.push(lc.id);
            make_lc_row(lc);
        }

        select_from_hash();
        $("#loading").hide();
    }

    var load_lc_failure = function(error) {
        console.log(error);
    }

    var lc_url = make_url('launchconfigurations?public=true')
    phantomGET(lc_url, load_lc_success, load_lc_failure);
}


function make_lc_row(lc) {

    var row = "<tr id='row-" + lc.id + "'><td><p class='lead'><a class='lc_id' href='#" + lc.id + "'>" + lc.name + "</a></p>" +
        "<p>By " + lc.owner + "</p>" +
        "<p><button class='btn btn-small import' data-name='" + lc.id + "'>Import</button></p></td>" +
        "<td><p class='lead'>&nbsp;</p><p>" + lc.description + "</td>" +
        "</tr>";
    $("#public_lc_table").append(row);
}

function select_from_hash() {
    var url_id = window.location.hash.substring(1);
    console.log(url_id);
    if (available_launch_configs.indexOf(url_id) > -1) {
        $("#public_lc_table tr").hide();
        $("#row-" + url_id).show();
        $("#show-all-lc").show();
    }
    else { // Default
        $("#public_lc_table tr").show();
        $("#show-all-lc").hide();
    }
}
