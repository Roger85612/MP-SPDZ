#!/usr/bin/env python3
"""
调试数值问题的脚本
分析为什么大数值会导致Y值NaN
"""

import numpy as np

def analyze_income_ranges():
    """分析两种收入范围的数值特征"""
    
    print("="*80)
    print("收入范围数值分析")
    print("="*80)
    
    # 情况1：正常工作的范围
    print("\n情况1（正常）：")
    np.random.seed(42)
    for party_id in range(3):
        base_income = 4500 + party_id * 1000
        incomes = np.random.normal(base_income, 15000, 10)
        incomes = np.clip(incomes, 2000, 15000)
        scaled_incomes = [int(x // 1000) for x in incomes]
        
        print(f"  参与方{party_id}:")
        print(f"    原始收入范围: {np.min(incomes):.0f} - {np.max(incomes):.0f}")
        print(f"    缩放后范围: {np.min(scaled_incomes)} - {np.max(scaled_incomes)}")
        print(f"    缩放后平均值: {np.mean(scaled_incomes):.2f}")
    
    # 情况2：出现NaN的范围
    print("\n情况2（NaN）：")
    np.random.seed(42)
    for party_id in range(3):
        base_income = 45000 + party_id * 10000
        incomes = np.random.normal(base_income, 15000, 10)
        incomes = np.clip(incomes, 20000, 150000)
        scaled_incomes = [int(x // 1000) for x in incomes]
        
        print(f"  参与方{party_id}:")
        print(f"    原始收入范围: {np.min(incomes):.0f} - {np.max(incomes):.0f}")
        print(f"    缩放后范围: {np.min(scaled_incomes)} - {np.max(scaled_incomes)}")
        print(f"    缩放后平均值: {np.mean(scaled_incomes):.2f}")

def analyze_sfix_limits():
    """分析sfix类型的数值限制"""
    print("\n" + "="*80)
    print("sfix类型数值限制分析")
    print("="*80)
    
    # MP-SPDZ中sfix通常使用16位小数精度
    # 整数部分通常是31位或更少
    
    print("sfix类型特征：")
    print("- 通常使用31.16固定点格式（31位整数，16位小数）")
    print("- 有效整数范围：约 ±2^30 = ±1,073,741,824")
    print("- 小数精度：2^(-16) ≈ 0.0000152")
    
    # 检查我们的数值是否超出范围
    max_safe_int = 2**30
    case1_max = 15  # 千美元
    case2_max = 150  # 千美元
    
    print(f"\n数值范围检查：")
    print(f"- sfix最大安全整数值: {max_safe_int:,}")
    print(f"- 情况1最大值: {case1_max}")
    print(f"- 情况2最大值: {case2_max}")
    print(f"- 两种情况都远小于sfix限制")

def analyze_division_precision():
    """分析除法精度问题"""
    print("\n" + "="*80)
    print("除法精度问题分析")
    print("="*80)
    
    # 模拟sfix除法可能遇到的精度问题
    total_count = 30  # 3方 * 10个数据点
    
    # 情况1的和
    np.random.seed(42)
    case1_values = []
    for party_id in range(3):
        base_income = 4500 + party_id * 1000
        incomes = np.random.normal(base_income, 15000, 10)
        incomes = np.clip(incomes, 2000, 15000)
        scaled_incomes = [int(x // 1000) for x in incomes]
        case1_values.extend(scaled_incomes)
    
    case1_sum = sum(case1_values)
    case1_mean = case1_sum / total_count
    
    # 情况2的和
    np.random.seed(42)
    case2_values = []
    for party_id in range(3):
        base_income = 45000 + party_id * 10000
        incomes = np.random.normal(base_income, 15000, 10)
        incomes = np.clip(incomes, 20000, 150000)
        scaled_incomes = [int(x // 1000) for x in incomes]
        case2_values.extend(scaled_incomes)
    
    case2_sum = sum(case2_values)
    case2_mean = case2_sum / total_count
    
    print(f"除法运算分析：")
    print(f"情况1:")
    print(f"  - 总和: {case1_sum}")
    print(f"  - 数据点数: {total_count}")
    print(f"  - 均值: {case1_mean:.6f}")
    print(f"  - 均值是否为整数: {case1_mean == int(case1_mean)}")
    
    print(f"情况2:")
    print(f"  - 总和: {case2_sum}")
    print(f"  - 数据点数: {total_count}")
    print(f"  - 均值: {case2_mean:.6f}")
    print(f"  - 均值是否为整数: {case2_mean == int(case2_mean)}")
    
    # 检查是否存在除法精度问题
    print(f"\n潜在问题：")
    if case2_sum % total_count != 0:
        print(f"⚠️  情况2的除法结果不是整数，可能导致sfix精度问题")
        print(f"   余数: {case2_sum % total_count}")
    
    if case1_sum % total_count != 0:
        print(f"⚠️  情况1的除法结果也不是整数，但为什么没出现问题？")
        print(f"   余数: {case1_sum % total_count}")

def analyze_variance_computation():
    """分析方差计算中的数值问题"""
    print("\n" + "="*80)
    print("方差计算数值问题分析")
    print("="*80)
    
    total_count = 30
    
    # 重现两种情况下的方差计算
    for case_name, config in [("情况1", (4500, 1000, 2000, 15000)), 
                             ("情况2", (45000, 10000, 20000, 150000))]:
        
        base_start, base_step, min_val, max_val = config
        
        np.random.seed(42)
        all_values = []
        for party_id in range(3):
            base_income = base_start + party_id * base_step
            incomes = np.random.normal(base_income, 15000, 10)
            incomes = np.clip(incomes, min_val, max_val)
            scaled_incomes = [int(x // 1000) for x in incomes]
            all_values.extend(scaled_incomes)
        
        sum_y = sum(all_values)
        mean_y = sum_y / total_count
        
        # 计算方差分子
        sum_sq_diff = sum((y - mean_y) ** 2 for y in all_values)
        variance = sum_sq_diff / (total_count - 1)
        
        print(f"\n{case_name}:")
        print(f"  数据: {all_values[:5]}... (显示前5个)")
        print(f"  总和: {sum_y}")
        print(f"  均值: {mean_y:.6f}")
        print(f"  方差分子: {sum_sq_diff:.6f}")
        print(f"  方差: {variance:.6f}")
        print(f"  最大数值: {max(all_values)}")
        print(f"  最大平方差: {max((y - mean_y) ** 2 for y in all_values):.6f}")

if __name__ == "__main__":
    analyze_income_ranges()
    analyze_sfix_limits()
    analyze_division_precision()
    analyze_variance_computation()
    
    print("\n" + "="*80)
    print("结论和建议")
    print("="*80)
    print("1. 两种情况的数值都远小于sfix的理论限制")
    print("2. 问题可能出现在：")
    print("   - sfix除法的精度处理")
    print("   - 中间计算结果的累积误差")
    print("   - MP-SPDZ实现中的特定数值范围限制")
    print("3. 建议的解决方案：")
    print("   - 使用更小的缩放因子（如100而不是1000）")
    print("   - 或者在MPC计算中使用不同的数值表示方法")