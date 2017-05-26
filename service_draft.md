Services代码结构草案
---
### update: 2017年5月26日
1. 整体层次：
- 不同的service包，对应实际的server(服务有自己的命名空间，保证代码隔离).
- 服务包的配置中，1指定关联使用此包的server名称，2需要指定发布哪些服务 3其他配置。
- 在mq_service层import服务包，指定生成service对应的服务包路径（默认指向services）

2. 每个服务层次：
- 发布多个函数服务,在使用装饰器指定发布的函数，服务名为（service_base_name__函数名）

最后导出的service格式
```
{'service_group': 's1',
 'enable': ['caculate_service', 'time_service'],
 'log_path': None,
 'services': {'calculate__add': {'function': <function run at 0x0000000002EEEDD8>,
                            'service_base_name': 'calculate',
                            'service_pkg': 'caculate_service',
                            'version': 1.0},
              'calculate__divide': {'function': <function run at 0x0000000002EEEDD1>,
                            'service_base_name': 'calculate',
                            'service_pkg': 'caculate_service',
                            'version': 1.0},
              'time__add': {'function': <function run at 0x0000000002EFD128>,
                           'service_base_name': 'time',
                           'service_pkg': 'time_service',
                           'version': 1.0}}}
```

---

### init: 2017年5月25日
1. 整体结构
- mq-service顶层目录下建立services包，每个下级package就是一种服务的代码。
- services下__init__.py初始化时导出所有服务到Services字典中

字典结构如下：
```
{'add': {
         'function': <function run at 0x0000000002959128>,
         'service_name': 'add',
         'version': 1.0},
 'sleep': {'function': <function sleep_function at 0x00000000029593C8>,
           'service_name': 'sleep',
           'version': 1.0}
}
```
- key：每个服务配置的发布名称
- value：包含实际运行的函数和其他设置

2. 每个服务的结构
- __init__.py中的run函数为发布的函数
- setting.yaml为配置文件 
>暂时想到了发布名service_name, 版本号version。
    
