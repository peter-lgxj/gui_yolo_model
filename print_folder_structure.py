import os

def print_folder_structure(folder_path):
    """
    打印指定文件夹的文件名称和结构
    :param folder_path: 文件夹路径
    """
    print(f"文件夹 '{folder_path}' 的内容结构：")
    print("=" * 50)
    
    # 如果路径不存在，则退出
    if not os.path.exists(folder_path):
        print("错误：路径不存在！")
        return
    
    # 遍历文件夹
    for root, dirs, files in os.walk(folder_path):
        # 计算当前层级的缩进
        level = root.replace(folder_path, '').count(os.sep)
        indent = ' ' * 2 * level
        
        # 获取当前文件夹名
        folder_name = os.path.basename(root)
        
        # 打印当前文件夹名
        print(f"{indent}{folder_name}/")
        
        sub_indent = ' ' * 2 * (level + 1)
        
        # 打印当前文件夹中的所有子文件夹
        for dir_name in dirs:
            print(f"{sub_indent}[dir] {dir_name}/")
        
        # 打印当前文件夹中的所有文件
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_size = os.path.getsize(file_path)
            
            # 转换文件大小为可读格式
            size_str = convert_bytes(file_size)
            print(f"{sub_indent}[file] {file_name} ({size_str})")


def convert_bytes(bytes_value):
    """
    将字节数转换为可读的大小格式
    :param bytes_value: 字节数
    :return: 可读的大小字符串
    """
    if bytes_value == 0:
        return "0B"
    
    size_units = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(bytes_value, 1024)))
    p = math.pow(1024, i)
    s = round(bytes_value / p, 1)
    return f"{s}{size_units[i]}"


if __name__ == "__main__":
    # 指定要查看的文件夹路径
    target_folder = "runs/detect/runs/input_box5"
    full_path = os.path.join(os.getcwd(), target_folder)
    
    # 如果相对路径不存在，尝试使用绝对路径
    if not os.path.exists(target_folder):
        target_folder = "d:/Program/graduate_models/runs/detect/runs/input_box5"
    
    print_folder_structure(target_folder)