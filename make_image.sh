#!/bin/sh
image_name=$1
path=$2
docker_registry=$3
docker_user=$4
docker_password=$5

cd ${path}
if [ "${docker_user}" != "None" ]; then
  $6 login -u${docker_user} -p${docker_password} ${docker_registry}
fi
if ! $6 build --network=host -t ${image_name} -f $7 .; then
  $6 build --load -t ${image_name} -f $7 .
fi
$6 push ${image_name}
#清理镜像
$6 image prune -a -f --filter until=24h