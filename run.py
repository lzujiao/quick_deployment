import subprocess
import os
import time

import yaml
import optparse
import json

parser = optparse.OptionParser()
parser.add_option("-s", dest="service_name", help="服务名称")
parser.add_option("-e", dest="env_name", help="环境名称")
parser.add_option("-b", dest="branch", default="develop_deploy_0808", help="分支名称")
parser.add_option("-d", dest="deploy", action="store_true", default=True, help="部署")
parser.add_option("-p", dest="deploy", action="store_false", help="不部署，只打包")
parser.add_option("-i", dest="image_name", default="", help="镜像名称")
parser.add_option("-r", dest="repeat", default="1", help="k8s部署的pod数")
(options, args) = parser.parse_args()

with open("global_config.json", 'r') as f:
    content = f.read()
    global_config = json.loads(content)

docker_base_dir = os.path.dirname(__file__)
newline = os.linesep


def run_cmd(cmd):
    print(f"cmd: {cmd}")
    subprocess.run(cmd, shell=True)


def alter(file, old_str_list, new_str_list):
    """
    替换文件中的字符串
    :param file:文件名
    :param old_str_list:就字符串列表
    :param new_str_list:新字符串列表
    :return:
    """
    file_data = ""
    with open(file, "r", encoding="utf-8") as f_alter:
        for line in f_alter:
            for i, old_str in enumerate(old_str_list):
                if old_str in line:
                    line = line.replace(old_str, str(new_str_list[i]))
            file_data += line
    with open(file, "w", encoding="utf-8") as f_alter:
        f_alter.write(file_data)


def deal_env_for_k8s(_env, env_default):
    config_list = [f'{key}: "{value}"' if type(value) is int else f'{key}: {value}' for key, value in
                   _env.items()]
    if env_default is not None:
        [config_list.append(f'{key}: "{value}"') if type(value) is int else config_list.append(f'{key}: {value}') for
         key, value in env_default.items()]
    _config = f'{newline}  '.join(config_list)
    print(_config)
    return _config


def deal_env_for_docker(_env, env_default):
    config_list = [f'-e {key}={value}' for key, value in _env.items()]
    if env_default is not None:
        [config_list.append(f'-e {key}={value}') for key, value in env_default.items()]
    _config = " ".join(config_list)
    print(_config)
    return _config


service = global_config["service_msg"][options.service_name]
env = options.env_name
docker_name = f"{options.service_name}_{env}"
branch = options.branch
image_name = options.image_name

# clone代码
run_cmd(f"rm -rf {docker_base_dir}/{service['dir']}/")
run_cmd(f"cd {docker_base_dir} && git clone -b {branch} {service['git_url']}")

# 获取配置信息
env_filename = f"{docker_base_dir}/{service['dir']}/script/env.yaml"
with open(env_filename, encoding='utf-8') as f:
    env_configs = yaml.safe_load(f)
print(env)
print(env_configs)
env_config = env_configs[env]
worker = env_config["deploy_param"]["worker"]
memory = env_config["deploy_param"]["memory"]
docker_default = global_config["registry"][env_config["docker_default"]]
docker_script_path = service.get("docker_script_path", "./script/Dockerfile_jenkins")
build_dir = f"{docker_base_dir}/{service['dir']}"
if options.service_name == "chatbot":
    build_dir = os.path.dirname(docker_base_dir)
# docker镜像打包
if image_name == "":
    tag = time.strftime('%Y%m%d%H%M%S', time.localtime())
    image_name = f"{docker_default['docker_registry']}/{docker_default['project']}/{docker_name}:{tag}"
    run_cmd(
        f"sh -x {docker_base_dir}/make_image.sh {image_name} {build_dir} {docker_default['docker_registry']} {docker_default['docker_user']} {docker_default['docker_password']} docker {docker_script_path}")
    print(f"image_name: {image_name}")

# 部署

if env_config["deploy_type"] == "k8s":
    # 脚本内容替换
    configmap_file = f"{docker_base_dir}/app_config/{options.service_name}/configmap_file.yaml"
    deployment_file = f"{docker_base_dir}/app_config/{options.service_name}/deployment.yaml"
    namespace = env_config["deploy_param"]["namespace"]
    config = deal_env_for_k8s(env_config["env"], env_configs.get("default_envs", None))
    alter(configmap_file, ["#namespace", "#config"], [namespace, config])
    alter(deployment_file, ["#namespace", "#workers", "#memory", "#image_secret", "#image_name", "#branch", "#repeat"],
          [namespace, worker, f"{memory}Gi", docker_default["image_secret"], image_name, branch, options.repeat])
    if options.deploy:
        run_cmd(f"kubectl apply -f {configmap_file}")
        run_cmd(f"kubectl apply -f {deployment_file}")
        print("部署完毕")
    else:
        print("打包镜像完毕")
        print(f"""镜像部署命令参考：
                  kubectl apply -f {configmap_file}
                  kubectl apply -f {deployment_file}""")

else:
    config = deal_env_for_docker(env_config["env"], env_configs.get("default_envs", None))
    extra_docker_command = env_config.get("extra_docker_command", "")
    _run_cmd = f"docker run -itd --name {docker_name} --network=host   --memory {memory}G  {config} -l branch={branch} {extra_docker_command} {image_name} uvicorn {service['main_position']}  --host=0.0.0.0 --port={service['port']}"
    if worker != -1:
        _run_cmd += f" --workers={worker}"
    if options.deploy:
        run_cmd(f"docker stop {docker_name}")
        run_cmd(f"docker rm {docker_name}")
        run_cmd(_run_cmd)
        print("部署完毕")
    else:
        print("打包镜像完毕")
        print(f"""镜像部署命令参考：
                  {_run_cmd}""")
