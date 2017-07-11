
kael-web
==========================
kael-web是基于kael命令的web界面封装，方便地图形化管理kael系统。

目前后端实现以下api：

:远程调用: '/api/v1/<namespace>/rpc/<fun_name>'
:安装更新重启: '/api/v1/<namespace>/operation'
:状态: '/api/v1/<namespace>/status'
:拉取topic信息: '/api/v1/<namespace>/pull/<topic>'


kael-web 命令
----------

安装kael成功之后，系统中出现kael-web，该命令为快速启动web服务。

首次使用可以键入: kael-web --help

有开发/生产两种模式：

:开发模式:
    kael-web dev --help，

两个参数：端口(默认5000), 消息队列地址

Example:::

      $ kael-web dev
      $ kael-web dev -p 5000 --kael_amqp 'amqp://user:****@localhost:5672/api'


:生产模式: kael-web run

生产模式为daemon模式，有start|stop|restart三种命令

参数:::

  -p, --port INTEGER              Port, default 5000
  --pid TEXT                      Pid file
  -c, --command [start|stop|restart]
                                  Command, [start | stop | restart]
  -a, --kael_amqp TEXT            AMQP_URI, default in flask setting

Example usage:

      $ kael-web run --command start --kael_amqp 'amqp://user:****@localhost:5672/api'


前端仍在开发中，敬请期待...

(未完待续)
