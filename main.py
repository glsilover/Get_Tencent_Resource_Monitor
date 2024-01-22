import logging
import describeInstances
from export_to_tablefile import list_to_excel, excel_to_list
from instance_export import cvm_instance_export, disk_instance_export
from get_monitor import get_all_instance_monitoring_result
from public_method import load_config
from match_ksyun_kec import cvm_matching
from match_ksyun_ebs import disk_matching

config = load_config('config.yaml')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    # 获取CVM实例信息
    cvm_infos = describeInstances.get_cvm_info()

    # 根据配置文件过滤CVM实例信息
    filtered_data = cvm_instance_export(cvm_infos)

    # 获取所有云硬盘的信息，包含系统盘和数据盘
    disk_list_all = disk_instance_export(filtered_data)

    # 获取所有CVM实例的监控数据
    logging.info(f"Step 2: 开始获取CVM实例监控数据, 共计{len(filtered_data)}台CVM实例, 请耐心等待\n\n\n")
    all_cvm_monitoring_result_dict = get_all_instance_monitoring_result(filtered_data, "QCE/CVM", 'InstanceId', config['cvm_monitor_params'])
    for monitor_values in all_cvm_monitoring_result_dict:
        list_to_excel(all_cvm_monitoring_result_dict[monitor_values], 'cvm_monitor_detail_data.xlsx', monitor_values)
    logging.info("Step 2: 所有CVM实例监控数据已导出到 'cvm_monitor_detail_data.xlsx' 文件")

    # 将CVM实例信息导出到Excel文件
    list_to_excel(filtered_data, 'cvm_monitor_detail_data.xlsx', 'CVM实例信息')
    logging.info("Step 2: 所有CVM实例信息已导出到 'cvm_monitor_detail_data.xlsx' 文件，'CVM实例信息' sheet\n\n\n")

    # 获取所有云硬盘的监控数据
    logging.info(f"Step 3: 开始获取云硬盘监控数据, 共计{len(disk_list_all)}块云硬盘, 请耐心等待")
    all_disk_monitoring_result_dict = get_all_instance_monitoring_result(disk_list_all, "QCE/BLOCK_STORAGE", 'DiskId', config['disk_monitor_params'])
    for monitor_values in all_disk_monitoring_result_dict:
        list_to_excel(all_disk_monitoring_result_dict[monitor_values], 'disk_monitor_detail_data.xlsx', monitor_values)
    logging.info("Step 3: 所有Disk实例监控数据已导出到 'disk_monitor_detail_data.xlsx' 文件")

    # 将云硬盘实例信息导出到Excel文件
    list_to_excel(disk_list_all, 'disk_monitor_detail_data.xlsx', 'Disk实例信息')
    logging.info("Step 3: 所有Disk实例信息已导出到 'disk_monitor_detail_data.xlsx' 文件，'Disk实例信息' sheet")


def match_ksyun():
    output_dict = {}
    cvm_data_list = excel_to_list('/Users/guantianyun/Desktop/test_2024.xlsx', 'CVM实例信息')
    disk_data_list = excel_to_list('/Users/guantianyun/Desktop/disk-test.xlsx', 'Disk实例信息')
    output_dict['CVM实例信息'] = cvm_matching(cvm_data_list)
    output_dict['Disk实例信息'] = disk_matching(disk_data_list, cvm_data_list)

    list_to_excel(output_dict['CVM实例信息'], '/Users/guantianyun/Desktop/cvm_finally20240121.xlsx', 'CVM实例信息')
    logging.info("Step 4: 所有CVM实例信息已匹配金山云产品并导出到 '/Users/guantianyun/Desktop/cvm_finally20240121.xlsx' 文件，'CVM实例信息' sheet\n\n\n")

    list_to_excel(output_dict['Disk实例信息'], '/Users/guantianyun/Desktop/disk_finally20240121.xlsx', 'Disk实例信息')
    logging.info("Step 4: 所有CVM实例信息已匹配金山云产品并导出到 '/Users/guantianyun/Desktop/disk_finally20240121.xlsx' 文件，'Disk实例信息' sheet\n\n\n")


if __name__ == "__main__":
    main()
    match_ksyun()
    logging.info("程序执行完毕")
