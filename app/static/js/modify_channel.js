$('#cate1_select').change(function () {
    url = "/api/get_cate2";
    $.post(url, {parent: $(this).val()}, function (msg) {
        var json_data = eval(msg);
        var str = '<option value="0">--无--</option>';
        cate2_items = json_data["data"]
        for (var i = 0; i < cate2_items.length; i++) {
            var cate2_item = cate2_items[i];
            str += '<option value=' + cate2_item + '>' + cate2_item + '</option>';
        }
        $('#cate2_select').html(str);
    });
});

$('#qd_cate1').change(function () {
    url = "/api/get_qd_cate2";
    $.post(url, {chid: $(this).val()}, function (msg) {
        var json_data = eval(msg);
        var str = '<option value="0">--无--</option>';
        cate2_items = json_data["data"]
        for (var i = 0; i < cate2_items.length; i++) {
            var cate2_item = cate2_items[i];
            str += '<option value=' + cate2_item.id + '>' + cate2_item.name + '</option>';
        }
        $('#qd_cate2').html(str);
    });
});


$('#modify_channel_form').submit(function () {
    var qd_1 = validate_field("#qd_cate1", "奇点第一分类必须选择，谢谢！");
    var cate_1 = validate_field("#cate1_select", "第一分类必须选择,谢谢!");
    var flag = qd_1 && cate_1;
    if (!flag) {
        return false;
    }
    $(this).ajaxSubmit(function (data) {
        alert(data.msg);
        history.go(-1);
        location.reload();
    });
    // return false to prevent normal browser submit and page navigation
    return false;
});
function validate_field(field, alerttxt) {
    var value = $(field).val();
    {
        if (value == null || value == "" || value == "0") {
            alert(alerttxt);
            return false
        }
        else {
            return true
        }
    }
}