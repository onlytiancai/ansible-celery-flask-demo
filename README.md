## 介绍

ansible是一个基于SSH协议的自动化部署工具，但官网提供的例子大多都是在命令行下执行的，
对于python api只提供了很简单的信息，对于批量任务（playbook）的api,官方甚至没有提供
文档。

但是要用ansible实现一套自动化部署系统，是必须要有个界面提供给使用者的, 使用者可以请求
执行一个批量部署任务，并获取任务执行进度和最终状态，在这期间，不能长时间占用web worker
的时间。

所以查了一些资料，最后用flask,celery,ansible来写了个demo

## 执行

    启动redis，作为celery的broker和result backend
    $ service redis start
    启动celery来接受任务处理
    $ celery worker -A app.celery --loglevel=info
    启动flask web app
    $ python app.py
    浏览器里打开http://localhost/play，按界面执行就可以了


## 文件介绍

### hosts.py

使用ansible进行自动化部署，需要先定义Inventory，一般来说Inventory是一个静态文本文件，
里面定义了ansible可管理的主机列表，但是有时候每个用户可管理的机器列表是不一样的，
或者要管理的机器列表经常变化，比如要和公司的CMDB去集成，这就需要用到 Dynamic Inventory

这个脚本是根据环境变量来获取指定的机器分组, 具体实现可从数据里读取可管理的机器列表。

参考链接：

- [Dynamic Inventory](http://docs.ansible.com/intro_dynamic_inventory.html)
- [Developing Dynamic Inventory Sources](http://docs.ansible.com/developing_inventory.html)

### test.yaml

这里定义了一个ansible playbook，就是一个部署任务，安装nginx，并启动nginx。
可以用如下代码执行该playbook

    $ ansible-playbook -i hosts.py test.yaml

参考链接：

- [Playbooks](http://docs.ansible.com/playbooks.html)

### test_playbook.py

该文件是利用了ansible的python api，去以编程的方式，而不是命令行的方式去执行一个playbook。
可以直接用如下命令去执行

    $ python test_playbook.py

注意这里的`PlaybookRunnerCallbacks`和`PlaybookCallbacks`两个类，是我自己定义过的，主要目的
是在每个task执行开始，执行成功或失败时，调用`update_state`去更新celery任务状态, 每个类的
`celery_taski`成员是一个celery的task，在构造函数里传入的。

参考链接

- [celery custom states](http://docs.celeryproject.org/en/latest/userguide/tasks.html#custom-states)
- [ansible python api](http://docs.ansible.com/developing_api.html)
- [Running ansible-playbook using Python API](http://stackoverflow.com/questions/27590039/running-ansible-playbook-using-python-api)

### app.py

这是一个flask web app，其中`/play/longtask`是发起一个异步任务，也就是执行playbook，该请求会返回
轮询检测任务执行状态的url，包含了该异步任务的ID, 如`/play/status/111` 。

参考链接

- [Using Celery with Flask](http://blog.miguelgrinberg.com/post/using-celery-with-flask)

### templates/index.html

在界面上点击按钮发起执行playbook的请求，然后自动轮询获取任务执行状态并显示。在整个任务执行过程中
web应用不会被hang住，真正的任务执行是celery执行的。

## 参考链接：

- [自动化运维工具之ansible](http://guoting.blog.51cto.com/8886857/1553446)
