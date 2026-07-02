"""
功能：批量将当前文件夹下所有 CSV 文件转换为 UTF-8 BOM 编码，并直接覆盖原文件
警告：会修改原始文件，建议先备份！
"""
import os
import pandas as pd

TARGET_DIR = R"D:\PythonProject\Bilibili\Bili\tools\Data"   # 改为你的文件夹路径，如 r"D:\导出文件夹"
BACKUP_DIR = os.path.join(TARGET_DIR, "backup_before_convert")  # 可选备份目录

def batch_convert_and_replace(target_dir=TARGET_DIR, create_backup=True):
    if create_backup:
        os.makedirs(BACKUP_DIR, exist_ok=True)

    for filename in os.listdir(target_dir):
        if filename.lower().endswith(".csv"):
            filepath = os.path.join(target_dir, filename)
            try:
                # 自动检测编码并读取
                df = None
                used_enc = None
                for enc in ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'gb18030', 'utf-16']:
                    try:
                        df = pd.read_csv(filepath, encoding=enc)
                        used_enc = enc
                        break
                    except UnicodeDecodeError:
                        continue
                if df is None:
                    print(f"❌ {filename} 无法识别编码，跳过")
                    continue

                # 可选：备份原文件
                if create_backup:
                    import shutil
                    shutil.copy2(filepath, os.path.join(BACKUP_DIR, filename))

                # 直接覆盖写入原文件，使用 utf-8-sig 编码
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
                print(f"✅ {filename} 转换并覆盖成功（原编码：{used_enc}）")
            except Exception as e:
                print(f"❌ {filename} 处理失败：{e}")

if __name__ == "__main__":
    # 为安全起见，默认会备份原文件到 backup_before_convert 文件夹
    # 若不想备份，设置 create_backup=False
    batch_convert_and_replace(create_backup=False)
    print("处理完成！")