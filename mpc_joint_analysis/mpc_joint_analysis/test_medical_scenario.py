#!/usr/bin/env python3
"""
医疗场景测试脚本
验证增强医疗MPC场景的完整工作流程
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def test_medical_data_generation():
    """测试医疗数据生成"""
    print("🧪 测试1: 医疗数据生成")
    
    try:
        result = subprocess.run([
            "python3", "mpc_data_generator.py", "medical"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("   ✅ 医疗数据生成成功")
            
            # 检查输入文件是否存在
            for i in range(3):
                input_file = Path(f"../Player-Data/Input-P{i}-0")
                if input_file.exists():
                    print(f"   ✅ 输入文件P{i}存在")
                else:
                    print(f"   ❌ 输入文件P{i}缺失")
                    return False
            return True
        else:
            print(f"   ❌ 数据生成失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ 数据生成异常: {e}")
        return False

def test_program_compilation():
    """测试程序编译"""
    print("\n🧪 测试2: MPC程序编译")
    
    try:
        os.chdir("../")  # 切换到MP-SPDZ根目录
        
        result = subprocess.run([
            "python3", "compile.py", "medical_joint_analysis"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("   ✅ 程序编译成功")
            
            # 检查字节码文件是否生成
            bytecode_file = Path("Programs/Bytecode/medical_joint_analysis-0.bc")
            schedule_file = Path("Programs/Schedules/medical_joint_analysis.sch")
            
            if bytecode_file.exists():
                print("   ✅ 字节码文件生成")
            else:
                print("   ❌ 字节码文件缺失")
                return False
                
            if schedule_file.exists():
                print("   ✅ 调度文件生成")
            else:
                print("   ❌ 调度文件缺失")
                return False
                
            return True
        else:
            print(f"   ❌ 编译失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ 编译异常: {e}")
        return False

def test_data_format_validation():
    """测试数据格式验证"""
    print("\n🧪 测试3: 数据格式验证")
    
    try:
        # 检查输入文件格式
        input_file = Path("Player-Data/Input-P0-0")
        
        if not input_file.exists():
            print("   ❌ 输入文件不存在")
            return False
        
        with open(input_file, 'r') as f:
            lines = f.readlines()
        
        # 验证数据行数 (50患者 × 4数据项 = 200行)
        if len(lines) != 200:
            print(f"   ❌ 数据行数错误: 期望200行，实际{len(lines)}行")
            return False
        
        print("   ✅ 数据行数正确 (200行)")
        
        # 验证数据格式 (每4行为一组患者数据)
        for i in range(0, min(20, len(lines)), 4):  # 检查前5个患者
            try:
                age = int(lines[i].strip())
                baseline = int(lines[i+1].strip())
                outcome = int(lines[i+2].strip())
                adverse = int(lines[i+3].strip())
                
                # 验证数据范围
                if not (18 <= age <= 90):
                    print(f"   ❌ 年龄数据超范围: {age}")
                    return False
                    
                if not (0 <= baseline <= 100):
                    print(f"   ❌ 基线评分超范围: {baseline}")
                    return False
                    
                if not (0 <= outcome <= 100):
                    print(f"   ❌ 疗效指标超范围: {outcome}")
                    return False
                    
                if not (0 <= adverse <= 10):
                    print(f"   ❌ 不良反应超范围: {adverse}")
                    return False
                    
            except ValueError as e:
                print(f"   ❌ 数据格式错误: {e}")
                return False
        
        print("   ✅ 数据格式和范围验证通过")
        return True
        
    except Exception as e:
        print(f"   ❌ 格式验证异常: {e}")
        return False

def test_medical_scenario_complete():
    """完整医疗场景测试"""
    print("\n🧪 完整医疗场景测试")
    print("=" * 60)
    
    # 进入正确的工作目录
    os.chdir("/mnt/c/Users/Lenovo/source/repos/MP-SPDZ/mpc_joint_analysis")
    
    # 测试1: 数据生成
    if not test_medical_data_generation():
        print("\n❌ 医疗场景测试失败: 数据生成步骤")
        return False
    
    # 测试2: 程序编译
    if not test_program_compilation():
        print("\n❌ 医疗场景测试失败: 程序编译步骤")
        return False
    
    # 测试3: 数据格式验证
    os.chdir("/mnt/c/Users/Lenovo/source/repos/MP-SPDZ")  # 切回根目录检查文件
    if not test_data_format_validation():
        print("\n❌ 医疗场景测试失败: 数据格式验证步骤")
        return False
    
    print("\n" + "=" * 60)
    print("✅ 医疗场景完整测试通过!")
    print("📋 测试结果摘要:")
    print("   ✅ 医疗数据生成 - 通过")
    print("   ✅ MPC程序编译 - 通过") 
    print("   ✅ 数据格式验证 - 通过")
    print("\n🚀 系统已准备好执行真实的Shamir MPC协议")
    print("📖 运行命令:")
    print("   cd /mnt/c/Users/Lenovo/source/repos/MP-SPDZ")
    print("   ./shamir-party.x -N 3 -p 0 medical_joint_analysis &")
    print("   ./shamir-party.x -N 3 -p 1 medical_joint_analysis &") 
    print("   ./shamir-party.x -N 3 -p 2 medical_joint_analysis &")
    
    return True

def main():
    """主函数"""
    print("🏥 医疗机构联合研究MPC场景测试")
    print("基于mpc_joint_analysis项目框架")
    
    try:
        success = test_medical_scenario_complete()
        
        if success:
            print("\n🎉 所有测试通过！医疗MPC场景设计完成。")
            sys.exit(0)
        else:
            print("\n❌ 测试失败，请检查系统配置。")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()