import logging
from public_method import load_config

config = load_config('config.yaml')
logger = logging.getLogger(__name__)


def performance_judgment(instance_dict):
    try:
        if instance_dict['Ksyun_IO'] > max(instance_dict['DiskReadTraffic_max(KB/s)'], instance_dict['DiskWriteTraffic_max(KB/s)']) / 1000:
            if instance_dict['Ksyun_IOPS'] > max(instance_dict['DiskReadIops_max(个/s)'], instance_dict['DiskWriteIops_max(个/s)']):
                matching_status = '匹配成功'
            else:
                matching_status = '匹配失败'
                print(instance_dict)
        else:
            matching_status = '匹配失败'
            print(instance_dict)
        return matching_status
    except KeyError:
        logger.warning(f'如下实例匹配失败,实例完整信息为：\n{instance_dict}', exc_info=False)
        return '匹配失败'

def kec_fit_judgment(instance_dict, cvm_data_list):
    for kec_instance in cvm_data_list:
        if kec_instance['InstanceId'] == instance_dict['InstanceId']:
            ebs_fit_list = config['ksyun_kec'][kec_instance['KsyunType']]['EBS']
            instance_dict['KECType'] = kec_instance['KsyunType']
            if instance_dict['KsyunType'] in ebs_fit_list:
                instance_dict['matching_status'] = '匹配成功'
            else:
                instance_dict['matching_status'] = '匹配失败'
                instance_dict['KsyunType'] = 'SSD3.0'
    return instance_dict

def calculate_performance_ksyun_ebs(instance_dict):
    basic_io = config['ksyun_ebs'][instance_dict['KsyunType']]['IO']['basic']
    max_io = config['ksyun_ebs'][instance_dict['KsyunType']]['IO']['max']
    times_io = config['ksyun_ebs'][instance_dict['KsyunType']]['IO']['times']
    basic_iops = config['ksyun_ebs'][instance_dict['KsyunType']]['IOPS']['basic']
    max_iops = config['ksyun_ebs'][instance_dict['KsyunType']]['IOPS']['max']
    times_iops = config['ksyun_ebs'][instance_dict['KsyunType']]['IOPS']['times']
    instance_dict['Ksyun_IO'] = min((basic_io + times_io * instance_dict['DiskSize']), max_io)
    instance_dict['Ksyun_IOPS'] = min((basic_iops + times_iops * instance_dict['DiskSize']), max_iops)

    return instance_dict

def price_match(instance_dict):
    if instance_dict['DiskKind'] == 'SystemDisk':
        bill_disksize = max(instance_dict['DiskSize'] - 50, 0)
    else:
        bill_disksize = instance_dict['DiskSize']
    instance_dict['KsyunPrice(元/月)'] = config['ksyun_ebs'][instance_dict['KsyunType']]['price']['disk'] * bill_disksize
    instance_dict['KsyunPayPrice(元/月)'] = instance_dict['KsyunPrice(元/月)'] * config['ksyun_ebs'][instance_dict['KsyunType']]['price']['discount']
    return instance_dict


def disk_matching(disk_data_list, cvm_data_list):
    for instance in disk_data_list:
        try:
            instance['KsyunType'] = config['disk_mapping'][instance['DiskType']]
            # 当前未有不满足的，因此不考虑升级，仅考虑机型适配，适配机型星河不支持ESSD，其他机型都用ESSD替换
            kec_fit_judgment(instance, cvm_data_list)
            instance = calculate_performance_ksyun_ebs(instance)
            instance['matching_status'] = performance_judgment(instance)
            instance = price_match(instance)

        except KeyError:
            instance['KsyunType'] = '未知'
            instance['matching_status'] = '匹配失败'
            logger.warning(f'如下实例匹配失败,实例完整信息为：\n{instance}', exc_info=False)
    return disk_data_list

