import logging
from public_method import load_config

config = load_config('config.yaml')
logger = logging.getLogger(__name__)



def bindwidth_judgment(instance_dict):
    try:
        if instance_dict['KsyunBandwidth(Gbps)'] > max(instance_dict['LanIntraffic_max(Mbps)'], instance_dict['LanOuttraffic_max(Mbps)']) / 1000:
            matching_status = '匹配成功'
        else:
            matching_status = '匹配失败'
        return matching_status
    except KeyError:
        logger.warning(f'如下实例匹配失败,实例完整信息为：\n{instance_dict}', exc_info=False)
        return '匹配失败'


def kec_upgrade_judgment(instance_dict):
    upgrade_order_list = ['星河型HKEC', '标准型S6', '计算优化型C7']
    # 查找instance['KsyunType']在upgrade_order_list中的位置
    instance_index = upgrade_order_list.index(instance_dict['KsyunType'])
    try:
        instance_dict['KsyunType'] = upgrade_order_list[instance_index + 1]
        instance_dict = kec_matching(instance_dict)
        if bindwidth_judgment(instance_dict) == '匹配成功':
            instance_dict['matching_status'] = '已升级'
        else:
            instance_dict['matching_status'] = '匹配失败'
    except IndexError:
        instance_dict['KsyunType'] = '无法满足'
        instance_dict['KsyunPrice(元/月)'] = 0
        instance_dict['KsyunPayPrice(元/月)'] = 0
        instance_dict['KsyunBandwidth(Gbps)'] = 0
        logger.warning(f'【{instance_dict["TencentType"]}】实例类型无法满足带宽需求,实例完整信息为：\n{instance_dict}', exc_info=False)
    return instance_dict


def kec_matching(instance_dict):
    try:
        instance_dict['KsyunPrice(元/月)'] = config['ksyun_kec'][instance_dict['KsyunType']]['price']['cpu'] * instance_dict['CPU'] + config['ksyun_kec'][instance_dict['KsyunType']]['price']['memory'] * instance_dict['Memory']
        instance_dict['KsyunPayPrice(元/月)'] = instance_dict['KsyunPrice(元/月)'] * config['ksyun_kec'][instance_dict['KsyunType']]['price']['discount']
        instance_dict['KsyunBandwidth(Gbps)'] = config['ksyun_kec'][instance_dict['KsyunType']]['internal_throughput'][instance_dict['CPU']]
    except KeyError:
        instance_dict['KsyunType'] = '未知'
        logger.warning(f'如下实例匹配失败,实例完整信息为：\n{instance_dict}', exc_info=False)
    return instance_dict


def cvm_matching(cvm_data_list):
    for instance in cvm_data_list:
        instance['TencentType'] = instance['InstanceType'].split('.')[0]
        try:
            instance['KsyunType'] = config['cvm_mapping'][instance['TencentType']]
            kec_matching(instance)
            instance['matching_status'] = bindwidth_judgment(instance)
            while instance['matching_status'] == '匹配失败':
                instance = kec_upgrade_judgment(instance)
        except KeyError:
            instance['KsyunType'] = '未知'
            logger.warning(f'如下实例匹配失败,实例完整信息为：\n{instance}', exc_info=False)
    return cvm_data_list
