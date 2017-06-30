*************************
使用手册
*************************

work frame框架
==========================
kael work frame是服务与代码管理框架，建立在micro_service层之上，能够方便地管理使用微服务与定时任务。

框架服务端
-----------------------
启动frame需要三个配置项：运行空间、消息队列地址、框架配置文件绝对路径

:运行空间: name，在同空间运行的服务能够互相发现。手动配置优先，为None时指定为配置文件中的service_group值。
:消息队列地址: auri，服务运行依靠的rabbitmq消息队列地址。
:框架配置文件绝对路径: service_group_conf，框架通过此配置文件载入需要启动的微服务与定时任务。


Example::

    from kael.work_frame import WORK_FRAME
    AMQ_URI = 'amqp://user:****@127.0.0.1:5672/api' # rabbitmq 地址
    namespace = 'test' # 运行空间
    conf_dir = '/data/frame_pkg_setting.yaml'
    server = WORK_FRAME(name=namespace, auri=AMQ_URI, service_group_conf=conf_dir)
    server.frame_start()


框架配置文件格式
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

配置文件为yaml格式，两部分构成：服务包空间名、服务包路径。

:服务包空间名: service_group，框架初始化时若没有指定name，则取此值作为运行空间名。
:服务包路径: path，列表，微服务包及定时任务包所在的路径。为绝对路径或相对路径（相对框架配置文件service_group_conf）

Example::

    service_group: services_default
    path:
      - ./caculate_service
      - /data/time_service
      - ./task1_crontab

接下来进入最内层服务包与定时任务包文件夹中，一窥究竟


服务包与定时任务包
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

对于服务和定时任务包，包配置的内容不同，但是结构一致。在包载入时，读取包中的setting.yaml获取报信息

文件夹结构::

    /calculate_service
    ├── __init__.py
    ├── setting.yaml
    └── ...


1. 服务包

    配置文件setting.yaml,包含四部分：类型、服务基名、版本号和发布的函数。

    Example::

        type: service
        service_base_name: calculate
        version: 1.0
        publish:
         - add
         - minus

    :type: 对于服务包，类型为'service'。
    :version: 版本号标志此包代码的版本，用于升级/安装代码，支持指定版本号升级。
    :service_base_name: 服务包的基名，与发布函数共同构成最终发布的微服务名。
    :publish: 服务包内发布的函数名，函数定义在包的*__init__.py*文件中。

    微服务名=包基名__发布函数名，上例中结构发布的微服务分别为：
    calculate__add, calculate__minus


2. 定时任务包

    同一个定时任务部署在各台机器上，同时间只有一台机器激活定时任务，其他机器不执行定时任务。
    配置文件setting.yaml,包含四部分：类型、定时任务名、版本号和发布的定时任务。

    Example::

        type: crontab
        crontab_name: print
        version: 1.0
        publish:
           - ['* * * * *', write.py]
           - ['*/2 * * * *', cat word.txt >> log.txt]

    :type: 对于定时任务包，类型为'crontab'。
    :version: 版本号标志此包代码的版本，用于升级/安装代码，支持指定版本号升级。
    :crontab_name: 定时任务包名。
    :publish: 该包发布的所有定时任务。

    publish中每个任务为两元素的列表，第一个内容为定时任务执行时间，第二个为执行的指令。

    执行的指令支持两种写法：
    - python文件可直接指定文件名称（相对路径为文件夹路径）
    - 也可写正常linux命令


框架客户端
-----------------

客户端不需要启动服务，所以配置运行空间name和消息队列地址auri即可

Example::

        from kael.work_frame import WORK_FRAME
        AMQ_URI = 'amqp://user:****@127.0.0.1:5672/api' # rabbitmq 地址
        namespace = 'test' # 运行空间
        client = WORK_FRAME(name=namespace, auri=AMQ_URI)

使用微服务：

直接调用微服务名称即可，如上面发布的微服务calculate__add.

::

    result = client.calculate__add(1,2)

框架微服务操作
^^^^^^^^^^^^^^^^^^^^^^^^^

RPC COMMAND 命令

在客户端调用command函数，第一个参数为rpc执行的函数名,返回id。函数在服务端执行并返回结果

::

        r = client.command(function, **kwargs) # 返回消息id
        result = client.get_response(r, timeout=5) # 获取结果

获取服务/定时任务版本 状态

::

        # 获取最新版本
        client.get_last_version(service='calculate', pkg_type='service')
        client.get_last_version(pkg_type='crontab')

        # 获取所有版本
        client.command("_get_pkg_version", pkg_type='service')
        client.command("_get_pkg_version", pkg_type='crontab')

        # 获取定时任务状态
        client.get_all_crontab_status(crontab=None)

更新、安装操作

::

        client.update_service(pkg_name, **kwargs)
        client.update_crontab(pkg_name, **kwargs)
        client.install_service(pkg_name, install_path, **kwargs)
        client.install_crontab(pkg_name, install_path, **kwargs)

还有可选参数

version：指定版本，默认为最高版本

id: 指定机器执行

not_id: list, 不执行的机器


重启

::

        client.command("_restart_service")
        client.command("_restart_crontab")

