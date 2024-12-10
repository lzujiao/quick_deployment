#!/bin/bash

# 检查 conda 是否安装
if ! command -v conda &> /dev/null
then
    echo "conda not found, please install conda first."
    exit 1
fi

# 检查 agent_app_config 环境是否存在
if conda info --envs | grep -q 'agent_app_config\s*.*\s*$'; then
    echo "agent_app_config environment already exists."
else
    # 创建 ttt 环境
    echo "Creating agent_app_config environment..."
    conda create -n agent_app_config python=3.10 -y
    activate_cmd=$(command -v activate)
    source ${activate_cmd} agent_app_config
    pip install pyyaml
fi

activate_cmd=$(command -v activate)
source ${activate_cmd} agent_app_config


rm -rf ./agent_app_config
git clone  http://ig.git
cd ./agent_app_config

python run.py $1


