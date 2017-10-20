/**
 * Created by apple on 17/7/19.
 */

$('#nid_search_form').submit(function () {
    $(this).ajaxSubmit(function (data) {
        alert(data.msg);
        $('#nid_result').empty();
        if (data.status == 0) {
            data = data.data
            $('#nid_result').append("<td>" + data.nid + "</td>");
            $('#nid_result').append("<td>" + data.site_name + "</td>");
            $('#nid_result').append("<td>" + data.ch_name + "</td>");
            $('#nid_result').append("<td>" + data.show_type + "</td>");
            $('#nid_result').append("<td>" + data.qd_1 + "</td>");
            $('#nid_result').append("<td>" + data.qd_2 + "</td>");
            $('#nid_result').append("<td>" + data.mongo_1 + "</td>");
            $('#nid_result').append("<td>" + data.mongo_2 + "</td>");
            $('#nid_result').append("<td><a href='" + data.ch_url + "' target='_blank' >" + data.ch_url + "</a></td>");


        }
    });
    // return false to prevent normal browser submit and page navigation
    return false;
});