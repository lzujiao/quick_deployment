1、部署应用的服务器软硬件环境要求：
 （1）对依赖的中间件/服务网络通，如：镜像仓库、redis、mysql、nacos等
 （2）已安装conda
 （3）已安装git
 （4）部署软件：
  a、对于k8s方式部署，需要有k8s环境，能执行kubectl相关命令
  b、对于docker方式部署，需要有docker环境，能执行docker相关命令

```conda
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm -rf ~/miniconda3/miniconda.sh
~/miniconda3/bin/conda init bash
~/miniconda3/bin/conda init zsh
source ~/.bashrc
```



2、工具使用方式
   登录服务器，在/data/workspace目录下，执行以下命令：
   ```
wget http://xxxxxosss.cn/script/deploy_agent_app.sh && sed -i -e 's/\r$//' deploy_agent_app.sh && chmod 744 deploy_agent_app.sh  && ./deploy_agent_app.sh "-s {应用名称} -e {环境名称} -b  {代码分支}" && rm -rf deploy_agent_app.sh
```
入口脚本放oss上，deploy_agent_app.sh的逻辑：
（1）检查conda环境是否存在并激活环境
（2）下载 git仓库 agent_app_config
（3）执行仓库中 run.sh脚本，逻辑如下：
  a、从配置中根据应用名称，下载应用仓库，并切换分支
  b、使用dockerfile打包镜像 
  c、根据入参的{应用名称}+{环境名称}，读取 env.yaml
  d、根据 env.yaml中的配置进行打包镜像，并部署

3、应用自己的配置
应用根目录 /script 目录下，仅包含Dockerfile，env.yaml
default_envs填写每个环境下的公共env
deploy_type填写部署方式，有k8s和docker
deploy_param填写部署参数，如memory、worker数、k8s部署下的namespace等
docker_default填写选择的镜像
```
default_envs:
  OPENAI_API_KEY: ***
dev:
  deploy_type: k8s
  env:
    ENVIRONMENT: dev
testcom:
  deploy_type: docker
  deploy_param:
    memory: 16
  env:
    ENVIRONMENT: testcom
testcn:
  deploy_type: k8s
  docker_default: **
  deploy_param:
    memory: 16
    worker: 16
    namespace: test
  env:
    ENVIRONMENT: test
```

4、应用配置使用公共git统一管理，避免应用的配置在各个分支上不同步导致的问题
      新建git仓库 agent_app_config
run.sh
global_config.json
app_config
-core
--deployment.yaml
--istio.yaml
--svc.yaml
-plugin
--deployment.yaml
--istio.yaml
--svc.yaml
```
"code_repo": {
    "core": {
        "dir": "**",
        "git_url": "**"
    },
    "plugin": {
        "dir": "**",
        "git_url": "**"
    }
}
"registry":{
    "habor": {
        "docker_registry": "**",
        "docker_user": "**",
        "docker_password": "**"
    },
    "registry": {
        "docker_registry": "**",
        "docker_user": "**",
        "docker_password": "**",
        "image_secret": "**"
    }  
  }
```
默认约定：
1、容器名称docker_name = {app_name}_{env_name}
5、使用
5.1 脚本参数介绍
部署参数 
参数	解释	实例	是否必填
-s	服务名称	-s core	是
-e	环境名称	-e testcn	是
-b	分支名称	-b develop_deploy_0613	是
-d	部署	-d	否，默认是部署
-p	不部署，只打包	-p	否，默认是部署，只需要打包时需指定参数
-i	镜像名称	-i **.aliyuncs.com/**/**:20240712134054	否，默认是重新打镜像，如果有现成镜像，需指定参数
-r	k8s部署的pod数	-r 3	否，默认为1
5.2 没有oss时使用
因为没有oss，部署脚本deploy_agent_app.sh需要自己拷贝到机器上（在agent_app_config代码仓库里）

![image](https://github.com/user-attachments/assets/efd2fb0a-a4d2-46f7-af69-d6c88ea5b6e5)

5.3 有oss使用
部署示例
运行如下脚本
```
wget  https://**.oss-cn-hongkong.aliyuncs.com/script/deploy_agent_app.sh &&sed -i -e 's/\r$//' deploy_agent_app.sh && chmod 744 deploy_agent_app.sh  && ./deploy_agent_app.sh "-s core -e devcn -b develop_deploy_0808" && rm -rf deploy_agent_app.sh
```
打包示例：
打包不依赖于机器，所以可以在任意机器上打包任意环境镜像，打包后，可以查看打包后的镜像名称，以及镜像部署参考命令，k8s环境的部署脚本可以按照目录copy使用

```
wget  https://**.oss-cn-hongkong.aliyuncs.com/script/deploy_agent_app.sh &&sed -i -e 's/\r$//' deploy_agent_app.sh && chmod 744 deploy_agent_app.sh  && ./deploy_agent_app.sh "-s structure -e devcom -b develop_deploy_0808 -p" && rm -rf deploy_agent_app.sh
```

5.4 部署分支查看
docker环境
```
docker inspect structure_devcom|grep branch
```
k8s环境
```
kubectl -n geogpt-dev get deployment --show-labels |grep branch
```
6、添加新镜像仓库
在agent_app_config仓库的global_config.json文件中的registry添加新的仓库信息，image_secret为k8s环境中，仓库对应的secret名称，project为推镜像的第一后缀名，如hu.aliyuncs.com/dd/plugin_testcn:20240712134054，就为dd
7、添加新环境
在服务的env.yaml中添加自己的服务信息，示例如下，其中
deploy_type:  必填 k8s、docker
  docker_default: 必填 ，与agent_app_config的global_config.json中registry名称对应
  deploy_param:
    memory:  必填 
    worker:  必填 
    namespace:  deploy_type为k8s时必填

8、在部署脚本中添加新应用
1）参考3、7，在应用根目录 /script 目录下添加Dockerfile，env.yaml
2) 在agent_app_config的global_config.json中的service_msg添加自己的服务信息
3）k8s环境部署需要在agent_app_config的app_config中添加自己服务的yaml

9、dockerfile与基础镜像
9.1 基础镜像
将dockerfile中不容易变动且安装费时的部分放入到基础镜像当中，如apt-get install过程，或者pip过程中需要超过20s的部分，尽量保持基础镜像很小， 不要把过多pip的过程放入基础镜像中，因为基础镜像大了之后，拉基础镜像的时间也会变长很多，不划算  
9.2 dockerfile缓存
为了更多的使用docker build缓存，提升打镜像时间，把相对固定的步骤放到最前面，示例：
1）我有一个包要安装，但是他的安装版本经常变动，要放在后面
2）我有一个copy过程，copy的文件是有可能变动的（如代码），要放在后面
9.3 dockerfile构建加速
安装pip包时使用国内镜像源
```
RUN pip install uwsgidecorators -i https://pypi.tuna.tsinghua.edu.cn/simple
```
apt-get install的时候使用国内镜像
```
RUN sed -i 's/archive.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y pandoc latexml
```
9.4 dockerfile瘦身
如果安装一个包时，我知道他的安装位置，并且可以通过copy安装位置，实现安装迁移（如，pip包安装的东西都放在/usr/local目录中，我在一个全新的机器上，把之前机器的/usr/local目录copy过来，python代码运行时就可以正常使用这些pip包），可以进行瘦身
通过多段构建进行瘦身：将第一段的构建结果copy到第二段直接使用
1）builder就是我的第一阶段构建
2）第二阶段构建时，使用了基础镜像，COPY --from=builder /usr/local /usr/local就是在使用第一阶段构建得到的结果
```
FROM python:3.10-slim-buster as builder
RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
。。。
RUN pip install beautifulsoup4 -i https://pypi.tuna.tsinghua.edu.cn/simple




FROM **.aliyuncs.com/**/**:20240725165446
USER root
RUN mkdir /app/ \
    && mkdir /app/**/
WORKDIR /app/**
RUN echo 'Asia/Shanghai' >/etc/timezone
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
COPY --from=builder /usr/local /usr/local
COPY ./ /app/dde-agent-plugins-python/
ENV PYTHONPATH=/app/**:$PYTHONPATH

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9487", "--workers", "16"]
EXPOSE 9487
```
