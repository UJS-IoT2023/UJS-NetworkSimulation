#!/usr/bin/env python3
"""
lab3_tcp_udp_automation.py - TCP vs UDP 协议性能对比自动化测试脚本
"""

import subprocess
import json
import csv
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from datetime import datetime
import os
import sys
import argparse
import re

class TcpUdpComparisonAutomation:
    def __init__(self, output_dir="results_tcp_udp"):
        self.results = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = output_dir
        
        # 创建输出目录
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 设置matplotlib中文字体
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        print(f"TCP vs UDP 对比测试初始化完成，结果将保存到: {output_dir}")
    
    def run_simulation(self, scenario_name, data_rate="10Mbps", delay="2ms", 
                      error_rate=0.0, tcp_algorithm="NewReno", 
                      packet_size=1024, simulation_time=20):
        """运行单个仿真测试"""
        cmd = [
            './cmake-cache/scratch/exp3/ns3.46-lab3_tcp_udp_comparison-default',
            f'--dataRate={data_rate}',
            f'--delay={delay}',
            f'--errorRate={error_rate}',
            f'--tcpAlgorithm={tcp_algorithm}',
            f'--packetSize={packet_size}',
            f'--simulationTime={simulation_time}'
        ]
        
        print(f"运行测试场景: {scenario_name}")
        print(f"  参数: 数据率={data_rate}, 延迟={delay}, 错误率={error_rate}, TCP算法={tcp_algorithm}")
        
        try:
            # 运行仿真
            result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
            
            if result.returncode != 0:
                print(f"  错误: 仿真运行失败，返回码: {result.returncode}")
                print(f"  标准输出: {result.stdout}")
                print(f"  错误输出: {result.stderr}")
                return None
            
            # 解析输出结果
            parsed_results = self.parse_output(result.stdout, scenario_name, 
                                             data_rate, delay, error_rate, 
                                             tcp_algorithm, packet_size)
            
            if parsed_results:
                self.results.extend(parsed_results)
                print(f"  解析成功: 收集到 {len(parsed_results)} 个协议结果")
            
            return parsed_results
            
        except Exception as e:
            print(f"测试失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def parse_output(self, output, scenario_name, data_rate, delay, error_rate, tcp_algorithm, packet_size):
        """从输出中解析性能统计结果"""
        results = []
        
        # 查找性能统计结果部分
        lines = output.split('\n')
        in_results_section = False
        protocol_data = {}
        
        for line in lines:
            if '性能统计结果:' in line:
                in_results_section = True
                continue
            
            if in_results_section:
                if line.strip() == '':
                    continue
                
                # 解析协议行 - 修复解析逻辑
                if '\t' in line and not line.startswith('协议'):
                    parts = line.split('\t')
                    if len(parts) >= 4:
                        protocol = parts[0].strip()
                        
                        # 安全地解析数值，处理可能的空值
                        try:
                            throughput = float(parts[1].strip()) if parts[1].strip() else 0.0
                        except ValueError:
                            throughput = 0.0
                        
                        try:
                            avg_delay = float(parts[2].strip()) if parts[2].strip() else 0.0
                        except ValueError:
                            avg_delay = 0.0
                        
                        try:
                            packet_loss = float(parts[3].strip()) if parts[3].strip() else 0.0
                        except ValueError:
                            packet_loss = 0.0
                        
                        result = {
                            'scenario_name': scenario_name,
                            'protocol': protocol,
                            'data_rate': data_rate,
                            'delay': delay,
                            'error_rate': error_rate,
                            'tcp_algorithm': tcp_algorithm,
                            'packet_size': packet_size,
                            'throughput': throughput,
                            'avg_delay': avg_delay,
                            'packet_loss': packet_loss,
                            'timestamp': datetime.now().isoformat()
                        }
                        results.append(result)
                
                # 查找公平性指数
                if '公平性指数:' in line:
                    match = re.search(r'[\d.]+', line.split(':')[1])
                    if match:
                        fairness_index = float(match.group())
                        # 为所有结果添加公平性指数
                        for result in results:
                            result['fairness_index'] = fairness_index
                    in_results_section = False
        
        return results
    
    def test_ideal_conditions(self):
        """测试理想网络条件"""
        print("\n=== Testing Ideal Network Conditions ===")
        self.run_simulation("Ideal Network", "10Mbps", "2ms", 0.0, "NewReno")
    
    def test_high_delay(self):
        """测试高延迟网络"""
        print("\n=== Testing High Delay Network ===")
        self.run_simulation("High Delay Network", "10Mbps", "50ms", 0.0, "NewReno")
    
    def test_packet_loss(self):
        """测试有丢包网络"""
        print("\n=== Testing Packet Loss Network ===")
        self.run_simulation("Packet Loss Network", "10Mbps", "2ms", 0.01, "NewReno")
    
    def test_low_bandwidth(self):
        """测试低带宽网络"""
        print("\n=== Testing Low Bandwidth Network ===")
        self.run_simulation("Low Bandwidth Network", "1Mbps", "2ms", 0.0, "NewReno")
    
    def test_tcp_algorithms(self):
        """测试不同TCP拥塞控制算法"""
        print("\n=== Testing Different TCP Congestion Control Algorithms ===")
        algorithms = ["NewReno", "Cubic", "Vegas"]
        for algorithm in algorithms:
            self.run_simulation(f"TCP {algorithm} Algorithm", "10Mbps", "2ms", 0.0, algorithm)
    
    def test_mixed_conditions(self):
        """测试混合网络条件"""
        print("\n=== Testing Mixed Network Conditions ===")
        self.run_simulation("Mixed Network Conditions", "5Mbps", "20ms", 0.005, "NewReno")
    
    def run_comprehensive_tests(self):
        """运行全面的测试套件"""
        print("开始TCP vs UDP综合性能对比测试...")
        
        # 先验证基础功能
        result = self.run_simulation("基础验证", "10Mbps", "2ms", 0.0, "NewReno", 1024, 10)
        if not result:
            print("基础功能验证失败，停止测试")
            return
        
        # 运行各种测试场景
        self.test_ideal_conditions()
        self.test_high_delay()
        self.test_packet_loss()
        self.test_low_bandwidth()
        self.test_tcp_algorithms()
        self.test_mixed_conditions()
        
        # 保存结果
        self.save_results()
        
        # 生成图表
        if self.results:
            self.generate_comparison_plots()
        
        print(f"\n综合测试完成！共收集 {len(self.results)} 个协议性能结果")
    
    def save_results(self):
        """保存测试结果到文件"""
        if not self.results:
            print("没有结果可保存")
            return
        
        # JSON格式
        json_filename = os.path.join(self.output_dir, f'tcp_udp_results_{self.timestamp}.json')
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        # CSV格式
        csv_filename = os.path.join(self.output_dir, f'tcp_udp_results_{self.timestamp}.csv')
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            if self.results:
                writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
                writer.writeheader()
                writer.writerows(self.results)
        
        print(f"结果已保存到: {json_filename}, {csv_filename}")
    
    def generate_comparison_plots(self):
        """生成TCP vs UDP性能对比图表"""
        if not self.results:
            print("没有数据可绘制图表")
            return
        
        # 设置图表样式
        sns.set_style("whitegrid")
        plt.figure(figsize=(20, 15))
        
        # 按场景分组数据
        scenarios = {}
        for result in self.results:
            scenario = result['scenario_name']
            if scenario not in scenarios:
                scenarios[scenario] = []
            scenarios[scenario].append(result)
        
        # 1. Throughput Comparison
        plt.subplot(3, 2, 1)
        scenario_names = list(scenarios.keys())
        tcp_throughputs = []
        udp_throughputs = []
        
        for scenario in scenario_names:
            tcp_throughput = next((r['throughput'] for r in scenarios[scenario] if r['protocol'] == 'TCP'), 0)
            udp_throughput = next((r['throughput'] for r in scenarios[scenario] if r['protocol'] == 'UDP'), 0)
            tcp_throughputs.append(tcp_throughput)
            udp_throughputs.append(udp_throughput)
        
        x_pos = np.arange(len(scenario_names))
        width = 0.35
        
        plt.bar(x_pos - width/2, tcp_throughputs, width, label='TCP', color='blue', alpha=0.7)
        plt.bar(x_pos + width/2, udp_throughputs, width, label='UDP', color='red', alpha=0.7)
        plt.xlabel('Test Scenario')
        plt.ylabel('Throughput (Mbps)')
        plt.title('TCP vs UDP Throughput Comparison')
        plt.xticks(x_pos, scenario_names, rotation=45, ha='right')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 2. Delay Comparison
        plt.subplot(3, 2, 2)
        tcp_delays = []
        udp_delays = []
        
        for scenario in scenario_names:
            tcp_delay = next((r['avg_delay'] for r in scenarios[scenario] if r['protocol'] == 'TCP'), 0)
            udp_delay = next((r['avg_delay'] for r in scenarios[scenario] if r['protocol'] == 'UDP'), 0)
            tcp_delays.append(tcp_delay)
            udp_delays.append(udp_delay)
        
        plt.bar(x_pos - width/2, tcp_delays, width, label='TCP', color='blue', alpha=0.7)
        plt.bar(x_pos + width/2, udp_delays, width, label='UDP', color='red', alpha=0.7)
        plt.xlabel('Test Scenario')
        plt.ylabel('Average Delay (ms)')
        plt.title('TCP vs UDP Delay Comparison')
        plt.xticks(x_pos, scenario_names, rotation=45, ha='right')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 3. Packet Loss Comparison
        plt.subplot(3, 2, 3)
        tcp_losses = []
        udp_losses = []
        
        for scenario in scenario_names:
            tcp_loss = next((r['packet_loss'] for r in scenarios[scenario] if r['protocol'] == 'TCP'), 0)
            udp_loss = next((r['packet_loss'] for r in scenarios[scenario] if r['protocol'] == 'UDP'), 0)
            tcp_losses.append(tcp_loss)
            udp_losses.append(udp_loss)
        
        plt.bar(x_pos - width/2, tcp_losses, width, label='TCP', color='blue', alpha=0.7)
        plt.bar(x_pos + width/2, udp_losses, width, label='UDP', color='red', alpha=0.7)
        plt.xlabel('Test Scenario')
        plt.ylabel('Packet Loss Rate (%)')
        plt.title('TCP vs UDP Packet Loss Comparison')
        plt.xticks(x_pos, scenario_names, rotation=45, ha='right')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # 4. TCP Algorithm Performance Comparison
        plt.subplot(3, 2, 4)
        tcp_algorithms = {}
        for result in self.results:
            if result['protocol'] == 'TCP' and 'TCP' in result['scenario_name']:
                algo = result['tcp_algorithm']
                if algo not in tcp_algorithms:
                    tcp_algorithms[algo] = []
                tcp_algorithms[algo].append(result['throughput'])
        
        if tcp_algorithms:
            algo_names = list(tcp_algorithms.keys())
            algo_throughputs = [np.mean(tcp_algorithms[algo]) for algo in algo_names]
            plt.bar(algo_names, algo_throughputs, color=['skyblue', 'lightcoral', 'lightgreen'])
            plt.xlabel('TCP Congestion Control Algorithm')
            plt.ylabel('Average Throughput (Mbps)')
            plt.title('TCP Algorithm Performance Comparison')
            plt.grid(True, alpha=0.3)
        
        # 5. Fairness Index Analysis
        plt.subplot(3, 2, 5)
        fairness_indices = []
        for scenario in scenario_names:
            fairness = next((r['fairness_index'] for r in scenarios[scenario] if 'fairness_index' in r), 0)
            fairness_indices.append(fairness)
        
        plt.bar(scenario_names, fairness_indices, color='orange', alpha=0.7)
        plt.xlabel('Test Scenario')
        plt.ylabel('Fairness Index')
        plt.title('Protocol Fairness Analysis')
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, alpha=0.3)
        plt.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='Perfect Fairness')
        plt.legend()
        
        # 6. Network Condition Impact
        plt.subplot(3, 2, 6)
        # Select key scenarios for network condition impact analysis
        key_scenarios = ['Ideal Network', 'High Delay Network', 'Packet Loss Network', 'Low Bandwidth Network']
        tcp_performance = []
        udp_performance = []
        available_scenarios = []
        
        for scenario in key_scenarios:
            if scenario in scenarios:
                tcp_perf = next((r['throughput'] for r in scenarios[scenario] if r['protocol'] == 'TCP'), 0)
                udp_perf = next((r['throughput'] for r in scenarios[scenario] if r['protocol'] == 'UDP'), 0)
                tcp_performance.append(tcp_perf)
                udp_performance.append(udp_perf)
                available_scenarios.append(scenario)
        
        if available_scenarios:  # Only plot when data is available
            x_pos_small = np.arange(len(available_scenarios))
            plt.plot(x_pos_small, tcp_performance, 'bo-', linewidth=2, markersize=6, label='TCP')
            plt.plot(x_pos_small, udp_performance, 'ro-', linewidth=2, markersize=6, label='UDP')
            plt.xlabel('Network Condition')
            plt.ylabel('Throughput (Mbps)')
            plt.title('Network Condition Impact on Protocol Performance')
            plt.xticks(x_pos_small, available_scenarios, rotation=45, ha='right')
            plt.legend()
            plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plot_filename = os.path.join(self.output_dir, f'tcp_udp_comparison_{self.timestamp}.png')
        plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
        print(f"性能对比图表已保存到: {plot_filename}")
        
        # 生成详细分析报告
        self.generate_detailed_analysis()
    
    def generate_detailed_analysis(self):
        """生成详细的分析报告"""
        if not self.results:
            return
        
        report_filename = os.path.join(self.output_dir, f'tcp_udp_analysis_{self.timestamp}.txt')
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write("=== TCP vs UDP 协议性能对比分析报告 ===\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"测试用例总数: {len(self.results)}\n\n")
            
            # 按协议分组统计
            tcp_results = [r for r in self.results if r['protocol'] == 'TCP']
            udp_results = [r for r in self.results if r['protocol'] == 'UDP']
            
            f.write("协议性能统计:\n")
            if tcp_results:
                tcp_throughputs = [r['throughput'] for r in tcp_results]
                tcp_delays = [r['avg_delay'] for r in tcp_results]
                tcp_losses = [r['packet_loss'] for r in tcp_results]
                
                f.write("TCP协议:\n")
                f.write(f"- 平均吞吐量: {np.mean(tcp_throughputs):.4f} Mbps\n")
                f.write(f"- 平均延迟: {np.mean(tcp_delays):.2f} ms\n")
                f.write(f"- 平均丢包率: {np.mean(tcp_losses):.2f}%\n")
            
            if udp_results:
                udp_throughputs = [r['throughput'] for r in udp_results]
                udp_delays = [r['avg_delay'] for r in udp_results]
                udp_losses = [r['packet_loss'] for r in udp_results]
                
                f.write("UDP协议:\n")
                f.write(f"- 平均吞吐量: {np.mean(udp_throughputs):.4f} Mbps\n")
                f.write(f"- 平均延迟: {np.mean(udp_delays):.2f} ms\n")
                f.write(f"- 平均丢包率: {np.mean(udp_losses):.2f}%\n\n")
            
            # 性能对比分析
            f.write("性能对比分析:\n")
            if tcp_results and udp_results:
                tcp_avg_throughput = np.mean(tcp_throughputs)
                udp_avg_throughput = np.mean(udp_throughputs)
                tcp_avg_delay = np.mean(tcp_delays)
                udp_avg_delay = np.mean(udp_delays)
                
                f.write(f"- TCP吞吐量比UDP高: {((tcp_avg_throughput - udp_avg_throughput) / udp_avg_throughput * 100):.1f}%\n")
                f.write(f"- UDP延迟比TCP低: {((udp_avg_delay - tcp_avg_delay) / tcp_avg_delay * 100):.1f}%\n")
            
            # 场景分析
            f.write("\n场景性能分析:\n")
            scenarios = {}
            for result in self.results:
                scenario = result['scenario_name']
                if scenario not in scenarios:
                    scenarios[scenario] = []
                scenarios[scenario].append(result)
            
            for scenario, results in scenarios.items():
                f.write(f"\n{scenario}:\n")
                tcp_scenario = [r for r in results if r['protocol'] == 'TCP']
                udp_scenario = [r for r in results if r['protocol'] == 'UDP']
                
                if tcp_scenario:
                    tcp = tcp_scenario[0]
                    f.write(f"  TCP: 吞吐量={tcp['throughput']:.4f}Mbps, 延迟={tcp['avg_delay']:.2f}ms, 丢包率={tcp['packet_loss']:.2f}%\n")
                if udp_scenario:
                    udp = udp_scenario[0]
                    f.write(f"  UDP: 吞吐量={udp['throughput']:.4f}Mbps, 延迟={udp['avg_delay']:.2f}ms, 丢包率={udp['packet_loss']:.2f}%\n")
            
            f.write("\n结论与建议:\n")
            f.write("1. TCP在拥塞网络中表现稳定，能够自适应调整发送速率\n")
            f.write("2. UDP在低延迟要求下表现更好，适合实时应用\n")
            f.write("3. 不同TCP算法在不同网络条件下表现各异，需要根据应用场景选择\n")
            f.write("4. 公平性指数反映了协议间的资源分配公平性，接近1表示更公平\n")
        
        print(f"详细分析报告已保存到: {report_filename}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='TCP vs UDP 协议性能对比自动化测试')
    parser.add_argument('--mode', choices=['basic', 'comprehensive'], 
                       default='comprehensive', help='测试模式: basic(基础), comprehensive(全面)')
    parser.add_argument('--output', default='results_tcp_udp', help='输出目录')
    
    args = parser.parse_args()
    
    automation = TcpUdpComparisonAutomation(output_dir=args.output)
    
    print("=== TCP vs UDP 协议性能对比自动化测试 ===")
    print(f"测试模式: {args.mode}")
    print(f"输出目录: {args.output}")
    
    if args.mode == 'comprehensive':
        automation.run_comprehensive_tests()
    else:
        # 基础测试只运行几个关键场景
        print("运行基础测试...")
        automation.run_simulation("理想网络条件", "10Mbps", "2ms", 0.0, "NewReno")
        automation.run_simulation("有丢包网络", "10Mbps", "2ms", 0.01, "NewReno")
        automation.save_results()
        if automation.results:
            automation.generate_comparison_plots()
    
    if automation.results:
        print(f"\n测试成功完成！共收集 {len(automation.results)} 个协议性能结果")
    else:
        print(f"\n测试完成，但没有收集到有效结果")
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()
