
#!/usr/bin/env python3
"""
任务1自动化脚本 - 修复版本
"""

import subprocess
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime

class Ns3Automation:
    def __init__(self, ns3_path="./"):
        self.ns3_path = ns3_path
        self.results = []
        
    def run_simulation(self, packet_size, interval, max_packets=100, simulation_time=10):
        """运行单次仿真并提取结果"""
        cmd = [
            "./ns3", "run", 
            f"scratch/exp2/third_task1 -- --packetSize={packet_size} --interval={interval} "
            f"--maxPackets={max_packets} --simulationTime={simulation_time}"
        ]
        
        print(f"运行仿真: 包大小={packet_size}B, 间隔={interval}s")
        
        try:
            process = subprocess.Popen(
                " ".join(cmd), 
                shell=True, 
                cwd=self.ns3_path,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            # 解析输出结果 - 更新解析逻辑
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
        
        df = pd.DataFrame(self.results)
        df.to_csv(filename, index=False)
        print(f"结果已保存到: {filename}")
        return filename
    
    def plot_results(self):
        """绘制性能图表"""
        if not self.results:
            print("没有可用的结果数据")
            return
        
        df = pd.DataFrame(self.results)
        
        # Create plots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('NS-3 UDP Performance Analysis - Task 1 Results', fontsize=16, fontweight='bold')
        
        # 1. Packet Size vs Throughput
        if len(df) > 0:
            ax1.plot(df['packet_size'], df['throughput'], 'bo-', linewidth=2, markersize=8)
            ax1.set_xlabel('Packet Size (Bytes)')
            ax1.set_ylabel('Throughput (Mbps)')
            ax1.set_title('Packet Size vs Throughput')
            ax1.grid(True, alpha=0.3)
        
        # 2. Packet Size vs Delay
        if len(df) > 0:
            ax2.plot(df['packet_size'], df['delay'], 'ro-', linewidth=2, markersize=8)
            ax2.set_xlabel('Packet Size (Bytes)')
            ax2.set_ylabel('Average Delay (ms)')
            ax2.set_title('Packet Size vs Delay')
            ax2.grid(True, alpha=0.3)
        
        # 3. Packet Interval vs Throughput (if multiple interval data exists)
        interval_groups = df.groupby('interval')
        if len(interval_groups) > 1:
            throughput_by_interval = interval_groups['throughput'].mean()
            ax3.semilogx(throughput_by_interval.index, throughput_by_interval.values, 'go-', linewidth=2, markersize=8)
            ax3.set_xlabel('Packet Interval (s) - Log Scale')
            ax3.set_ylabel('Throughput (Mbps)')
            ax3.set_title('Packet Interval vs Throughput')
            ax3.grid(True, alpha=0.3)
        else:
            ax3.text(0.5, 0.5, 'No multiple interval data', ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('Packet Interval vs Throughput')
        
        # 4. Packet Loss Rate Analysis
        if 'loss_rate' in df.columns and len(df) > 0:
            ax4.bar(df['packet_size'], df['loss_rate'], alpha=0.7, color='orange')
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
        plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
        print(f"图表已保存到: {plot_filename}")
        
        plt.show()
    
    def generate_report(self):
        """生成分析报告"""
        if not self.results:
            print("没有可用的结果数据")
            return
        
        df = pd.DataFrame(self.results)
        
        print("\n" + "=" * 60)
        print("任务1性能分析报告")
        print("=" * 60)
        
        print(f"\n总实验次数: {len(df)}")
        if len(df) > 0:
            print(f"吞吐量范围: {df['throughput'].min():.2f} - {df['throughput'].max():.2f} Mbps")
            print(f"时延范围: {df['delay'].min():.2f} - {df['delay'].max():.2f} ms")
            
            if 'loss_rate' in df.columns:
                print(f"丢包率范围: {df['loss_rate'].min():.2f} - {df['loss_rate'].max():.2f} %")

def main():
    """主函数"""
    automator = Ns3Automation()
    
    # 实验1: 不同包大小的影响
    print("实验1: 测试不同包大小对性能的影响")
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
        automator.plot_results()
        
        print(f"\n所有实验完成！")
        print(f"数据文件: {csv_file}")
        print(f"图表文件: task1_plots_*.png")
    else:
        print("没有收集到任何结果数据")

if __name__ == "__main__":
    main()
