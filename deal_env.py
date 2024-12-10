import optparse
import os
import yaml

parser = optparse.OptionParser()
parser.add_option("-s", dest="service_name", help="服务名称")
(options, args) = parser.parse_args()


def alter(file, old_str, new_str):
    """
    替换文件中的字符串
    :param file:文件名
    :param old_str:就字符串
    :param new_str:新字符串
    :return:
    """
    file_data = ""
    with open(file, "r", encoding="utf-8") as f_alter:
        for line in f_alter:
            if old_str in line:
                line = line.replace(old_str, new_str)
            file_data += line
    with open(file, "w", encoding="utf-8") as f_alter:
        f_alter.write(file_data)


parent_directory_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_filename = f"{parent_directory_path}/script/env.yaml"
config_filename = f"{os.path.dirname(__file__)}/app_config/{options.service_name}/configmap_file.yaml"
with open(env_filename, encoding='utf-8') as f:
    config = yaml.safe_load(f)
config_env = config["{cn}"]["env"]
config_default = config.get("default_envs", None)
newline = os.linesep
config_list = [f'{key}: "{value}"' if type(value) is int else f'{key}: {value}' for key, value in config_env.items()]
if config_default is not None:
    [config_list.append(f'{key}: "{value}"') if type(value) is int else config_list.append(f'{key}: {value}') for key, value
     in config_default.items()]
config = f'{newline}  '.join(config_list)
print(config)
alter(config_filename, '#config', config)
