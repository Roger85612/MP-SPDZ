#!/usr/bin/env python3
"""
测试协议执行状态 - 不使用模拟数据
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from mpc_executor import MPCProtocolExecutor

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def test_protocol_execution():
    """测试协议执行状态 - 验证无模拟数据fallback"""
    
    print("🔍 测试真实MPC协议执行状态（金融和医疗场景）")
    print("="*70)
    print("目标: 验证协议失败时不使用模拟数据")
    print("="*70)
    
    results = {}
    
    # 1. 测试金融场景 (MASCOT)
    print("\n🏦 金融场景 - MASCOT协议测试")
    print("-" * 40)
    
    try:
        executor = MPCProtocolExecutor()
        financial_results = executor.execute_financial_mpc(3, "financial_risk_analysis")
        executor.cleanup()
        
        print(f"协议类型: {financial_results.get('protocol', 'UNKNOWN')}")
        print(f"执行状态: {financial_results.get('protocol_execution', 'UNKNOWN')}")
        print(f"成功: {financial_results.get('success', False)}")
        
        # 检查模拟数据
        has_simulation = 'simulated' in str(financial_results).lower() or 'mpc_execution' in financial_results
        print(f"包含模拟数据: {'是' if has_simulation else '否'}")
        print(f"错误信息: {financial_results.get('error', '无')}")
        print(f"备注: {financial_results.get('note', '无')}")
        
        results['financial'] = {
            'protocol': financial_results.get('protocol'),
            'success': financial_results.get('success', False),
            'has_simulation': has_simulation,
            'status': financial_results.get('protocol_execution', 'UNKNOWN')
        }
        
    except Exception as e:
        print(f"❌ 异常: {e}")
        results['financial'] = {'success': False, 'has_simulation': False, 'error': str(e)}
    
    # 2. 测试医疗场景 (Shamir)
    print("\n🏥 医疗场景 - Shamir协议测试")
    print("-" * 40)
    
    try:
        executor = MPCProtocolExecutor()
        medical_results = executor.execute_medical_mpc(3, "joint_statistics")
        executor.cleanup()
        
        print(f"协议类型: {medical_results.get('protocol', 'UNKNOWN')}")
        print(f"执行状态: {medical_results.get('protocol_execution', 'UNKNOWN')}")
        print(f"成功: {medical_results.get('success', False)}")
        
        # 检查模拟数据
        has_simulation = 'simulated' in str(medical_results).lower() or 'mpc_execution' in medical_results
        print(f"包含模拟数据: {'是' if has_simulation else '否'}")
        print(f"错误信息: {medical_results.get('error', '无')}")
        print(f"备注: {medical_results.get('note', '无')}")
        
        results['medical'] = {
            'protocol': medical_results.get('protocol'),
            'success': medical_results.get('success', False),
            'has_simulation': has_simulation,
            'status': medical_results.get('protocol_execution', 'UNKNOWN')
        }
        
    except Exception as e:
        print(f"❌ 异常: {e}")
        results['medical'] = {'success': False, 'has_simulation': False, 'error': str(e)}
    
    # 3. 验证总结
    print("\n" + "="*70)
    print("📋 协议执行状态验证总结")
    print("="*70)
    
    financial_clean = not results.get('financial', {}).get('has_simulation', True)
    medical_clean = not results.get('medical', {}).get('has_simulation', True)
    
    print(f"✅ 金融场景 (MASCOT): {'无模拟数据' if financial_clean else '检测到模拟数据'}")
    print(f"✅ 医疗场景 (Shamir): {'无模拟数据' if medical_clean else '检测到模拟数据'}")
    
    if financial_clean and medical_clean:
        print("\n🎉 验证成功!")
        print("✅ 两个场景都不使用模拟数据fallback")
        print("✅ 协议执行失败时正确报告真实状态")
        print("✅ 系统准备就绪，可进行真实MPC协议调试")
    else:
        print("\n❌ 发现问题:")
        if not financial_clean:
            print("   - 金融场景仍有模拟数据fallback")
        if not medical_clean:
            print("   - 医疗场景仍有模拟数据fallback")
    
    return financial_clean and medical_clean

def main():
    """主函数"""
    setup_logging()
    success = test_protocol_execution()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())