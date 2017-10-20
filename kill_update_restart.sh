#!/usr/bin/env bash

#Step1: git pull 更新代码
#Step2: kill uwsgi进程
#Step3: 检查老进程是否还存在，若不存在，重启

proc_name="uwsgi"
log_name="./code_update.log"
pid=0

proc_num()
{
    num=`ps -ef | grep $proc_name | grep -v grep | wc -l`
    return $num
}

proc_id()
{
    pid=`ps -ef | grep $proc_name | grep -v grep | awk '{print $2}'`
}

kill_proc()
{
    `ps -ef | grep $proc_name | grep -v grep | awk '{print "kill " $2}'` | sh
}
git pull

kill_proc

while (true)
do
    proc_num
    number=$?
    if [ $number -eq 0 ]
    then
        uwsgi uwsgi.ini
        echo 'Restart:' >> $log_name
        proc_id
	    echo ${pid}:`date` >>  $log_name
        break
    fi
    sleep 1s
done
