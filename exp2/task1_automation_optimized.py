
#!/usr/bin/env python3
"""
任务1自动化脚本 - 优化参数版本
"""

import subprocess
import os
import sys
import csv
from datetime import datetime

# 尝试导入matplotlib，如果失败则使用纯文本模式
try:
    import matplotlib
    # 使用非交互式后端
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 用黑体或DejaVu Sans
    plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号
    HAS_MATPLOTLIB = True
except (ImportError, AttributeError) as e:
    print(f"警告: 无法导入matplotlib, 将使用纯文本模式。错误: {e}")
    HAS_MATPLOTLIB = False

class Ns3Automation:
    def __init__(self, ns3_path="./"):
        self.ns3_path = ns3_path
        self.results = []
        
    def run_simulation(self, packet_size, interval, max_packets=1000, simulation_time=30):
        """运行单次仿真并提取结果"""
        # 修复：在--后面传递参数
        cmd = [
            "./ns3", "run", "scratch/exp2/third_task1", "--",
            f"--packetSize={packet_size}",
            f"--interval={interval}",
            f"--maxPackets={max_packets}",
            f"--simulationTime={simulation_time}"
        ]
        
        print(f"运行仿真: 包大小={packet_size}B, 间隔={interval}s")
        
        try:
            process = subprocess.Popen(
                cmd,  # 使用列表而不是字符串，避免shell解析问题
                cwd=self.ns3_path,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            # 解析输出结果
            for line in stdout.split('\n'):
                # 跳过表头和空行
                if line.startswith('PACKET_SIZE') or not line.strip():
                    continue
                
                # 解析CSV数据行
                parts = line.split(',')
                if len(parts) == 5:
                    try:
                        result = {
                            'packet_size': int(parts[0]),
                            'interval': float(parts[1]),
                            'throughput': float(parts[2]),
                            'delay': float(parts[3]),
                            'loss_rate': float(parts[4])
                        }
                        self.results.append(result)
                        print(f"  结果: 吞吐量={result['throughput']:.2f} Mbps, "
                              f"时延={result['delay']:.2f} ms, "
                              f"丢包率={result['loss_rate']:.2f}%")
                        return result
                    except ValueError as e:
                        print(f"解析结果时出错: {e}, 行内容: {line}")
                        continue
            
            if stderr:
                print(f"错误输出: {stderr}")
                
        except Exception as e:
            print(f"运行仿真时出错: {e}")
            
        return None
    
    def sweep_packet_size(self, packet_sizes, interval=0.1):
        """扫描不同的包大小"""
        print("=" * 60)
        print("开始包大小扫描实验")
        print("=" * 60)
        
        for size in packet_sizes:
            self.run_simulation(packet_size=size, interval=interval, 
                              max_packets=500, simulation_time=20)
    
    def sweep_interval(self, packet_size=1024, intervals=None):
        """扫描不同的发包间隔"""
        if intervals is None:
            intervals = [0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2]
            
        print("=" * 60)
        print("开始发包间隔扫描实验")
        print("=" * 60)
        
        for interval in intervals:
            self.run_simulation(packet_size=packet_size, interval=interval,
                              max_packets=1000, simulation_time=30)
    
    def save_results(self, filename=None):
        """保存结果到CSV文件"""
        if not self.results:
            print("没有结果数据可保存")
            return None
            
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"task1_results_{timestamp}.csv"
        
        # 使用csv模块保存结果
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['packet_size', 'interval', 'throughput', 'delay', 'loss_rate']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in self.results:
                writer.writerow(result)
        
        print(f"结果已保存到: {filename}")
        return filename
    
    def plot_results_simple(self):
        """简化的绘图函数"""
        if not HAS_MATPLOTLIB:
            print("无法绘图: matplotlib不可用")
            return
            
        if not self.results:
            print("没有可用的结果数据")
            return
        
        try:
            # 创建图表
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
            fig.suptitle('NS-3 UDP Performance Analysis - Task 1 Results', fontsize=14, fontweight='bold')
            
            # 提取数据
            packet_sizes = [r['packet_size'] for r in self.results]
            throughputs = [r['throughput'] for r in self.results]
            delays = [r['delay'] for r in self.results]
            intervals = [r['interval'] for r in self.results]
            loss_rates = [r['loss_rate'] for r in self.results]
            
            # 1. Packet Size vs Throughput
            unique_sizes = sorted(set(packet_sizes))
            if len(unique_sizes) > 1:
                # 计算每个包大小的平均吞吐量
                avg_throughputs = []
                for size in unique_sizes:
                    size_throughputs = [t for s, t in zip(packet_sizes, throughputs) if s == size]
                    avg_throughputs.append(sum(size_throughputs) / len(size_throughputs))
                
                ax1.plot(unique_sizes, avg_throughputs, 'bo-', linewidth=2, markersize=6)
                ax1.set_xlabel('Packet Size (Bytes)')
                ax1.set_ylabel('Throughput (Mbps)')
                ax1.set_title('Packet Size vs Throughput')
                ax1.grid(True, alpha=0.3)
            else:
                ax1.text(0.5, 0.5, 'No multiple packet size data', ha='center', va='center', transform=ax1.transAxes)
                ax1.set_title('Packet Size vs Throughput')
            
            # 2. Packet Size vs Delay
            if len(unique_sizes) > 1:
                # 计算每个包大小的平均时延
                avg_delays = []
                for size in unique_sizes:
                    size_delays = [d for s, d in zip(packet_sizes, delays) if s == size]
                    avg_delays.append(sum(size_delays) / len(size_delays))
                
                ax2.plot(unique_sizes, avg_delays, 'ro-', linewidth=2, markersize=6)
                ax2.set_xlabel('Packet Size (Bytes)')
                ax2.set_ylabel('Average Delay (ms)')
                ax2.set_title('Packet Size vs Delay')
                ax2.grid(True, alpha=0.3)
            else:
                ax2.text(0.5, 0.5, 'No multiple packet size data', ha='center', va='center', transform=ax2.transAxes)
                ax2.set_title('Packet Size vs Delay')
            
            # 3. Interval vs Throughput
            unique_intervals = sorted(set(intervals))
            if len(unique_intervals) > 1:
                # 计算每个间隔的平均吞吐量
                avg_interval_throughputs = []
                for interval in unique_intervals:
                    interval_throughputs = [t for i, t in zip(intervals, throughputs) if i == interval]
                    avg_interval_throughputs.append(sum(interval_throughputs) / len(interval_throughputs))
                
                ax3.semilogx(unique_intervals, avg_interval_throughputs, 'go-', linewidth=2, markersize=6)
                ax3.set_xlabel('Packet Interval (s) - Log Scale')
                ax3.set_ylabel('Throughput (Mbps)')
                ax3.set_title('Interval vs Throughput')
                ax3.grid(True, alpha=0.3)
            else:
                ax3.text(0.5, 0.5, 'No multiple interval data', ha='center', va='center', transform=ax3.transAxes)
                ax3.set_title('Interval vs Throughput')
            
            # 4. Packet Loss Analysis
            if len(unique_sizes) > 1 and any(loss_rates):
                # 计算每个包大小的平均丢包率
                avg_losses = []
                for size in unique_sizes:
                    size_losses = [l for s, l in zip(packet_sizes, loss_rates) if s == size]
                    avg_losses.append(sum(size_losses) / len(size_losses))
                
                ax4.bar(unique_sizes, avg_losses, alpha=0.7, color='orange', width=50)
                ax4.set_xlabel('Packet Size (Bytes)')
                ax4.set_ylabel('Packet Loss Rate (%)')
                ax4.set_title('Packet Size vs Loss Rate')
                ax4.grid(True, alpha=0.3)
            else:
                ax4.text(0.5, 0.5, 'No packet loss data', ha='center', va='center', transform=ax4.transAxes)
                ax4.set_title('Packet Size vs Loss Rate')
            
            plt.tight_layout()
            
            # 保存图表
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plot_filename = f"task1_plots_{timestamp}.png"
            plt.savefig(plot_filename, dpi=200, bbox_inches='tight')
            print(f"图表已保存到: {plot_filename}")
            
            # 关闭图表释放内存
            plt.close()
            
        except Exception as e:
            print(f"绘图时出错: {e}")
            print("将继续生成数据文件...")
    
    def generate_report(self):
        """生成分析报告"""
        if not self.results:
            print("没有可用的结果数据")
            return
        
        print("\n" + "=" * 60)
        print("任务1性能分析报告")
        print("=" * 60)
        
        print(f"\n总实验次数: {len(self.results)}")
        
        if self.results:
            throughputs = [r['throughput'] for r in self.results]
            delays = [r['delay'] for r in self.results]
            
            print(f"吞吐量范围: {min(throughputs):.2f} - {max(throughputs):.2f} Mbps")
            print(f"时延范围: {min(delays):.2f} - {max(delays):.2f} ms")
            
            if 'loss_rate' in self.results[0]:
                loss_rates = [r['loss_rate'] for r in self.results]
                print(f"丢包率范围: {min(loss_rates):.2f} - {max(loss_rates):.2f} %")
            
            # 按包大小分组统计
            size_groups = {}
            for result in self.results:
                size = result['packet_size']
                if size not in size_groups:
                    size_groups[size] = []
                size_groups[size].append(result)
            
            if len(size_groups) > 1:
                print("\n包大小影响分析:")
                for size in sorted(size_groups.keys()):
                    group = size_groups[size]
                    avg_throughput = sum(r['throughput'] for r in group) / len(group)
                    avg_delay = sum(r['delay'] for r in group) / len(group)
                    print(f"  包大小 {size}B: 平均吞吐量={avg_throughput:.2f} Mbps, 平均时延={avg_delay:.2f} ms")
            
            # 按间隔分组统计
            interval_groups = {}
            for result in self.results:
                interval = result['interval']
                if interval not in interval_groups:
                    interval_groups[interval] = []
                interval_groups[interval].append(result)
            
            if len(interval_groups) > 1:
                print("\n发包间隔影响分析:")
                for interval in sorted(interval_groups.keys()):
                    group = interval_groups[interval]
                    avg_throughput = sum(r['throughput'] for r in group) / len(group)
                    print(f"  间隔 {interval}s: 平均吞吐量={avg_throughput:.2f} Mbps")

def main():
    """主函数"""
    print("NS-3 任务1自动化实验")
    print("=" * 40)
    print("优化参数: 增加仿真时间和包数量以获得更好的统计结果")
    
    # 检查环境
    if HAS_MATPLOTLIB:
        print("✓ matplotlib 可用")
    else:
        print("✗ matplotlib 不可用，将只生成数据文件")
    
    automator = Ns3Automation()
    
    # 实验1: 不同包大小的影响 - 使用更长的仿真时间
    print("\n实验1: 测试不同包大小对性能的影响")
    packet_sizes = [64, 128, 256, 512, 1024, 1500]
    automator.sweep_packet_size(packet_sizes, interval=0.1)
    
    # 实验2: 不同发包间隔的影响 - 使用更广泛的间隔范围
    print("\n实验2: 测试不同发包间隔对性能的影响")
    intervals = [0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5]
    automator.sweep_interval(packet_size=1024, intervals=intervals)
    
    # 保存结果和生成报告
    if automator.results:
        csv_file = automator.save_results()
        automator.generate_report()
        
        # 尝试绘图
        automator.plot_results_simple()
        
        print(f"\n" + "=" * 60)
        print("所有实验完成！")
        print(f"数据文件: {csv_file}")
        
        if HAS_MATPLOTLIB:
            print("图表文件: task1_plots_*.png")
        else:
            print("提示: 要生成图表，请修复matplotlib安装")
    else:
        print("没有收集到任何结果数据")

if __name__ == "__main__":
    main()
    
    
