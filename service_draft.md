Services代码结构草案
---

### update: 2017年6月5日
1. work frame层次指定配置yaml文件，配置中每个微服务写所在路径。
2. 不依赖于文件夹组织结构，不一定在同一文件夹，但微服务组织在一起是推荐方式。
3. 微服务的层次不变
返回的Service字典如下：
```
{
        'service_group': 'services_default',
        'service_pkg':
            {
                'calculate': {
                    'path': '/data/project/mq-service/services_default/sleep_service',
                    'version': 1.0,
                    'services': {
                        'calculate__add': <function add at 0x00000000029C7AC8>,
                        'calculate__minus': <function minus at 0x00000000029C7B38>
                    }
                },
                'time': {
                    'path': '/data/project/mq-service/services_default/time_service',
                    'version': 1.0,
                    'services': {
                        'time__transfer': <function transfer at 0x00000000029C7F28>
                    }
                }
            }
    }
```
### update: 2017年5月27日
1. 服务包整体层次保持不变
2. 每个服务层次，服务自己配置发布哪些函数（使用配置而不是装饰器）服务名为（service_base_name__函数名）
3. work frame层次调用服务包两种方式：1 指定服务包名称（字符串）； 2 import服务包（传包进去，实质也是获取路径）

服务结构：
```
services_default        
|   setting.yaml        #服务包的整体配置，包括：1 micro_service微服务的名字，2 enable哪些下属服务包
|   __init__.py         
|
+---caculate_service
|       setting.yaml    #内层服务的配置，包括：1 service_base_name服务空间名字, 2发布哪些函数，3版本号
|       __init__.py     #服务发布的函数需要在这里定义
|
+---sleep_service
|       setting.yaml
|       __init__.py
|
\---time_service
        setting.yaml
        __init__.py
```
---
### update: 2017年5月26日
1. 整体层次：
- 不同的service包，对应实际的server(服务有自己的命名空间，保证代码隔离).
- 服务包的配置中，1指定关联使用此包的server名称，2需要指定发布哪些服务 3其他配置。
- 在mq_service层import服务包，指定生成service对应的服务包路径（默认指向services）

2. 每个服务层次：
- 发布多个函数服务,在使用装饰器指定发布的函数，服务名为（service_base_name__函数名）
---

### init: 2017年5月25日
1. 整体结构
- mq-service顶层目录下建立services包，每个下级package就是一种服务的代码。
- services下__init__.py初始化时导出所有服务到Services字典中

- key：每个服务配置的发布名称
- value：包含实际运行的函数和其他设置

2. 每个服务的结构
- __init__.py中的run函数为发布的函数
- setting.yaml为配置文件 
>暂时想到了发布名service_name, 版本号version。
    
