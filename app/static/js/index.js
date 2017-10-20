var form_line = echarts.init(document.getElementById('main'));

        // 指定图表的配置项和数据
       var form_option = {

    tooltip: {
        trigger: 'axis'
    },
    legend: {
        data:['NEWS','JOKE','VIDEO','ATLAS','PICTURE']
    },
    grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
    },
    toolbox: {
        feature: {
            saveAsImage: {}
        }
    },
    xAxis: {
        type: 'category',
        boundaryGap: false,
        data: []
    },
    yAxis: {
        type: 'value'
    },
    series: [
        {
            name:'NEWS',
            type:'line',
            data:[]
        },
        {
            name:'JOKE',
            type:'line',
            data:[]
        },
        {
            name:'VIDEO',
            type:'line',
            data:[]
        },
        {
            name:'ATLAS',
            type:'line',
            data:[]
        },
        {
            name:'PICTURE',
            type:'line',
            data:[]
        }

    ]
};


function get_week_stat(){
    form_line.showLoading();
    $.ajax({
         type : "get",
         async : true,
         url : "/api/get_week_stat/",
         data : {},
         dataType : "json",
         success : function(result) {
             if (result) {

                    try{
                        result_data = result.data

                        for (var i in result_data){

                        form_option.xAxis.data.push(result_data[i].day)
                        form_option.series[0].data.push(result_data[i].data.news)
                        form_option.series[1].data.push(result_data[i].data.joke)
                        form_option.series[2].data.push(result_data[i].data.video)
                        form_option.series[3].data.push(result_data[i].data.atlas)
                        form_option.series[4].data.push(result_data[i].data.picture)
                        }
                        form_line.setOption(form_option);
                        form_line.hideLoading();

                    }

                    catch(err){
                        alert(err);
                    }



             }

        },
         error : function(errorMsg) {
         alert("获取数据失败，通知 Tacey Wong 检查");
         form_line.hideLoading();
         }
    })
}

get_week_stat()

function ask_count()
 {
       $("span.site_item").each(function(){
       try{
           $.ajax({
               type: "GET",
               url: "/api/get_site_data_count",
               data:{sid:$(this).attr("id").split("_")[1]},
               dataType: "json",
               success: function(data) {
               id = "#"+data.sid;
               count = data.count;
                  $(id).text(count);
               }
           });
           }
           catch(err)
           {;}
           }
           )

   }

ask_count()



