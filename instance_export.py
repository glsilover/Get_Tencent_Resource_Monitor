import logging
from public_method import load_config

logger = logging.getLogger(__name__)
config = load_config('config.yaml')


def cvm_instance_export(cvm_infos):
    filtered_data = [{k: d[k] for k in config['cvm_params']} for d in cvm_infos]
    logger.debug(filtered_data)
    return filtered_data


def disk_instance_export(filtered_data):
    disk_list_all = []
    for instance in filtered_data:
        disk_dict = {'DiskId': instance['SystemDisk']['DiskId'], 'DiskKind': 'SystemDisk', 'DiskType': instance['SystemDisk']['DiskType'], 'DiskSize': instance['SystemDisk']['DiskSize'], 'InstanceId': instance['InstanceId'], 'InstanceName': instance['InstanceName']}
        disk_list_all.append(disk_dict)
        for disk in instance['DataDisks']:
            disk_dict_data = {'DiskId': disk['DiskId'], 'DiskKind': 'DataDisk', 'DiskType': disk['DiskType'], 'DiskSize': disk['DiskSize'], 'InstanceId': instance['InstanceId'], 'InstanceName': instance['InstanceName']}
            disk_list_all.append(disk_dict_data)

    logger.debug(disk_list_all)
    logger.info(f"Step 1: 【{config['region']}】可用区实例已经全部获取完毕，共获取【{len(disk_list_all)}】块云硬盘\n\n\n")

    return disk_list_all
