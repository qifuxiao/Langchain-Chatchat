docker login  registry.cn-chengdu.aliyuncs.com -u 867225266@qq.com -p Js147258
docker build --network=host   -t registry.cn-chengdu.aliyuncs.com/llm-studio/chatchat:20250303.v3  -f Dockerfile . 

docker push registry.cn-chengdu.aliyuncs.com/llm-studio/chatchat:20250303.v3