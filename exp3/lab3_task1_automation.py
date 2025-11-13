
#!/usr/bin/env python3
"""
lab3_task1_automation.py - 网络传输协议仿真自动化测试脚本
修复输出解析问题，正确处理包含百分号的字符串
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

class NetworkTestAutomation:
    def __init__(self, output_dir="results"):
        self.results = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = output_dir
        
        # 创建输出目录
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 设置matplotlib中文字体
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        print(f"自动化测试初始化完成，结果将保存到: {output_dir}")
    
    def run_simulation(self, packet_size=1024, max_packets=100, 
                      simulation_time=20, data_rate="5Mbps", delay="2ms"):
        """运行单个仿真测试"""
        # 参数放在 -- 后面
        cmd = [
            './ns3', 'run',
            'scratch/exp3/lab3_task1',
            '--',
            f'--packetSize={packet_size}',
            f'--maxPackets={max_packets}',
            f'--simulationTime={simulation_time}',
            f'--dataRate={data_rate}',
            f'--delay={delay}'
        ]
        
        print(f"运行测试: 数据包大小={packet_size}B, 最大包数={max_packets}, 数据率={data_rate}, 延迟={delay}")
        
        try:
            # 运行仿真
            result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
            
            if result.returncode != 0:
                print(f"  错误: 仿真运行失败，返回码: {result.returncode}")
                print(f"  标准输出: {result.stdout}")
                print(f"  错误输出: {result.stderr}")
                return None
            
            # 调试：打印原始输出
            print(f"  原始输出前500字符: {result.stdout[:500]}")
            
            # 解析输出结果
            throughput = self.parse_throughput(result.stdout)
            avg_delay = self.parse_delay(result.stdout)
            packet_loss = self.parse_packet_loss(result.stdout)
            received_packets = self.parse_received_packets(result.stdout)
            total_bytes = self.parse_total_bytes(result.stdout)
            
            test_result = {
                'packet_size': packet_size,
                'max_packets': max_packets,
                'simulation_time': simulation_time,
                'data_rate': data_rate,
                'delay': delay,
                'throughput': throughput,
                'avg_delay': avg_delay,
                'packet_loss': packet_loss,
                'received_packets': received_packets,
                'total_bytes': total_bytes,
                'timestamp': datetime.now().isoformat()
            }
            
            self.results.append(test_result)
            print(f"  解析结果: 吞吐量={throughput:.4f}Mbps, 延迟={avg_delay:.2f}ms, 丢包率={packet_loss:.1f}%")
            
            return test_result
            
        except Exception as e:
            print(f"测试失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def parse_throughput(self, output):
        """从输出中解析吞吐量"""
        for line in output.split('\n'):
            if '网络吞吐量:' in line:
                # 提取数字部分
                match = re.search(r'[\d.]+', line.split(':')[1])
                if match:
                    return float(match.group())
        return 0.0
    
    def parse_delay(self, output):
        """从输出中解析平均延迟"""
        for line in output.split('\n'):
            if '平均延迟:' in line:
                # 提取数字部分
                match = re.search(r'[\d.]+', line.split(':')[1])
                if match:
                    return float(match.group())
        return 0.0
    
    def parse_packet_loss(self, output):
        """从输出中解析丢包率 - 修复百分号处理"""
        for line in output.split('\n'):
            if '丢包率:' in line:
                # 提取数字部分，去掉百分号
                value_str = line.split(':')[1].strip()
                # 使用正则表达式提取数字
                match = re.search(r'([\d.]+)', value_str)
                if match:
                    return float(match.group(1))
        return 0.0
    
    def parse_received_packets(self, output):
        """从输出中解析接收数据包数"""
        for line in output.split('\n'):
            if '接收数据包总数:' in line:
                # 提取数字部分
                match = re.search(r'\d+', line.split(':')[1])
                if match:
                    return int(match.group())
        return 0
    
    def parse_total_bytes(self, output):
        """从输出中解析总接收字节数"""
        for line in output.split('\n'):
            if '总接收字节数:' in line:
                # 提取数字部分
                match = re.search(r'\d+', line.split(':')[1])
                if match:
                    return int(match.group())
        return 0
    
    def test_packet_sizes(self):
        """测试不同数据包大小对性能的影响"""
        print("\n=== 测试不同数据包大小 ===")
        packet_sizes = [512, 1024, 2048]
        for size in packet_sizes:
            self.run_simulation(packet_size=size, max_packets=100)
    
    def test_data_rates(self):
        """测试不同数据速率对性能的影响"""
        print("\n=== 测试不同数据速率 ===")
        data_rates = ["1Mbps", "5Mbps", "10Mbps"]
        for rate in data_rates:
            self.run_simulation(data_rate=rate)
    
    def test_delays(self):
        """测试不同链路延迟对性能的影响"""
        print("\n=== 测试不同链路延迟 ===")
        delays = ["2ms", "10ms", "50ms"]
        for delay in delays:
            self.run_simulation(delay=delay)
    
    def run_basic_test(self):
        """基础测试 - 只运行最基本的测试"""
        print("运行基础测试...")
        
        # 先测试一个最简单的案例来验证
        print("首先验证基础功能...")
        result = self.run_simulation(packet_size=1024, max_packets=50, simulation_time=10)
        
        if result:
            print("基础功能验证成功！继续更多测试...")
            # 只运行3个最基本的测试
            self.run_simulation(packet_size=512)
            self.run_simulation(packet_size=2048)
        else:
            print("基础功能验证失败，请检查代码和参数")
        
        self.save_results()
        if self.results:
            self.generate_plots()
    
    def run_quick_test(self):
        """快速测试 - 运行少量关键测试"""
        print("运行快速测试...")
        
        # 先验证基础功能
        print("首先验证基础功能...")
        result = self.run_simulation(packet_size=1024, max_packets=50, simulation_time=10)
        
        if not result:
            print("基础功能验证失败，停止测试")
            return
        
        # 测试关键参数组合
        test_cases = [
            {'packet_size': 512},
            {'packet_size': 2048},
            {'data_rate': '1Mbps'},
            {'data_rate': '10Mbps'},
            {'delay': '10ms'},
        ]
        
        for case in test_cases:
            self.run_simulation(**case)
        
        self.save_results()
        if self.results:
            self.generate_plots()
    
    def run_comprehensive_tests(self):
        """运行全面的测试套件"""
        print("开始综合性能测试...")
        
        # 先验证基础功能
        result = self.run_simulation(packet_size=1024, max_packets=50, simulation_time=10)
        if not result:
            print("基础功能验证失败，停止测试")
            return
        
        self.test_packet_sizes()
        self.test_data_rates()
        self.test_delays()
        
        # 保存结果
        self.save_results()
        
        # 生成图表
        if self.results:
            self.generate_plots()
        
        print(f"\n综合测试完成！共运行 {len(self.results)} 个测试用例")
    
    def save_results(self):
        """保存测试结果到文件"""
        if not self.results:
            print("没有结果可保存")
            return
        
        # JSON格式
        json_filename = os.path.join(self.output_dir, f'results_{self.timestamp}.json')
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        # CSV格式
        csv_filename = os.path.join(self.output_dir, f'results_{self.timestamp}.csv')
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            if self.results:
                writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
                writer.writeheader()
                writer.writerows(self.results)
        
        print(f"结果已保存到: {json_filename}, {csv_filename}")
    
    def generate_plots(self):
        """生成性能分析图表"""
        if not self.results:
            print("没有数据可绘制图表")
            return
        
        # 设置图表样式
        sns.set_style("whitegrid")
        plt.figure(figsize=(15, 10))
        
        # 1. 数据包大小 vs 性能指标
        packet_size_results = [r for r in self.results if r.get('max_packets', 100) == 100 and r.get('data_rate', '5Mbps') == "5Mbps" and r.get('delay', '2ms') == "2ms"]
        packet_size_results.sort(key=lambda x: x['packet_size'])
        
        if packet_size_results:
            sizes = [r['packet_size'] for r in packet_size_results]
            
            plt.subplot(2, 2, 1)
            throughputs = [r['throughput'] for r in packet_size_results]
            plt.plot(sizes, throughputs, 'bo-', linewidth=2, markersize=6)
            plt.xlabel('Packet Size (bytes)')
            plt.ylabel('Throughput (Mbps)')
            plt.title('Packet Size vs Throughput')
            plt.grid(True, alpha=0.3)
            
            plt.subplot(2, 2, 2)
            delays = [r['avg_delay'] for r in packet_size_results]
            plt.plot(sizes, delays, 'ro-', linewidth=2, markersize=6)
            plt.xlabel('Packet Size (bytes)')
            plt.ylabel('Average Delay (ms)')
            plt.title('Packet Size vs Delay')
            plt.grid(True, alpha=0.3)
        
        # 2. 数据速率 vs 性能指标
        data_rate_results = [r for r in self.results if r.get('packet_size', 1024) == 1024 and r.get('max_packets', 100) == 100 and r.get('delay', '2ms') == "2ms"]
        # 按数据速率排序
        rate_order = {"1Mbps": 1, "5Mbps": 2, "10Mbps": 3}
        data_rate_results.sort(key=lambda x: rate_order.get(x.get('data_rate', '5Mbps'), 0))
        
        if data_rate_results:
            rates = [r['data_rate'] for r in data_rate_results]
            x_pos = np.arange(len(rates))
            
            plt.subplot(2, 2, 3)
            throughputs = [r['throughput'] for r in data_rate_results]
            plt.bar(x_pos, throughputs, color='skyblue', alpha=0.7)
            plt.xlabel('Data Rate')
            plt.ylabel('Throughput (Mbps)')
            plt.title('Data Rate vs Throughput')
            plt.xticks(x_pos, rates, rotation=45)
            plt.grid(True, alpha=0.3)
            
            plt.subplot(2, 2, 4)
            delays = [r['avg_delay'] for r in data_rate_results]
            plt.bar(x_pos, delays, color='lightcoral', alpha=0.7)
            plt.xlabel('Data Rate')
            plt.ylabel('Average Delay (ms)')
            plt.title('Data Rate vs Delay')
            plt.xticks(x_pos, rates, rotation=45)
            plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plot_filename = os.path.join(self.output_dir, f'performance_analysis_{self.timestamp}.png')
        plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
        print(f"性能图表已保存到: {plot_filename}")
        
        # 生成详细分析报告
        self.generate_detailed_analysis()
    
    def generate_detailed_analysis(self):
        """生成详细的分析报告"""
        if not self.results:
            return
        
        report_filename = os.path.join(self.output_dir, f'analysis_report_{self.timestamp}.txt')
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write("=== 网络传输协议仿真分析报告 ===\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"测试用例总数: {len(self.results)}\n\n")
            
            # 找出最佳性能配置
            if self.results:
                best_throughput = max(self.results, key=lambda x: x['throughput'])
                best_delay = min(self.results, key=lambda x: x['avg_delay'])
                best_loss = min(self.results, key=lambda x: x['packet_loss'])
                
                f.write("最佳性能配置:\n")
                f.write(f"- 最高吞吐量: {best_throughput['throughput']:.4f} Mbps " 
                       f"(包大小: {best_throughput['packet_size']}B, 数据率: {best_throughput['data_rate']})\n")
                f.write(f"- 最低延迟: {best_delay['avg_delay']:.2f} ms "
                       f"(包大小: {best_delay['packet_size']}B, 数据率: {best_delay['data_rate']})\n")
                f.write(f"- 最低丢包率: {best_loss['packet_loss']:.1f}% "
                       f"(包大小: {best_loss['packet_size']}B, 数据率: {best_loss['data_rate']})\n\n")
                
                # 统计分析
                throughputs = [r['throughput'] for r in self.results]
                delays = [r['avg_delay'] for r in self.results]
                losses = [r['packet_loss'] for r in self.results]
                
                f.write("性能统计:\n")
                f.write(f"- 吞吐量范围: {min(throughputs):.4f} - {max(throughputs):.4f} Mbps\n")
                f.write(f"- 延迟范围: {min(delays):.2f} - {max(delays):.2f} ms\n")
                f.write(f"- 丢包率范围: {min(losses):.1f} - {max(losses):.1f}%\n")
                if throughputs:
                    f.write(f"- 平均吞吐量: {np.mean(throughputs):.4f} Mbps\n")
                if delays:
                    f.write(f"- 平均延迟: {np.mean(delays):.2f} ms\n")
                if losses:
                    f.write(f"- 平均丢包率: {np.mean(losses):.1f}%\n\n")
                
                f.write("配置建议:\n")
                f.write("1. 对于需要高吞吐量的应用，建议使用较大的数据包大小和较高的数据速率\n")
                f.write("2. 对于实时性要求高的应用，建议选择较低的链路延迟配置\n")
                f.write("3. 在拥塞网络中，适当减少数据包大小可以降低丢包率\n")
        
        print(f"详细分析报告已保存到: {report_filename}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='网络传输协议仿真自动化测试')
    parser.add_argument('--mode', choices=['basic', 'quick', 'comprehensive'], 
                       default='basic', help='测试模式: basic(基础), quick(快速), comprehensive(全面)')
    parser.add_argument('--output', default='results', help='输出目录')
    
    args = parser.parse_args()
    
    automation = NetworkTestAutomation(output_dir=args.output)
    
    print("=== 网络传输协议仿真自动化测试 ===")
    print(f"测试模式: {args.mode}")
    print(f"输出目录: {args.output}")
    
    if args.mode == 'basic':
        automation.run_basic_test()
    elif args.mode == 'quick':
        automation.run_quick_test()
    elif args.mode == 'comprehensive':
        automation.run_comprehensive_tests()
    
    if automation.results:
        print(f"\n测试成功完成！共收集 {len(automation.results)} 个有效结果")
    else:
        print(f"\n测试完成，但没有收集到有效结果")
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()
