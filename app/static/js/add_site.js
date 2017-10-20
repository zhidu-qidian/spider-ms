
    $('#add_site_form').submit(function() {
    $(this).ajaxSubmit(function(data){alert(data.msg);$("button[type='reset']").trigger("click");});
    // return false to prevent normal browser submit and page navigation
    return false;
});

