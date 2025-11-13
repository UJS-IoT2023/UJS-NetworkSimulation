#!/usr/bin/env python3
"""
Task 1 Automation Script - Fixed parameter passing issues
"""

import subprocess
import os
import sys
import csv
from datetime import datetime

# Try to import matplotlib, use text-only mode if failed
try:
    import matplotlib
    # Use non-interactive backend
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except (ImportError, AttributeError) as e:
    print(f"Warning: Cannot import matplotlib, will use text-only mode. Error: {e}")
    HAS_MATPLOTLIB = False

class Ns3Automation:
    def __init__(self, ns3_path="./"):
        self.ns3_path = ns3_path
        self.results = []
        
    def run_simulation(self, packet_size, interval, max_packets=100, simulation_time=10):
        """Run single simulation and extract results"""
        # Fix: pass parameters after --
        cmd = [
            "./ns3", "run", "scratch/exp2/third_task1", "--",
            f"--packetSize={packet_size}",
            f"--interval={interval}",
            f"--maxPackets={max_packets}",
            f"--simulationTime={simulation_time}"
        ]
        
        print(f"Running simulation: packet_size={packet_size}B, interval={interval}s")
        
        try:
            process = subprocess.Popen(
                cmd,  # Use list instead of string to avoid shell parsing issues
                cwd=self.ns3_path,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            # Parse output results
            for line in stdout.split('\n'):
                # Skip header and empty lines
                if line.startswith('PACKET_SIZE') or not line.strip():
                    continue
                
                # Parse CSV data row
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
                        print(f"  Result: throughput={result['throughput']:.2f} Mbps, "
                              f"delay={result['delay']:.2f} ms, "
                              f"loss_rate={result['loss_rate']:.2f}%")
                        return result
                    except ValueError as e:
                        print(f"Error parsing result: {e}, line content: {line}")
                        continue
            
            if stderr:
                print(f"Error output: {stderr}")
                
        except Exception as e:
            print(f"Error running simulation: {e}")
            
        return None
    
    def sweep_packet_size(self, packet_sizes, interval=0.1):
        """扫描不同的包大小"""
        print("=" * 60)
        print("开始包大小扫描实验")
        print("=" * 60)
        
        for size in packet_sizes:
            self.run_simulation(packet_size=size, interval=interval)
    
    def sweep_interval(self, packet_size=1024, intervals=None):
        """扫描不同的发包间隔"""
        if intervals is None:
            intervals = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0]
            
        print("=" * 60)
        print("开始发包间隔扫描实验")
        print("=" * 60)
        
        for interval in intervals:
            self.run_simulation(packet_size=packet_size, interval=interval)
    
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
            # Create plots
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
            fig.suptitle('NS-3 UDP Performance Analysis - Task 1 Results', fontsize=14, fontweight='bold')
            
            # Extract data
            packet_sizes = [r['packet_size'] for r in self.results]
            throughputs = [r['throughput'] for r in self.results]
            delays = [r['delay'] for r in self.results]
            intervals = [r['interval'] for r in self.results]
            loss_rates = [r['loss_rate'] for r in self.results]
            
            # 1. Packet Size vs Throughput
            unique_sizes = sorted(set(packet_sizes))
            if len(unique_sizes) > 1:
                # Calculate average throughput for each packet size
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
                # Calculate average delay for each packet size
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
            
            # 3. Packet Interval vs Throughput
            unique_intervals = sorted(set(intervals))
            if len(unique_intervals) > 1:
                # Calculate average throughput for each interval
                avg_interval_throughputs = []
                for interval in unique_intervals:
                    interval_throughputs = [t for i, t in zip(intervals, throughputs) if i == interval]
                    avg_interval_throughputs.append(sum(interval_throughputs) / len(interval_throughputs))
                
                ax3.plot(unique_intervals, avg_interval_throughputs, 'go-', linewidth=2, markersize=6)
                ax3.set_xlabel('Packet Interval (s)')
                ax3.set_ylabel('Throughput (Mbps)')
                ax3.set_title('Packet Interval vs Throughput')
                ax3.grid(True, alpha=0.3)
            else:
                ax3.text(0.5, 0.5, 'No multiple interval data', ha='center', va='center', transform=ax3.transAxes)
                ax3.set_title('Packet Interval vs Throughput')
            
            # 4. Packet Loss Rate Analysis
            if len(unique_sizes) > 1 and any(loss_rates):
                # Calculate average loss rate for each packet size
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
    
    # 检查环境
    if HAS_MATPLOTLIB:
        print("✓ matplotlib 可用")
    else:
        print("✗ matplotlib 不可用，将只生成数据文件")
    
    automator = Ns3Automation()
    
    # 实验1: 不同包大小的影响
    print("\n实验1: 测试不同包大小对性能的影响")
    packet_sizes = [64, 128, 256, 512, 1024]
    automator.sweep_packet_size(packet_sizes, interval=0.1)
    
    # 实验2: 不同发包间隔的影响  
    print("\n实验2: 测试不同发包间隔对性能的影响")
    intervals = [0.01, 0.02, 0.05, 0.1, 0.2]
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
