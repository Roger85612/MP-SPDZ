#!/usr/bin/env python3
"""
MPC程序管理器
管理基础MPC程序和场景特定程序的编译、执行和结果处理
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json
import tempfile

logger = logging.getLogger(__name__)

class MPCProgramManager:
    """MPC程序管理器 - 负责MPC程序的生命周期管理"""
    
    def __init__(self, mp_spdz_path: str = "/mnt/c/Users/Lenovo/source/repos/MP-SPDZ"):
        self.mp_spdz_path = Path(mp_spdz_path)
        self.programs_source = self.mp_spdz_path / "Programs" / "Source"
        self.programs_bytecode = self.mp_spdz_path / "Programs" / "Bytecode"
        self.joint_analysis_path = self.mp_spdz_path / "mpc_joint_analysis"
        
        # 基础MPC程序映射
        self.base_programs = {
            'statistics': 'joint_statistics',
            'regression': 'joint_regression',
            'clustering': 'joint_clustering',
            'ml': 'privacy_preserving_ml',
            'aggregation': 'secure_aggregation'
        }
        
        # 场景特定程序映射
        self.scenario_programs = {
            'financial': 'financial_risk_analysis',
            'medical': 'medical_research_analysis'
        }
        
    def ensure_program_exists(self, program_name: str) -> bool:
        """确保MPC程序文件存在"""
        
        # 检查基础程序
        base_program_path = self.joint_analysis_path / "mpc_programs" / f"{program_name}.mpc"
        if base_program_path.exists():
            return True
            
        # 检查场景程序
        scenario_program_path = self.programs_source / f"{program_name}.mpc"
        if scenario_program_path.exists():
            return True
            
        logger.error(f"MPC program not found: {program_name}")
        return False
    
    def copy_program_to_source(self, program_name: str) -> bool:
        """将基础MPC程序复制到MP-SPDZ源码目录"""
        
        try:
            # 源文件路径
            src_path = self.joint_analysis_path / "mpc_programs" / f"{program_name}.mpc"
            # 目标路径
            dst_path = self.programs_source / f"{program_name}.mpc"
            
            if not src_path.exists():
                logger.error(f"Source program not found: {src_path}")
                return False
                
            # 复制文件
            import shutil
            shutil.copy2(src_path, dst_path)
            logger.info(f"Copied {src_path} to {dst_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to copy program {program_name}: {e}")
            return False
    
    def compile_program(self, program_name: str, field_size: int = 64) -> Tuple[bool, str]:
        """编译MPC程序"""
        
        logger.info(f"Compiling MPC program: {program_name}")
        
        try:
            # 确保程序存在于源码目录
            program_path = self.programs_source / f"{program_name}.mpc"
            if not program_path.exists():
                # 尝试从基础程序复制
                if not self.copy_program_to_source(program_name):
                    return False, f"Program {program_name} not found and cannot be copied"
            
            # 编译命令
            cmd = [
                "python3", "compile.py",
                program_name,
                "-g", str(field_size)
            ]
            
            # 执行编译
            result = subprocess.run(
                cmd,
                cwd=self.mp_spdz_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully compiled {program_name}")
                logger.debug(f"Compile output: {result.stdout}")
                return True, result.stdout
            else:
                logger.error(f"Compilation failed for {program_name}")
                logger.error(f"Error output: {result.stderr}")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            logger.error(f"Compilation timeout for {program_name}")
            return False, "Compilation timeout"
        except Exception as e:
            logger.error(f"Compilation error for {program_name}: {e}")
            return False, str(e)
    
    def is_program_compiled(self, program_name: str) -> bool:
        """检查程序是否已编译"""
        bytecode_path = self.programs_bytecode / f"{program_name}-0.bc"
        return bytecode_path.exists()
    
    def get_program_dependencies(self, program_name: str) -> List[str]:
        """获取程序依赖的基础程序列表"""
        
        # 场景程序的依赖关系
        dependencies = {
            'financial_risk_analysis': ['joint_statistics', 'joint_regression'],
            'medical_research_analysis': ['joint_statistics', 'joint_regression']
        }
        
        return dependencies.get(program_name, [])
    
    def ensure_dependencies_compiled(self, program_name: str) -> Tuple[bool, List[str]]:
        """确保程序的所有依赖都已编译"""
        
        dependencies = self.get_program_dependencies(program_name)
        failed_deps = []
        
        for dep in dependencies:
            if not self.is_program_compiled(dep):
                logger.info(f"Compiling dependency: {dep}")
                success, error = self.compile_program(dep)
                if not success:
                    failed_deps.append(dep)
                    logger.error(f"Failed to compile dependency {dep}: {error}")
        
        return len(failed_deps) == 0, failed_deps
    
    def prepare_program_for_execution(self, program_name: str) -> Tuple[bool, str]:
        """准备程序执行 - 编译程序和依赖"""
        
        logger.info(f"Preparing program for execution: {program_name}")
        
        try:
            # 1. 检查并编译依赖
            deps_ok, failed_deps = self.ensure_dependencies_compiled(program_name)
            if not deps_ok:
                return False, f"Failed to compile dependencies: {failed_deps}"
            
            # 2. 检查主程序是否已编译
            if not self.is_program_compiled(program_name):
                success, error = self.compile_program(program_name)
                if not success:
                    return False, f"Failed to compile main program: {error}"
            
            logger.info(f"Program {program_name} ready for execution")
            return True, "Program prepared successfully"
            
        except Exception as e:
            logger.error(f"Failed to prepare program {program_name}: {e}")
            return False, str(e)
    
    def create_input_data_file(self, party_id: int, data: Dict[str, Any], 
                              program_name: str) -> Tuple[bool, str]:
        """为特定参与方创建输入数据文件"""
        
        try:
            # 创建输入文件路径
            input_file = self.mp_spdz_path / f"Player-Data/Input-P{party_id}-0"
            
            # 确保目录存在
            input_file.parent.mkdir(exist_ok=True)
            
            # 根据程序类型格式化数据
            formatted_data = self._format_input_data(data, program_name)
            
            # 写入文件
            with open(input_file, 'w') as f:
                f.write(formatted_data)
            
            logger.info(f"Created input file for Party {party_id}: {input_file}")
            return True, str(input_file)
            
        except Exception as e:
            logger.error(f"Failed to create input file for Party {party_id}: {e}")
            return False, str(e)
    
    def _format_input_data(self, data: Dict[str, Any], program_name: str) -> str:
        """格式化输入数据为MP-SPDZ格式"""
        
        if program_name in ['joint_statistics', 'financial_risk_analysis']:
            # 统计类程序的数据格式
            lines = []
            if 'values' in data:
                for value in data['values']:
                    lines.append(str(float(value)))
            return '\n'.join(lines)
            
        elif program_name in ['joint_regression', 'medical_research_analysis']:
            # 回归类程序的数据格式
            lines = []
            if 'features' in data and 'targets' in data:
                # 先写特征数据
                for features in data['features']:
                    for feature in features:
                        lines.append(str(float(feature)))
                # 再写目标数据
                for target in data['targets']:
                    lines.append(str(float(target)))
            return '\n'.join(lines)
        
        else:
            # 默认格式 - 简单数值列表
            lines = []
            for key, values in data.items():
                if isinstance(values, (list, tuple)):
                    for value in values:
                        lines.append(str(float(value)))
                else:
                    lines.append(str(float(values)))
            return '\n'.join(lines)
    
    def cleanup_program_files(self, program_name: str):
        """清理程序相关的临时文件"""
        
        try:
            # 清理输入文件
            for i in range(10):  # 支持最多10个参与方
                input_file = self.mp_spdz_path / f"Player-Data/Input-P{i}-0"
                if input_file.exists():
                    input_file.unlink()
                    
            logger.info(f"Cleaned up temporary files for {program_name}")
            
        except Exception as e:
            logger.warning(f"Failed to cleanup files for {program_name}: {e}")
    
    def get_available_programs(self) -> Dict[str, List[str]]:
        """获取所有可用的MPC程序"""
        
        available = {
            'base_programs': [],
            'scenario_programs': []
        }
        
        # 检查基础程序
        base_dir = self.joint_analysis_path / "mpc_programs"
        if base_dir.exists():
            for program_file in base_dir.glob("*.mpc"):
                available['base_programs'].append(program_file.stem)
        
        # 检查场景程序
        for program_file in self.programs_source.glob("*_analysis.mpc"):
            available['scenario_programs'].append(program_file.stem)
        
        return available

if __name__ == "__main__":
    # 测试程序管理器
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    manager = MPCProgramManager()
    
    # 测试编译基础程序
    programs_to_test = ['joint_statistics', 'joint_regression']
    
    for program in programs_to_test:
        print(f"\\nTesting {program}:")
        
        # 准备程序
        success, message = manager.prepare_program_for_execution(program)
        print(f"Preparation: {'SUCCESS' if success else 'FAILED'} - {message}")
        
        # 检查编译状态
        compiled = manager.is_program_compiled(program)
        print(f"Compiled: {'YES' if compiled else 'NO'}")
    
    # 显示可用程序
    available = manager.get_available_programs()
    print(f"\\nAvailable programs: {available}")