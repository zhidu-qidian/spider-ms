$("button.delete").click(function(){
  $.get($(this).val(),function(data,status){
    alert(data.msg);
    window.location.reload();
  });
});


$("button.schedule_true").click(function(){
  $.post("/api/set_schedule",{action:"set_true",cid:$(this).val()},function(data,status){
      alert(data.msg);
      if (data.msg=="success"){
      dom_select = "#sch_"+data.cid;
      dom_text = "True" ? data.result : "False" ;
      $(dom_select).text(dom_text);}
  });
});


$("button.schedule_false").click(function(){
  $.post("/api/set_schedule",{action:"set_false",cid:$(this).val()},function(data,status){
      alert(data.msg);
      if (data.msg=="success"){
      dom_select = "#sch_"+data.cid;
      dom_text = "True" ? data.result : "False" ;
      $(dom_select).text(dom_text);}
  });
});



$("button.start_schedule").click(function(){
  $.post("/api/schedule",{name:"channel",id:$(this).val()},function(data,status){
    alert(data.added);
  });
});

$("button.stop_schedule").click(function(){
  $.ajax(
  {
  url:"/api/schedule",
  type: 'DELETE',
  data:{name:"channel",id:$(this).val()},
  success:function(data,status){
  alert(data.removed);
  }

  });
});


function ask_count()
 {
       $("tr.channel_item").each(function(){
       try{
           $.ajax({
               type: "GET",
               url: "/api/get_channel_data_count",
               data:{cid:$(this).attr("id").split("_")[1]},
               dataType: "json",
               success: function(data) {
               id = "#"+data.cid;
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


function ask_last()
 {
       $("tr.channel_item").each(function(){
       try{
           $.ajax({
               type: "GET",
               url: "/api/get_last_db_time",
               data:{cid:$(this).attr("id").split("_")[1]},
               dataType: "json",
               success: function(data) {
               id = "#"+data.cid;
               last_time = data.last_time
                  $(id).text(last_time);
               }
           });
           }
           catch(err)
           {;}
           }
           )

   }

ask_count();
ask_last()
window.setInterval(ask_count,600000);
window.setInterval(ask_last,600000);



