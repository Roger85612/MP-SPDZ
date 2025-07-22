#!/usr/bin/env python3
"""
测试真实Shamir协议执行
专门用于验证reveal机制的数据披露功能
"""

import sys
import logging
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from mpc_executor import MPCProtocolExecutor
import numpy as np

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('test_real_shamir.log')
        ]
    )

def generate_simple_test_data():
    """生成简单的测试数据供joint_statistics使用"""
    
    # 确保Input目录存在
    input_dir = Path("/mnt/c/Users/Lenovo/source/repos/MP-SPDZ/Player-Data")
    input_dir.mkdir(exist_ok=True)
    
    # 为3个参与方生成数据
    np.random.seed(42)
    
    for party_id in range(3):
        # X和Y数据各100个点
        x_data = np.random.uniform(20, 100, 100)  # X值：20-100之间
        y_data = np.random.uniform(30, 100, 100)  # Y值：30-100之间
        
        # 创建输入文件
        input_file = input_dir / f"Input-P{party_id}-0"
        
        with open(input_file, 'w') as f:
            # 先写X数据
            for x in x_data:
                f.write(f"{x:.1f}\n")
            # 再写Y数据  
            for y in y_data:
                f.write(f"{y:.1f}\n")
        
        print(f"Generated input data for Party {party_id}: {len(x_data) + len(y_data)} values")

def test_real_shamir_protocol():
    """测试真实的Shamir协议执行"""
    
    logger = logging.getLogger(__name__)
    logger.info("=== 开始真实Shamir协议测试 ===")
    
    try:
        # 1. 创建MPC执行器
        executor = MPCProtocolExecutor()
        
        # 2. 生成测试数据
        generate_simple_test_data()
        logger.info("✅ 测试数据生成完成")
        
        # 3. 执行医疗场景MPC
        logger.info("🏥 执行医疗场景 (Shamir协议) ...")
        medical_results = executor.execute_medical_mpc(
            n_parties=3, 
            program="joint_statistics"
        )
        
        # 4. 显示结果
        print("\n" + "="*60)
        print("🏥 医疗场景MPC计算结果 (Shamir协议)")
        print("="*60)
        
        # 检查协议执行状态
        protocol_status = medical_results.get('protocol_execution', 'UNKNOWN')
        execution_success = medical_results.get('success', False)
        
        if protocol_status == 'SUCCESS' and execution_success:
            print("✅ 真实Shamir协议执行成功")
            print("✅ Reveal机制成功披露业务数据")
            
            # 显示实际的业务数据
            if 'mean_x' in medical_results:
                print(f"平均X值 (如血压): {medical_results['mean_x']:.2f}")
            if 'mean_y' in medical_results:
                print(f"平均Y值 (如治疗效果): {medical_results['mean_y']:.2f}")
            if 'variance_x' in medical_results:
                print(f"X方差: {medical_results['variance_x']:.2f}")
            if 'variance_y' in medical_results:
                print(f"Y方差: {medical_results['variance_y']:.2f}")
            if 'correlation_xy' in medical_results:
                print(f"X-Y相关性: {medical_results['correlation_xy']:.3f}")
            if 'beta_coefficient' in medical_results:
                print(f"回归系数β: {medical_results['beta_coefficient']:.3f}")
                
        elif protocol_status == 'FAILED':
            print("❌ 真实Shamir协议执行失败")
            print(f"协议状态: {protocol_status}")
            print(f"失败原因: {medical_results.get('error', 'Unknown error')}")
            
            # 显示详细的失败信息
            if 'failure_details' in medical_results:
                print("\n详细失败信息:")
                for detail in medical_results['failure_details']:
                    print(f"  - {detail}")
                    
        elif protocol_status == 'PARSING_FAILED':
            print("⚠️  Shamir协议执行成功，但结果解析失败")
            print(f"解析错误: {medical_results.get('error', 'Unknown parsing error')}")
            
        else:
            print(f"❌ 协议执行异常: {protocol_status}")
            print(f"错误: {medical_results.get('error', 'Unknown error')}")
        
        # 显示通用信息
        print(f"协议类型: {medical_results.get('protocol', 'Shamir')}")
        print(f"参与方数量: {medical_results.get('n_parties', 3)}")
        print(f"程序名称: {medical_results.get('program', 'joint_statistics')}")
        
        if 'note' in medical_results:
            print(f"备注: {medical_results['note']}")
        
        # 5. 返回结果供进一步分析
        return medical_results
        
    except Exception as e:
        logger.error(f"真实Shamir协议测试失败: {e}")
        return {'error': str(e)}
    
    finally:
        try:
            executor.cleanup()
        except:
            pass

def save_results_report(medical_results):
    """保存结果报告"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"real_mpc_analysis_report_medical_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# 真实MPC协议执行分析报告 - 医疗场景\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 医疗场景分析结果 (Shamir协议)\n\n")
        f.write("### 关键业务指标\n\n")
        
        if medical_results.get('execution_success'):
            f.write("✅ **协议执行状态**: 成功\n\n")
        else:
            f.write("❌ **协议执行状态**: 失败\n\n")
        
        if 'mean_x' in medical_results:
            f.write(f"- **平均X值** (如血压): {medical_results['mean_x']:.2f}\n")
        if 'mean_y' in medical_results:
            f.write(f"- **平均Y值** (如治疗效果): {medical_results['mean_y']:.2f}\n")
        if 'correlation_xy' in medical_results:
            f.write(f"- **X-Y相关性**: {medical_results['correlation_xy']:.3f}\n")
        if 'beta_coefficient' in medical_results:
            f.write(f"- **回归系数β**: {medical_results['beta_coefficient']:.3f}\n")
        
        f.write("\n### Reveal机制验证\n\n")
        f.write("本测试验证了MPC程序中的reveal机制能够正确披露计算结果：\n\n")
        f.write("```mpc\n")
        f.write("print_ln(\"BUSINESS_DISCLOSURE - Mean X: %s\", mean_x.reveal())\n")
        f.write("print_ln(\"BUSINESS_DISCLOSURE - Mean Y: %s\", mean_y.reveal())\n")
        f.write("print_ln(\"BUSINESS_DISCLOSURE - Correlation X-Y: %s\", correlation.reveal())\n")
        f.write("print_ln(\"BUSINESS_DISCLOSURE - Beta Coefficient: %s\", beta_coefficient.reveal())\n")
        f.write("```\n\n")
        
        f.write("### 技术细节\n\n")
        f.write(f"- **协议类型**: {medical_results.get('protocol', 'Unknown')}\n")
        f.write(f"- **参与方数量**: {medical_results.get('n_parties', 'Unknown')}\n")
        f.write(f"- **程序名称**: {medical_results.get('program', 'Unknown')}\n")
        
        if medical_results.get('mpc_execution') == 'simulated':
            f.write("\n⚠️ **注意**: 当前结果为模拟数据，真实MPC协议执行遇到问题\n")
            f.write("需要进一步调试以下问题：\n")
            f.write("1. 确保shamir-party.x可执行文件路径正确\n")
            f.write("2. 验证输入数据格式和路径\n")
            f.write("3. 检查MP-SPDZ编译环境\n")
            f.write("4. 确认网络端口配置\n")
        
        if 'error' in medical_results:
            f.write(f"\n❌ **错误信息**: {medical_results['error']}\n")
        
        f.write("\n### 原始结果数据\n\n")
        f.write("```json\n")
        f.write(json.dumps(medical_results, indent=2, ensure_ascii=False))
        f.write("\n```\n")
    
    print(f"\n📊 详细分析报告已保存至: {report_file}")

def main():
    """主函数"""
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🚀 启动真实Shamir协议测试")
    print("目标: 验证reveal机制的数据披露功能")
    print("-" * 50)
    
    try:
        # 执行真实Shamir协议测试
        medical_results = test_real_shamir_protocol()
        
        # 保存结果报告
        save_results_report(medical_results)
        
        print("\n" + "="*60)
        print("📈 Shamir协议测试完成")
        print("="*60)
        
        # 判断执行状态
        if medical_results.get('execution_success'):
            print("✅ 真实Shamir协议执行成功!")
            print("✅ Reveal机制成功披露业务数据!")
        elif medical_results.get('mpc_execution') == 'simulated':
            print("⚠️  使用模拟数据 (真实协议执行遇到技术问题)")
            print("🔧 需要进一步调试协议执行环境")
        else:
            print("❌ Shamir协议执行失败")
            print(f"错误: {medical_results.get('error', '未知错误')}")
        
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        print(f"❌ 测试执行失败: {e}")

if __name__ == "__main__":
    main()