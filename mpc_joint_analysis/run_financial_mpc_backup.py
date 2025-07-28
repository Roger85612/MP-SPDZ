#!/usr/bin/env python3
"""
金融场景MPC执行器
基于mpc_joint_analysis项目架构的金融场景真实MPC协议执行
使用joint_statistics.mpc（复杂版本）进行联合统计分析
"""

import os
import sys
import logging
import yaml
from pathlib import Path
from typing import Dict, Any

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from mpc_data_generator import MPCDataGenerator
from mpc_executor import MPCProtocolExecutor
from mpc_program_manager import MPCProgramManager
from mpc_result_disclosure import MPCResultDisclosure

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FinancialMPCRunner:
    """金融场景MPC运行器"""
    
    def __init__(self, mp_spdz_path: str = "/mnt/c/Users/Lenovo/source/repos/MP-SPDZ"):
        self.mp_spdz_path = Path(mp_spdz_path)
        self.project_path = Path(__file__).parent
        
        # 加载配置
        self.config = self._load_config()
        
        # 初始化组件
        self.data_generator = MPCDataGenerator(seed=42)
        self.program_manager = MPCProgramManager(str(self.mp_spdz_path))
        self.protocol_executor = MPCProtocolExecutor(str(self.mp_spdz_path))
        self.disclosure_manager = MPCResultDisclosure("financial")
        
    def _load_config(self) -> Dict[str, Any]:
        """加载金融场景配置"""
        config_file = self.project_path / "scenario_1_financial_config.yaml"
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded financial scenario config from {config_file}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            # 使用默认配置
            return {
                'system': {'max_parties': 3, 'default_protocol': 'mascot'},
                'financial': {
                    'institutions': [
                        {'name': 'Bank Alpha', 'party_id': 0},
                        {'name': 'Bank Beta', 'party_id': 1}, 
                        {'name': 'Bank Gamma', 'party_id': 2}
                    ]
                }
            }
    
    def generate_financial_data(self, n_parties: int = 3, data_size: int = 100) -> bool:
        """生成金融场景的输入数据"""
        logger.info("=== 生成金融机构数据 ===")
        
        try:
            # 获取机构信息
            institutions = self.config.get('financial', {}).get('institutions', [])
            
            for i in range(n_parties):
                institution_name = institutions[i]['name'] if i < len(institutions) else f"Institution_{i}"
                logger.info(f"为 {institution_name} (Party {i}) 生成客户数据...")
            
            # 使用数据生成器创建数据
            party_data = self.data_generator.generate_financial_mpc_data(
                n_parties=n_parties,
                customers_per_bank=data_size
            )
            
            # 保存到MP-SPDZ输入文件格式
            self._save_to_mpc_input_format(party_data, n_parties, data_size)
            
            logger.info("金融数据生成完成")
            return True
            
        except Exception as e:
            logger.error(f"数据生成失败: {e}")
            return False
    
    def _save_to_mpc_input_format(self, party_data: Dict, n_parties: int, data_size: int):
        """将数据保存为MP-SPDZ输入格式"""
        
        # 确保Player-Data目录存在
        player_data_dir = self.mp_spdz_path / "Player-Data"
        player_data_dir.mkdir(exist_ok=True)
        
        for party_id in range(n_parties):
            input_file = player_data_dir / f"Input-P{party_id}-0"
            
            with open(input_file, 'w') as f:
                if party_id in party_data:
                    customers = party_data[party_id]['financial_data']
                    
                    # 写入数据 - 适配joint_statistics.mpc的输入格式
                    for customer in customers[:data_size]:
                        # X变量 - 信用评分
                        f.write(f"{int(customer['credit_score'])}\n")
                    
                    for customer in customers[:data_size]:
                        # Y变량 - 收入（缩放为百美元单位）
                        scaled_income = int(customer['income'] // 100)
                        f.write(f"{scaled_income}\n")
                    
                    logger.info(f"Party {party_id} 数据已保存到 {input_file}")
                else:
                    logger.warning(f"Party {party_id} 没有生成数据")
    
    def compile_mpc_program(self, program_name: str = "joint_statistics") -> bool:
        """编译MPC程序"""
        logger.info(f"=== 编译MPC程序: {program_name} ===")
        
        try:
            success = self.program_manager.compile_program(program_name)
            
            if success:
                logger.info(f"程序 {program_name} 编译成功")
            else:
                logger.error(f"程序 {program_name} 编译失败")
            
            return success
            
        except Exception as e:
            logger.error(f"编译过程出错: {e}")
            return False
    
    def execute_mascot_protocol(self, program_name: str = "joint_statistics") -> Dict[str, Any]:
        """执行MASCOT协议"""
        logger.info("=== 执行MASCOT协议 (金融场景) ===")
        
        try:
            n_parties = self.config.get('system', {}).get('max_parties', 3)
            
            # 执行MASCOT协议
            results = self.protocol_executor.execute_financial_mpc(
                n_parties=n_parties,
                program=program_name
            )
            
            logger.info("MASCOT协议执行完成")
            return results
            
        except Exception as e:
            logger.error(f"MASCOT协议执行失败: {e}")
            return {
                'protocol_execution': 'FAILED',
                'protocol': 'MASCOT',
                'error': str(e),
                'success': False
            }
    
    def process_results(self, raw_results: Dict[str, Any]) -> Dict[str, Any]:
        """处理和披露结果"""
        logger.info("=== 处理MPC计算结果 ===")
        
        try:
            # 使用披露管理器评估和处理结果
            context = {
                "sample_size": 300,  # 3方 * 100客户
                "regulatory_approved": True
            }
            
            # 批量评估披露
            disclosure_results = self.disclosure_manager.batch_evaluate_results(
                raw_results, context
            )
            
            # 合并原始结果和披露信息
            processed_results = raw_results.copy()
            processed_results.update({
                'disclosed_results': disclosure_results['disclosed_results'],
                'disclosure_summary': disclosure_results['evaluation_summary'],
                'audit_trail': disclosure_results['audit_trail']
            })
            
            logger.info(f"结果处理完成: {disclosure_results['evaluation_summary']['total_disclosed']}/{disclosure_results['evaluation_summary']['total_computed']} 项结果被披露")
            return processed_results
            
        except Exception as e:
            logger.error(f"结果处理失败: {e}")
            return raw_results
    
    def display_financial_results(self, results: Dict[str, Any]):
        """显示金融场景结果"""
        print("\n" + "="*80)
        print("🏦 金融机构联合统计分析结果")
        print("="*80)
        
        # 显示协议信息
        protocol = results.get('protocol', 'Unknown')
        print(f"\n🔧 使用协议: {protocol}")
        
        if protocol == 'MASCOT':
            print("   - 安全模型: 恶意敌手 (Malicious)")
            print("   - 敌手模型: 不诚实多数 (Dishonest Majority)")
        
        # 显示执行状态
        success = results.get('success', False)
        print(f"\n📊 协议执行状态: {'✅ 成功' if success else '❌ 失败'}")
        
        if not success:
            error = results.get('error', 'Unknown error')
            print(f"❌ 错误信息: {error}")
            return
        
        # 显示统计结果
        print(f"\n🔓 MPC联合统计结果:")
        print("-"*60)
        
        # 金融特定的结果展示
        if 'mean_credit_score' in results:
            print(f"📈 平均信用评分: {results['mean_credit_score']:.2f}")
        
        if 'mean_default_risk' in results:
            print(f"⚠️  平均违约风险: {results['mean_default_risk']:.4f}")
        
        if 'total_customers' in results:
            print(f"👥 总客户数: {results['total_customers']}")
        
        if 'high_risk_customers' in results:
            print(f"🚨 高风险客户数: {results['high_risk_customers']}")
        
        # 显示隐私保护信息
        print(f"\n🔒 隐私保护信息:")
        print("-"*60)
        print("✓ 各银行原始客户数据在整个计算过程中保持私密")
        print("✓ 只有最终的聚合统计结果被安全披露")
        print("✓ 使用金融级MPC协议提供强安全保证")
        print(f"✓ 符合 {protocol} 协议的安全模型要求")
        
        # 监管合规信息
        compliance = self.config.get('financial', {}).get('regulatory_compliance', [])
        if compliance:
            print(f"\n📋 监管合规:")
            print("-"*60)
            for standard in compliance:
                print(f"✓ {standard} 合规")
    
    def run_financial_scenario(self) -> Dict[str, Any]:
        """运行完整的金融场景"""
        logger.info("🚀 启动金融机构联合风险评估MPC场景")
        
        try:
            # 1. 生成数据
            if not self.generate_financial_data(n_parties=3, data_size=100):
                return {'success': False, 'error': '数据生成失败'}
            
            # 2. 编译程序
            if not self.compile_mpc_program("joint_statistics"):
                return {'success': False, 'error': 'MPC程序编译失败'}
            
            # 3. 执行协议
            raw_results = self.execute_mascot_protocol("joint_statistics")
            
            # 4. 处理结果
            final_results = self.process_results(raw_results)
            
            # 5. 显示结果
            self.display_financial_results(final_results)
            
            return final_results
            
        except Exception as e:
            logger.error(f"金融场景执行失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'protocol': 'MASCOT',
                'scenario': 'financial'
            }
        finally:
            # 清理资源
            self.protocol_executor.cleanup()

def main():
    """主函数"""
    print("🏦 金融机构联合风险评估MPC系统")
    print("基于MP-SPDZ的真实协议实现")
    print("="*80)
    
    # 创建运行器
    runner = FinancialMPCRunner()
    
    # 执行金融场景
    results = runner.run_financial_scenario()
    
    # 最终总结
    print("\n" + "="*80)
    if results.get('success', False):
        print("🎉 金融MPC场景执行成功!")
    else:
        print("❌ 金融MPC场景执行失败!")
        print(f"错误: {results.get('error', 'Unknown error')}")
    print("="*80)
    
    return results

if __name__ == "__main__":
    main()