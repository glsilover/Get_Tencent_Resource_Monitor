import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.monitor.v20180724 import monitor_client, models
from public_method import load_config
from datetime import datetime, timedelta
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

config = load_config('config.yaml')
logger = logging.getLogger(__name__)


def get_monitor_data(namespace, metric_name, period, instances_dimensions_name, instances_dimensions_value, start_time=config["start_time"], end_time=config["end_time"]):
    try:
        # 实例化一个认证对象，入参需要传入腾讯云账户 SecretId 和 SecretKey，此处还需注意密钥对的保密
        # 代码泄露可能会导致 SecretId 和 SecretKey 泄露，并威胁账号下所有资源的安全性。以下代码示例仅供参考，建议采用更安全的方式来使用密钥，请参见：https://cloud.tencent.com/document/product/1278/85305
        # 密钥可前往官网控制台 https://console.cloud.tencent.com/cam/capi 进行获取
        cred = credential.Credential(config['AK'], config['SK'])
        # 实例化一个http选项，可选的，没有特殊需求可以跳过
        httpProfile = HttpProfile()
        httpProfile.endpoint = "monitor.tencentcloudapi.com"
        # 实例化一个client选项，可选的，没有特殊需求可以跳过
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        # 实例化要请求产品的client对象,clientProfile是可选的
        client = monitor_client.MonitorClient(cred, config['region'], clientProfile)

        # 实例化一个请求对象,每个接口都会对应一个request对象
        req = models.GetMonitorDataRequest()

        # 腾讯云通过DescribeInstances接口返回的实例信息中，云硬盘实例的维度名称为"DiskId"，但是通过GetMonitorData接口获取监控数据时，实例的维度名称为"diskId"，因此需要对维度名称进行转换
        if instances_dimensions_name == 'DiskId':
            instances_dimensions_name = 'diskId'

        params = {
            "Namespace": namespace,
            "MetricName": metric_name,
            "Period": period,
            "StartTime": start_time,
            "EndTime": end_time,
            "Instances": [
                {
                    "Dimensions": [
                        {
                            "Name": instances_dimensions_name,
                            "Value": instances_dimensions_value
                        }
                    ]
                }
            ]
        }
        req.from_json_string(json.dumps(params))

        # 返回的resp是一个GetMonitorDataResponse的实例，与请求对象对应
        resp = client.GetMonitorData(req)
        # 输出json格式的字符串回包
        return json.loads(resp.to_json_string())

    except TencentCloudSDKException as err:
        print(err)


def process_single_instance_monitoring_data(monitor_data_dict_combine_list):
    """
    将腾讯云多次接口调用的监控数据，加工返回为时间戳对应的监控数据dict。

    参数:
    monitor_data_dict_combine_list (list): 包含多个监控数据字典的列表。

    返回:
    dict: 组合后的监控数据字典，其中时间戳作为键，值作为字典的值。
    """

    # 初始化两个空列表，用于存储所有监控数据的时间戳和值
    timestamps = []
    values = []

    # 遍历输入列表中的每个监控数据字典
    for i in range(len(monitor_data_dict_combine_list)):
        # 将当前字典的时间戳和值添加到对应的列表中
        timestamps.extend(monitor_data_dict_combine_list[i]['DataPoints'][0]['Timestamps'])
        values.extend(monitor_data_dict_combine_list[i]['DataPoints'][0]['Values'])

    # 将时间戳和值的列表组合成一个字典
    process_single_instance_monitoring_data_dict = dict(zip(timestamps, values))

    # 求监控数据的平均值、最大值
    try:
        max_num = round(max(values), 2)
        average_num = round(sum(values) / len(values), 2)
    except:
        max_num = 0
        average_num = 0

    # 打印出组合后的监控数据字典
    logger.debug(process_single_instance_monitoring_data_dict)

    # 返回组合后的监控数据字典
    return process_single_instance_monitoring_data_dict, max_num, average_num


def combine_single_instance_monitoring_data(namespace, metric_name, period, instances_dimensions_name, instances_dimensions_value):
    """
    根据指定的命名空间、指标名称、统计周期、实例名称和实例值，获取并组合监控数据。
    由于腾讯云单请求的数据点数限制为1440个， 若需要调用的指标、对象较多，可能存在因限频出现拉取失败的情况，因此需要将请求按时间维度均摊。
    该函数会判断，当采样周期为3600s时，直接调用接口获取。其他采样周期时逐天获取监控数据，并将每天的监控数据添加到一个列表中，对返回的监控数据不做任何处理。

    参数:
    namespace (str): 命名空间，例如 "QCE/CVM"。
    metric_name (str): 指标名称，例如 "CPUUtilization"。
    period (int): 统计周期，单位是秒，例如 300。
    instance_name (str): 实例名称，例如 "InstanceId"。
    instance_value (str): 实例的值，例如 "ins-abcdefgh"。

    返回:
    list: 包含多个监控数据字典的列表。

    示例:
    monitor_data_dict_combine_list = combine_monitor_data("QCE/CVM", "CPUUtilization", 300, "InstanceId", "ins-abcdefgh")
    """
    single_instance_monitoring_combine_list = []

    # 当统计周期为3600秒时，1个月的采样点为24*30<1440，可以直接调用 get_monitor_data 函数获取监控数据，无需拆分为多天进行获取
    if period == 3600:
        monitor_data_dict = get_monitor_data(namespace, metric_name, period, instances_dimensions_name, instances_dimensions_value, config["start_time"], config["end_time"])
        single_instance_monitoring_combine_list.append(monitor_data_dict)
    else:
        # 将时间字符串转换为datetime对象
        start_time_str = config["start_time"]
        end_time_str = config["end_time"]

        start_time = datetime.fromisoformat(start_time_str)
        end_time = datetime.fromisoformat(end_time_str)

        # 逐天迭代
        current_time = start_time
        while current_time < end_time:
            next_day = current_time + timedelta(days=1)
            # 转换为ISO格式的字符串
            start_time_iso = current_time.isoformat()
            end_time_iso = next_day.isoformat()

            if end_time_iso > end_time_str:
                end_time_iso = end_time_str

            # 调用 get_monitor_data 函数获取监控数据
            monitor_data_dict = get_monitor_data(namespace, metric_name, period, instances_dimensions_name, instances_dimensions_value, start_time_iso, end_time_iso)
            # 将获取到的监控数据添加到列表中
            single_instance_monitoring_combine_list.append(monitor_data_dict)
            # 到下一天
            logger.debug(f"调用API：开始时间 {start_time_iso}, 结束时间 {end_time_iso}")
            current_time = next_day

    # 返回包含多个监控数据字典的列表
    return single_instance_monitoring_combine_list


def calculate_single_instance_monitoring_data(instance_id, namespace, instances_dimensions_name, metric_dict):
    """
    计算单个实例的监控数据，包含了配置文件中各个维度的监控指标

    参数:
    instance_id (str): 实例的ID。
    namespace (str): 命名空间，例如 "QCE/CVM"。
    instances_dimensions_name (str): 实例维度名称，例如 "InstanceId"。
    metric_dict (dict): 包含所有要采集的监控项的字典。

    返回:
    dict: 包含单个实例监控结果的字典，其中键为监控项名称，值为监控项数据。

    示例:
    single_instance_monitoring_data = calculate_single_instance_monitoring_data("ins-abcdefgh", "QCE/CVM", "InstanceId", metric_dict)
    """
    single_instance_monitoring_data_dict = {}

    # 遍历配置文件中的所有监控项，并获取每个监控项的监控数据
    for metric in metric_dict:
        monitor_data_dict_combine_list = combine_single_instance_monitoring_data(namespace, metric['name'], metric['period'], instances_dimensions_name, instance_id)
        process_monitor_data_dict, max_num, average_num = process_single_instance_monitoring_data(monitor_data_dict_combine_list)

        instance_dict = {"instance_id": instance_id, "metric_unit": metric["unit"], "max_num": max_num, "average_num": average_num, 'start_time': config["start_time"], 'end_time': config["end_time"], 'period': metric['period']}
        update_dict = {**instance_dict, **process_monitor_data_dict}

        single_instance_monitoring_data_dict[metric['name']] = update_dict
        logger.debug(f"【{instance_id}】{metric['name']}监控数据已获取完毕")

    return single_instance_monitoring_data_dict


def get_all_instance_monitoring_result(instance_list_all, namespace, instances_dimensions_name, metric_dict):
    """
    获取所有实例的监控结果。

    参数:
    instance_list_all (list): 包含所有实例信息的列表。
    namespace (str): 命名空间，例如 "QCE/CVM"。
    instances_dimensions_name (str): 实例维度名称，例如 "InstanceId"。
    metric_dict (dict): 包含所有要采集的监控项的字典。

    返回:
    dict: 包含所有实例监控结果的字典，其中键为监控项名称，值为监控项数据列表。

    示例:
    all_instance_monitoring_result = get_all_instance_monitoring_result(instance_list, "QCE/CVM", "InstanceId", metric_dict)
    """
    all_instance_monitoring_result_dict = {}
    for monitor_params in metric_dict:
        all_instance_monitoring_result_dict[monitor_params['name']] = []

    # 使用多线程获取所有实例的监控数据
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(calculate_single_instance_monitoring_data, instance[instances_dimensions_name], namespace, instances_dimensions_name, metric_dict) for instance in instance_list_all]

        # 遍历所有线程的返回值
        for i, future in enumerate(futures):
            monitor_data = future.result()
            # 按照监控项名称，重新整理为以监控项为key，所有实例对应监控项指标数据list作为value的字典。以便输出至不同的Excel Sheet
            for monitor_values in all_instance_monitoring_result_dict:
                all_instance_monitoring_result_dict[monitor_values].append(monitor_data[monitor_values])
                # 将监控数据单位添加到实例信息字典中
                unit = monitor_data[f'{monitor_values}']['metric_unit']
                # 在实例信息汇总表中添加各监控项的总结数据包含最大值、平均值
                instance_list_all[i][f'{monitor_values}_max({unit})'] = monitor_data[f'{monitor_values}']['max_num']
                instance_list_all[i][f'{monitor_values}_average({unit})'] = monitor_data[f'{monitor_values}']['average_num']

                logging.debug(f"已完成第 {i + 1}/{len(instance_list_all)} 个实例的f'{monitor_values}监控数据采集")
            logging.info(f"当前正在进行【{instances_dimensions_name}: {instance_list_all[i][instances_dimensions_name]}】指标采集，已完成第 {i + 1}/{len(instance_list_all)} 个实例的监控数据采集")

    return all_instance_monitoring_result_dict

