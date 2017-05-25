Services代码结构草案
---
### 1 整体结构
mq-service顶层目录下建立services包，每个下级package就是一种服务的代码。

services下__init__.py初始化时导出所有服务到Services字典中

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

### 2 每个服务的结构
1. __init__.py中的run函数为发布的函数
2. setting.yaml为配置文件

>暂时想到了发布名service_name, 版本号version。
    
