$("button.delete").click(function(){
  $.get($(this).val(),function(data,status){
    alert(data.msg);
    window.location.reload();
  });
});


$("button.start_schedule").click(function(){
  $.post("/api/schedule",{name:"site",id:$(this).val()},function(data,status){
    alert(data.added);
  });
});

$("button.stop_schedule").click(function(){
  $.ajax(
  {
  url:"/api/schedule",
  type: 'DELETE',
  data:{name:"site",id:$(this).val()},
  success:function(data,status){
  alert(data.removed);
  }

  });
});
