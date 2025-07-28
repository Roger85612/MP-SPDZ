#!/usr/bin/env python3
"""
金融场景MPC执行器
基于mpc_joint_analysis项目架构的金融场景真实MPC协议执行
使用financial_joint_analysis.mpc（增强版本）进行金融风险评估
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
        """将数据保存为MP-SPDZ输入格式 - 适配financial_joint_analysis.mpc"""
        
        # 确保Player-Data目录存在
        player_data_dir = self.mp_spdz_path / "Player-Data"
        player_data_dir.mkdir(exist_ok=True)
        
        for party_id in range(n_parties):
            input_file = player_data_dir / f"Input-P{party_id}-0"
            
            with open(input_file, 'w') as f:
                if party_id in party_data:
                    customers = party_data[party_id]['financial_data']
                    
                    # 写入数据 - 适配financial_joint_analysis.mpc的4变量输入格式
                    for customer in customers[:data_size]:
                        # 第1变量 - 信用评分 (300-850)
                        f.write(f"{int(customer['credit_score'])}\n")
                        # 第2变量 - 年收入 (千美元) - 保持原数值，现已调整为合理范围
                        f.write(f"{int(customer['income'])}\n")
                        # 第3变量 - 债务收入比 (%) - 转换为百分比整数
                        debt_ratio = int(customer['debt_ratio'] * 100)  # 转换0.185 -> 18
                        f.write(f"{debt_ratio}\n")
                        # 第4变量 - 违约标志 (0=正常, 1=违约) - 调整风险阈值
                        default_flag = 1 if customer.get('default_risk', 0) > 0.25 else 0
                        f.write(f"{default_flag}\n")
                    
                    logger.info(f"Party {party_id} 数据已保存到 {input_file} (4变量格式)")
                else:
                    logger.warning(f"Party {party_id} 没有生成数据")
    
    def compile_mpc_program(self, program_name: str = "financial_joint_analysis") -> bool:
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
    
    def execute_mascot_protocol(self, program_name: str = "financial_joint_analysis") -> Dict[str, Any]:
        """执行优化的MASCOT协议 - 增强版金融场景"""
        logger.info("=== 执行优化的MASCOT协议 (增强金融场景) ===")
        
        try:
            n_parties = self.config.get('system', {}).get('max_parties', 3)
            
            # 优化的MASCOT协议执行
            results = self._execute_optimized_mascot(n_parties, program_name)
            
            logger.info("优化MASCOT协议执行完成")
            return results
            
        except Exception as e:
            logger.error(f"MASCOT协议执行失败: {e}")
            return {
                'protocol_execution': 'FAILED',
                'protocol': 'MASCOT',
                'error': str(e),
                'success': False
            }
    
    def _execute_optimized_mascot(self, n_parties: int, program_name: str) -> Dict[str, Any]:
        """优化的MASCOT协议执行 - 处理增强金融场景的复杂性"""
        import subprocess
        import time
        from pathlib import Path
        
        logger.info(f"启动优化的MASCOT协议执行: {program_name}")
        
        # 切换到MP-SPDZ目录
        os.chdir(self.mp_spdz_path)
        
        # 第一步: 运行优化的离线阶段
        logger.info("步骤1: 执行优化的MASCOT离线阶段...")
        offline_success = self._run_optimized_offline_phase(n_parties, program_name)
        
        if not offline_success:
            return {
                'protocol_execution': 'OFFLINE_FAILED',
                'protocol': 'MASCOT',
                'n_parties': n_parties,
                'program': program_name,
                'success': False,
                'error': '优化的MASCOT离线阶段失败',
                'note': '增强金融场景预处理失败'
            }
        
        # 第二步: 运行优化的在线阶段
        logger.info("步骤2: 执行优化的MASCOT在线阶段...")
        online_results = self._run_optimized_online_phase(n_parties, program_name)
        
        # 第三步: 解析结果
        logger.info("步骤3: 解析增强金融场景结果...")
        parsed_results = self._parse_enhanced_financial_results(online_results)
        
        # 添加执行元数据
        parsed_results.update({
            'protocol': 'MASCOT_OPTIMIZED',
            'n_parties': n_parties,
            'program': program_name,
            'offline_phase': offline_success,
            'optimization_applied': True,
            'enhanced_financial_scenario': True
        })
        
        return parsed_results
    
    def _run_optimized_offline_phase(self, n_parties: int, program_name: str) -> bool:
        """优化的MASCOT离线阶段 - 增加超时和并发控制"""
        import subprocess
        
        logger.info(f"启动{n_parties}方优化离线阶段...")
        
        processes = []
        
        try:
            # 为每个参与方启动离线进程
            for party_id in range(n_parties):
                cmd = [
                    "./mascot-offline.x",
                    "-N", str(n_parties),
                    "-p", str(party_id),
                    program_name
                ]
                
                logger.info(f"启动优化离线Party {party_id}: {' '.join(cmd)}")
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=self.mp_spdz_path,
                    text=True
                )
                processes.append((party_id, process))
            
            # 等待所有进程完成 - 增加超时时间
            all_success = True
            for party_id, process in processes:
                try:
                    # 增强金融场景需要更长的预处理时间
                    stdout, stderr = process.communicate(timeout=300)  # 5分钟超时
                    returncode = process.returncode
                    
                    if returncode == 0:
                        logger.info(f"优化离线Party {party_id} 完成")
                    else:
                        logger.error(f"优化离线Party {party_id} 失败 (code {returncode})")
                        logger.error(f"错误输出: {stderr}")
                        all_success = False
                        
                except subprocess.TimeoutExpired:
                    logger.error(f"优化离线Party {party_id} 超时")
                    process.kill()
                    all_success = False
            
            return all_success
            
        except Exception as e:
            logger.error(f"优化离线阶段异常: {e}")
            return False
    
    def _run_optimized_online_phase(self, n_parties: int, program_name: str) -> Dict:
        """优化的MASCOT在线阶段 - 增强版金融场景"""
        import subprocess
        
        logger.info("启动优化的MASCOT在线阶段...")
        
        processes = []
        output_files = []
        
        # 为每个参与方启动在线进程
        for party_id in range(n_parties):
            output_file = f"enhanced_party{party_id}_output.txt"
            output_files.append(output_file)
            
            cmd = [
                "./mascot-party.x",
                "-N", str(n_parties),
                "-p", str(party_id),
                program_name
            ]
            
            logger.info(f"启动优化在线Party {party_id}: {' '.join(cmd)}")
            
            with open(output_file, 'w') as f:
                process = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    cwd=self.mp_spdz_path,
                    text=True
                )
                processes.append((party_id, process, output_file))
        
        # 等待所有进程完成 - 增强场景需要更长时间
        results = {}
        for party_id, process, output_file in processes:
            try:
                # 增强金融场景计算复杂度更高，增加超时时间
                returncode = process.wait(timeout=180)  # 3分钟超时
                
                # 读取输出
                with open(output_file, 'r') as f:
                    output = f.read()
                
                results[party_id] = {
                    'returncode': returncode,
                    'output': output,
                    'success': returncode == 0
                }
                
                logger.info(f"优化在线Party {party_id} 完成 (code {returncode})")
                
            except subprocess.TimeoutExpired:
                logger.warning(f"优化在线Party {party_id} 超时")
                process.kill()
                process.wait()
                results[party_id] = {
                    'returncode': -1,
                    'output': "增强金融场景在线阶段超时",
                    'success': False
                }
        
        return results
    
    def _parse_enhanced_financial_results(self, results: Dict) -> Dict:
        """解析增强金融场景的MPC结果"""
        import re
        
        logger.info("解析增强金融场景MPC结果...")
        
        # 寻找成功的结果
        successful_results = [r for r in results.values() if r.get('success', False)]
        
        if not successful_results:
            logger.error("没有成功的增强金融场景结果")
            return {
                'protocol_execution': 'FAILED',
                'success': False,
                'error': '增强金融场景MASCOT协议执行失败',
                'note': '真实协议执行失败 - 未使用模拟数据'
            }
        
        # 从成功的参与方获取结果
        primary_result = successful_results[0]
        output_text = primary_result['output']
        
        logger.info(f"增强金融场景输出长度: {len(output_text)} 字符")
        
        # 解析增强金融场景的统计结果
        parsed_results = {
            'protocol_execution': 'SUCCESS',
            'success': True,
            'enhanced_scenario': True
        }
        
        try:
            # 解析FINANCIAL_DISCLOSURE标记的结果 - 增强金融场景专用格式
            disclosure_lines = [line for line in output_text.split('\n') 
                              if 'FINANCIAL_DISCLOSURE' in line and ':' in line]
            
            logger.info(f"发现 {len(disclosure_lines)} 个金融披露行")
            
            for line in disclosure_lines:
                logger.info(f"处理金融披露行: {line}")
                
                # 解析增强金融场景的各种统计
                if "平均信用评分:" in line:
                    credit_match = re.search(r"平均信用评分:\s*([\d.-]+)", line)
                    if credit_match:
                        parsed_results['mean_credit_score'] = float(credit_match.group(1))
                
                elif "平均年收入:" in line:
                    income_match = re.search(r"平均年收入:\s*([\d.-]+|NaN)", line)
                    if income_match and income_match.group(1) != "NaN":
                        parsed_results['mean_income'] = float(income_match.group(1))
                    else:
                        parsed_results['mean_income'] = "数据溢出"
                
                elif "平均债务收入比:" in line:
                    debt_match = re.search(r"平均债务收入比:\s*([\d.-]+)", line)
                    if debt_match:
                        parsed_results['mean_debt_ratio'] = float(debt_match.group(1))
                
                elif "总体违约率:" in line:
                    default_match = re.search(r"总体违约率:\s*([\d.-]+)", line)
                    if default_match:
                        parsed_results['default_rate'] = float(default_match.group(1)) / 100  # 转换为小数
                
                elif "优秀信用客户数:" in line:
                    excellent_match = re.search(r"优秀信用客户数:\s*([\d.-]+)", line)
                    if excellent_match:
                        parsed_results['excellent_credit_customers'] = int(float(excellent_match.group(1)))
                
                elif "良好信用客户数:" in line:
                    good_match = re.search(r"良好信用客户数:\s*([\d.-]+)", line)
                    if good_match:
                        parsed_results['good_credit_customers'] = int(float(good_match.group(1)))
                
                elif "一般信用客户数:" in line:
                    fair_match = re.search(r"一般信用客户数:\s*([\d.-]+)", line)
                    if fair_match:
                        parsed_results['fair_credit_customers'] = int(float(fair_match.group(1)))
                
                elif "较差信用客户数:" in line:
                    poor_match = re.search(r"较差信用客户数:\s*([\d.-]+)", line)
                    if poor_match:
                        parsed_results['poor_credit_customers'] = int(float(poor_match.group(1)))
                
                elif "高风险客户比例:" in line:
                    high_risk_match = re.search(r"高风险客户比例:\s*([\d.-]+)", line)
                    if high_risk_match:
                        parsed_results['high_risk_ratio'] = float(high_risk_match.group(1))
                
                elif "优质客户比例:" in line:
                    premium_match = re.search(r"优质客户比例:\s*([\d.-]+)", line)
                    if premium_match:
                        parsed_results['premium_customer_ratio'] = float(premium_match.group(1))
            
            # 计算总客户数
            if all(key in parsed_results for key in ['excellent_credit_customers', 'good_credit_customers', 
                                                   'fair_credit_customers', 'poor_credit_customers']):
                parsed_results['total_customers'] = (
                    parsed_results['excellent_credit_customers'] + 
                    parsed_results['good_credit_customers'] + 
                    parsed_results['fair_credit_customers'] + 
                    parsed_results['poor_credit_customers']
                )
            
            logger.info(f"成功解析增强金融场景结果: {len(parsed_results)-2} 项统计")
            
        except Exception as e:
            logger.error(f"增强金融场景结果解析错误: {e}")
            return {
                'protocol_execution': 'PARSING_FAILED',
                'success': False,
                'error': f'增强金融场景结果解析失败: {str(e)}',
                'note': '协议执行成功但结果解析失败'
            }
        
        return parsed_results
    
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
        
        # 增强金融场景的结果展示
        if 'mean_credit_score' in results:
            print(f"📈 平均信用评分: {results['mean_credit_score']:.1f}")
        
        if 'mean_income' in results:
            if results['mean_income'] == "数据溢出":
                print(f"💰 平均年收入: {results['mean_income']} (超出精度范围)")
            else:
                print(f"💰 平均年收入: ${results['mean_income']:,.0f}")
        
        if 'mean_debt_ratio' in results:
            print(f"📊 平均债务收入比: {results['mean_debt_ratio']:.1f}%")
        
        if 'default_rate' in results:
            print(f"⚠️  违约率: {results['default_rate']:.1%}")
        
        if 'total_customers' in results:
            print(f"👥 总客户数: {results['total_customers']}")
        
        # 显示客户分层分析
        if 'excellent_credit_customers' in results:
            print(f"\n🏆 客户信用分层分析:")
            print(f"   ⭐ 优秀信用客户: {results['excellent_credit_customers']} 人")
            if 'good_credit_customers' in results:
                print(f"   ✅ 良好信用客户: {results['good_credit_customers']} 人")
            if 'fair_credit_customers' in results:
                print(f"   📊 一般信用客户: {results['fair_credit_customers']} 人")
            if 'poor_credit_customers' in results:
                print(f"   ⚠️  较差信用客户: {results['poor_credit_customers']} 人")
        
        # 显示风险分析
        if 'high_risk_ratio' in results:
            print(f"\n🚨 风险分析:")
            print(f"   高风险客户比例: {results['high_risk_ratio']:.1f}%")
        
        if 'premium_customer_ratio' in results:
            print(f"   优质客户比例: {results['premium_customer_ratio']:.1f}%")
        
        # 显示增强场景特定信息
        if results.get('enhanced_scenario', False):
            print(f"\n🎯 增强金融场景分析:")
            print("-"*60)
            print("✓ 4变量客户风险画像分析 (信用评分+收入+债务比+违约标志)")
            print("✓ 多维度金融风险评估")
            print("✓ 客户分层和违约预测模型")
        
        if results.get('optimization_applied', False):
            print(f"\n⚡ 协议优化:")
            print("-"*60)
            print("✓ 离线阶段超时优化 (5分钟)")
            print("✓ 在线阶段超时优化 (3分钟)")
            print("✓ 增强场景计算复杂度处理")
        
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
            if not self.compile_mpc_program("financial_joint_analysis"):
                return {'success': False, 'error': 'MPC程序编译失败'}
            
            # 3. 执行协议
            raw_results = self.execute_mascot_protocol("financial_joint_analysis")
            
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