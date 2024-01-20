import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.cvm.v20170312 import cvm_client, models
from public_method import load_config
import logging

config = load_config('config.yaml')
logger = logging.getLogger(__name__)


def get_cvm_info():
    try:
        # 实例化一个认证对象，入参需要传入腾讯云账户 SecretId 和 SecretKey，此处还需注意密钥对的保密
        # 代码泄露可能会导致 SecretId 和 SecretKey 泄露，并威胁账号下所有资源的安全性。以下代码示例仅供参考，建议采用更安全的方式来使用密钥，请参见：https://cloud.tencent.com/document/product/1278/85305
        # 密钥可前往官网控制台 https://console.cloud.tencent.com/cam/capi 进行获取
        cred = credential.Credential(config['AK'], config['SK'])
        # 实例化一个http选项，可选的，没有特殊需求可以跳过
        httpProfile = HttpProfile()
        httpProfile.endpoint = "cvm.tencentcloudapi.com"

        # 实例化一个client选项，可选的，没有特殊需求可以跳过
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        # 实例化要请求产品的client对象,clientProfile是可选的
        client = cvm_client.CvmClient(cred, config['region'], clientProfile)

        # 实例化一个请求对象,每个接口都会对应一个request对象
        req = models.DescribeInstancesRequest()

        result_size = 100
        offset = 0
        cvm_infos = []
        total_cvm = 0

        while not result_size < 100:
            params = {
                "Offset": offset,
                "Limit": 100
            }
            req.from_json_string(json.dumps(params))

            # 返回的resp是一个DescribeInstancesResponse的实例，与请求对象对应
            resp = client.DescribeInstances(req)
            # 输出json格式的字符串回包
            instance_str = resp.to_json_string()
            struct = json.loads(instance_str)
            cvm_infos.extend(struct["InstanceSet"])
            offset += 100
            result_size = len(struct["InstanceSet"])
            total_cvm += result_size
            logger.info(f'Step 1: 腾讯云API调用 {total_cvm} 台CVM实例已获取')
            logger.debug(struct["InstanceSet"])
        logger.info(f'Step 1: 【{config["region"]}】可用区实例已经全部获取完毕，共获取【{total_cvm}】台CVM实例')
        return cvm_infos

    except TencentCloudSDKException as err:
        logging.error("发生错误：", exc_info=True)
