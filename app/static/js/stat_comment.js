var  pie_view = echarts.init(document.getElementById('comment_pie'))
pie_option = {
    tooltip : {
        trigger: 'item',
        formatter: "{a} <br/>{b} : {c} ({d}%)"
    },
    legend: {
        orient: 'vertical',
        left: 'left',
        data:['来自微博','来自网易','来自快报','来自微信']
    },
    toolbox: {
        show : true,
        feature : {
            mark : {show: true},
            dataView : {show: true, readOnly: false},
            magicType : {
                show: true,
                type: ['pie', 'funnel']
            },
            restore : {show: true},
            saveAsImage : {show: true}
        }
    },
    calculable : true,
    series : [

        {
            name:'评论来源情况',
            type:'pie',
            radius : [30, 110],
//            roseType : 'area',
            data:[
//                {value:10, name:'无评论新闻'},
                {value:5, name:'来自微博'},
                {value:15, name:'来自网易'},
                {value:25, name:'来自快报'},
                {value:20, name:'来自微信'},

            ]
        }
    ]
};

var bar_view = echarts.init(document.getElementById('week_stat'))

bar_option = {
    tooltip : {
        trigger: 'axis',
        axisPointer : {            // 坐标轴指示器，坐标轴触发有效
            type : 'shadow'        // 默认为直线，可选为：'line' | 'shadow'
        }
    },
    legend: {
        data:['有评论新闻','微博评论','网易评论','微信评论','快报评论']
    },
        toolbox: {
        show : true,
        feature : {
            mark : {show: true},
            dataView : {show: true, readOnly: false},
            restore : {show: true},
            saveAsImage : {show: true}
        }
    },
    grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
    },
    xAxis : [
        {
            type : 'category',
            data : []
        }
    ],
    yAxis : [
        {
            type : 'value'
        }
    ],
    series : [

        {
            name:'有评论新闻',
            type:'bar',
            data:[],
        },
        {
            name:'微博评论',
            type:'bar',
            stack: '有评论新闻',
            data:[]
        },
        {
            name:'网易评论',
            type:'bar',
            stack: '有评论新闻',
            data:[]
        },
        {
            name:'微信评论',
            type:'bar',
            stack: '有评论新闻',
            data:[]
        },
        {
            name:'快报评论',
            type:'bar',
            stack: '有评论新闻',
            data:[]
        }
    ]
};




function stat(from_h=24,to_h=0){
    pie_view.showLoading();
    bar_view.showLoading();

    $.ajax({
         type : "post",
         async : true,
         url : "stat",
         data : {from:from_h,to:to_h},
         dataType : "json",
         success : function(result) {
             if (result) {
                    $("#total_news").text(result.total_news)
                    $("#total_news_c").text(result.total_news_c)
                    $("#weibo_scan").text(result.scan_count)
                    $("#weibo_get").text(result.comment_result.weibo.num)
                    datas = []

//                    datas.push({value:result.total_news-result.total_news_c, name:'无评论新闻'})
                    datas.push({value:result.comment_result.weibo.num, name:'来自微博'})
                    datas.push({value:result.comment_result["163"].num, name:'来自网易'})
                    datas.push({value:result.comment_result.kuaibao.num, name:'来自快报'})
                    datas.push({value:result.comment_result.wechat.num, name:'来自微信'})
                    pie_option.series[0].data=datas
                    pie_view.setOption(pie_option);
                    pie_view.hideLoading();    //隐藏加载动画
                    try{
                        c = result.channels
                        count = 0
                        for (var i in c){count++}
                        for (i=1;i<=count ;i++)
                        {

                        bar_option.xAxis[0].data.push(c[i]["cname"])
                        bar_option.series[0].data.push(c[i].comment.total)
                        bar_option.series[1].data.push(c[i].comment.weibo)
                        bar_option.series[2].data.push(c[i].comment["163"])
                        bar_option.series[3].data.push(c[i].comment.wechat)
                        bar_option.series[4].data.push(c[i].comment.kuaibao)
                        bar_view.hideLoading();

                    }
                    }
                    catch(err){
                        alert(err);
                    }
                    bar_view.setOption(bar_option)

                    try{
                        c_r = result.comment_result;
                        var oris = ["max","min","median","mod","avg","variance"]
                        for(var i=1;i<7;i++)
                        {
                            $("#weibo_stat").children().eq(i).text(c_r.weibo[oris[i-1]])
                            $("#kuaibao_stat").children().eq(i).text(c_r.kuaibao[oris[i-1]])
                            $("#wechat_stat").children().eq(i).text(c_r.wechat[oris[i-1]])
                            $("#netease_stat").children().eq(i).text(c_r["163"][oris[i-1]])
                        }

                    }

                    catch(err){
                        alert(err);
                    }


             }

        },
         error : function(errorMsg) {
         alert("检索失败，通知 Tacey Wong 检查");
         pie_view.hideLoading();
         bar_view.hideLoading();
         }
    })
}


$("#search_button").click(function()
{
    text = $("#search").val()
    text = text.replace(/(^\s*)|(\s*$)/g, "")
    text_array = text.split("-")
    if (text_array.length !=2){
        alert("请输入正确格式!如：查询过去24小时到过去十二小时：24-12");
    }
    else{
    from_h = text_array[0];
    to_h = text_array[1];
    stat(from_h,to_h)}

})

stat()

