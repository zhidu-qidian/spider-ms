$('#check_parse_form').submit(function() {
    $(this).ajaxSubmit(function(data){
    var format = function () {
            var options = {
                dom: '#parse_result',
                quoteKeys: true,
                tabSize: 2,
            };
            window.jf = new JsonFormater(options);
            jf.doFormat(data);
        };
    format();

    });
    // return false to prevent normal browser submit and page navigation
    return false;
});


