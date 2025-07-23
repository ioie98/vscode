import pandas as pd
import argparse
import os

def process_data(input_csv, site_name, output_json):
    """
    预处理CSV数据并保存为JSON格式
    
    参数：
    input_csv -- 输入CSV文件路径
    site_name -- 站点名称（用于输出文件名）
    output_json -- 输出JSON文件路径
    """
    # 验证输入文件
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"输入文件不存在：{input_csv}")

    # 读取CSV数据
    df = pd.read_csv(input_csv)
    
    # 验证必要列
    required_columns = {'date', 'true', 'pred'}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"CSV文件缺少必要列：{', '.join(missing)}")

    # 转换日期格式
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # 保存为JSON
    df.to_json(
        output_json,
        orient='records',
        date_format='iso',
        default_handler=str,
        force_ascii=False
    )

    # 生成处理报告
    report = f"""
    ✅ 数据处理完成！
    ---------------------------
    输入文件：{os.path.abspath(input_csv)}
    输出文件：{os.path.abspath(output_json)}
    记录总数：{len(df):,}
    时间范围：{df['date'].iloc[0]} 至 {df['date'].iloc[-1]}
    数据列：{', '.join(df.columns)}
    """
    print(report)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='预测数据预处理工具',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--input',
        required=True,
        help='输入CSV文件路径\n示例：./B72/B72_pred1by1.csv'
    )
    parser.add_argument(
        '--site',
        required=True,
        help='站点名称（用于输出文件名）\n示例：B72'
    )
    parser.add_argument(
        '--output',
        default='./processed_data.json',
        help='输出JSON文件路径\n默认：./processed_data.json'
    )
    
    args = parser.parse_args()
    process_data(args.input, args.site, args.output)