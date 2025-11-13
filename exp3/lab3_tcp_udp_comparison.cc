/* lab3_tcp_udp_comparison.cc - TCP vs UDP 协议性能对比研究
 * 实验要求：
 * 1. 创建两个节点，节点0作为客户端，节点1作为服务器
 * 2. 在节点1上安装TCP和UDP服务器
 * 3. 在节点0上安装TCP和UDP客户端，并同时启动两种流量
 * 4. 测量两种协议的吞吐量、延迟、丢包率等
 * 5. 改变网络条件（如引入丢包、延迟、带宽限制）重复测试
 * 6. 测试不同的TCP拥塞控制算法（如NewReno、Cubic等）与UDP的对比
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/error-model.h"
#include <iostream>
#include <fstream>
#include <vector>
#include <map>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("TcpUdpComparison");

// 全局统计结构
struct ProtocolStats {
    uint64_t totalBytesReceived;
    uint64_t totalPacketsReceived;
    double totalDelay;
    uint64_t totalPacketsSent;
    double startTime;
    double stopTime;
    
    ProtocolStats() : totalBytesReceived(0), totalPacketsReceived(0), 
                     totalDelay(0.0), totalPacketsSent(0), 
                     startTime(0.0), stopTime(0.0) {}
};

// 全局统计变量
std::map<std::string, ProtocolStats> protocolStats;

/**
 * @brief TCP 服务器应用，用于统计TCP性能
 */
class TcpStatsServer : public Application {
public:
    TcpStatsServer();
    virtual ~TcpStatsServer();

    static TypeId GetTypeId(void);
    
    void Setup(uint16_t port);

protected:
    virtual void DoDispose(void);

private:
    virtual void StartApplication(void);
    virtual void StopApplication(void);
    
    void HandleAccept(Ptr<Socket> socket, const Address& from);
    void HandleRead(Ptr<Socket> socket);
    
    uint16_t m_port;
    Ptr<Socket> m_socket;
    std::vector<Ptr<Socket>> m_connections;
};

TcpStatsServer::TcpStatsServer() : m_port(0) {
}

TcpStatsServer::~TcpStatsServer() {
}

TypeId TcpStatsServer::GetTypeId(void) {
    static TypeId tid = TypeId("TcpStatsServer")
        .SetParent<Application>()
        .SetGroupName("Applications")
        .AddConstructor<TcpStatsServer>();
    return tid;
}

void TcpStatsServer::Setup(uint16_t port) {
    m_port = port;
}

void TcpStatsServer::DoDispose(void) {
    NS_LOG_FUNCTION(this);
    for (auto& socket : m_connections) {
        socket->Close();
    }
    if (m_socket) {
        m_socket->Close();
        m_socket = 0;
    }
    Application::DoDispose();
}

void TcpStatsServer::StartApplication(void) {
    NS_LOG_FUNCTION(this);
    
    if (!m_socket) {
        TypeId tid = TypeId::LookupByName("ns3::TcpSocketFactory");
        m_socket = Socket::CreateSocket(GetNode(), tid);
        InetSocketAddress local = InetSocketAddress(Ipv4Address::GetAny(), m_port);
        if (m_socket->Bind(local) == -1) {
            NS_FATAL_ERROR("Failed to bind socket");
        }
        m_socket->Listen();
        m_socket->SetAcceptCallback(
            MakeNullCallback<bool, Ptr<Socket>, const Address &>(),
            MakeCallback(&TcpStatsServer::HandleAccept, this)
        );
    }
    
    protocolStats["TCP"].startTime = Simulator::Now().GetSeconds();
    NS_LOG_INFO("TCP Server started on port " << m_port);
}

void TcpStatsServer::StopApplication(void) {
    NS_LOG_FUNCTION(this);
    
    if (m_socket) {
        m_socket->Close();
        m_socket->SetAcceptCallback(
            MakeNullCallback<bool, Ptr<Socket>, const Address &>(),
            MakeNullCallback<void, Ptr<Socket>, const Address &>()
        );
    }
    
    for (auto& socket : m_connections) {
        socket->Close();
    }
    m_connections.clear();
    
    protocolStats["TCP"].stopTime = Simulator::Now().GetSeconds();
}

void TcpStatsServer::HandleAccept(Ptr<Socket> socket, const Address& from) {
    NS_LOG_FUNCTION(this << socket << from);
    socket->SetRecvCallback(MakeCallback(&TcpStatsServer::HandleRead, this));
    m_connections.push_back(socket);
}

void TcpStatsServer::HandleRead(Ptr<Socket> socket) {
    NS_LOG_FUNCTION(this << socket);
    
    Ptr<Packet> packet;
    Address from;
    
    while ((packet = socket->RecvFrom(from))) {
        uint32_t packetSize = packet->GetSize();
        
        // 更新TCP统计
        protocolStats["TCP"].totalBytesReceived += packetSize;
        protocolStats["TCP"].totalPacketsReceived++;
        
        // 计算延迟（简化版本，实际TCP需要更复杂的延迟计算）
        double receiveTime = Simulator::Now().GetSeconds();
        protocolStats["TCP"].totalDelay += receiveTime - protocolStats["TCP"].startTime;
        
        NS_LOG_DEBUG("TCP Packet received, size: " << packetSize << " bytes");
    }
}

/**
 * @brief UDP 服务器应用，用于统计UDP性能
 */
class UdpStatsServer : public Application {
public:
    UdpStatsServer();
    virtual ~UdpStatsServer();

    static TypeId GetTypeId(void);
    
    void Setup(uint16_t port);

protected:
    virtual void DoDispose(void);

private:
    virtual void StartApplication(void);
    virtual void StopApplication(void);
    
    void HandleRead(Ptr<Socket> socket);
    
    uint16_t m_port;
    Ptr<Socket> m_socket;
};

UdpStatsServer::UdpStatsServer() : m_port(0) {
}

UdpStatsServer::~UdpStatsServer() {
}

TypeId UdpStatsServer::GetTypeId(void) {
    static TypeId tid = TypeId("UdpStatsServer")
        .SetParent<Application>()
        .SetGroupName("Applications")
        .AddConstructor<UdpStatsServer>();
    return tid;
}

void UdpStatsServer::Setup(uint16_t port) {
    m_port = port;
}

void UdpStatsServer::DoDispose(void) {
    NS_LOG_FUNCTION(this);
    if (m_socket) {
        m_socket->Close();
        m_socket = 0;
    }
    Application::DoDispose();
}

void UdpStatsServer::StartApplication(void) {
    NS_LOG_FUNCTION(this);
    
    if (!m_socket) {
        TypeId tid = TypeId::LookupByName("ns3::UdpSocketFactory");
        m_socket = Socket::CreateSocket(GetNode(), tid);
        InetSocketAddress local = InetSocketAddress(Ipv4Address::GetAny(), m_port);
        if (m_socket->Bind(local) == -1) {
            NS_FATAL_ERROR("Failed to bind socket");
        }
    }
    
    m_socket->SetRecvCallback(MakeCallback(&UdpStatsServer::HandleRead, this));
    protocolStats["UDP"].startTime = Simulator::Now().GetSeconds();
    NS_LOG_INFO("UDP Server started on port " << m_port);
}

void UdpStatsServer::StopApplication(void) {
    NS_LOG_FUNCTION(this);
    
    if (m_socket) {
        m_socket->SetRecvCallback(MakeNullCallback<void, Ptr<Socket>>());
    }
    
    protocolStats["UDP"].stopTime = Simulator::Now().GetSeconds();
}

void UdpStatsServer::HandleRead(Ptr<Socket> socket) {
    NS_LOG_FUNCTION(this << socket);
    
    Ptr<Packet> packet;
    Address from;
    
    while ((packet = socket->RecvFrom(from))) {
        uint32_t packetSize = packet->GetSize();
        
        // 更新UDP统计
        protocolStats["UDP"].totalBytesReceived += packetSize;
        protocolStats["UDP"].totalPacketsReceived++;
        
        // 计算延迟（简化版本）
        double receiveTime = Simulator::Now().GetSeconds();
        protocolStats["UDP"].totalDelay += receiveTime - protocolStats["UDP"].startTime;
        
        NS_LOG_DEBUG("UDP Packet received, size: " << packetSize << " bytes");
    }
}

/**
 * @brief 创建并配置网络拓扑
 */
void SetupNetwork(NodeContainer& nodes, NetDeviceContainer& devices, 
                  Ipv4InterfaceContainer& interfaces,
                  const std::string& dataRate, const std::string& delay,
                  double errorRate = 0.0) {
    
    // 创建点对点链路
    PointToPointHelper pointToPoint;
    pointToPoint.SetDeviceAttribute("DataRate", StringValue(dataRate));
    pointToPoint.SetChannelAttribute("Delay", StringValue(delay));
    
    devices = pointToPoint.Install(nodes);
    
    // 如果设置了错误率，添加错误模型
    if (errorRate > 0.0) {
        Ptr<RateErrorModel> em = CreateObject<RateErrorModel>();
        em->SetAttribute("ErrorRate", DoubleValue(errorRate));
        em->SetAttribute("ErrorUnit", StringValue("ERROR_UNIT_PACKET"));
        devices.Get(0)->SetAttribute("ReceiveErrorModel", PointerValue(em));
        devices.Get(1)->SetAttribute("ReceiveErrorModel", PointerValue(em));
    }
    
    // 安装协议栈
    InternetStackHelper stack;
    stack.Install(nodes);
    
    // 分配IP地址
    Ipv4AddressHelper address;
    address.SetBase("10.1.1.0", "255.255.255.0");
    interfaces = address.Assign(devices);
}

/**
 * @brief 设置TCP拥塞控制算法
 */
void SetTcpCongestionControl(const std::string& algorithm) {
    if (algorithm == "NewReno") {
        Config::SetDefault("ns3::TcpL4Protocol::SocketType", TypeIdValue(TcpNewReno::GetTypeId()));
    } else if (algorithm == "Cubic") {
        Config::SetDefault("ns3::TcpL4Protocol::SocketType", TypeIdValue(TcpCubic::GetTypeId()));
    } else if (algorithm == "Vegas") {
        Config::SetDefault("ns3::TcpL4Protocol::SocketType", TypeIdValue(TcpVegas::GetTypeId()));
    } else {
        // 默认使用NewReno
        Config::SetDefault("ns3::TcpL4Protocol::SocketType", TypeIdValue(TcpNewReno::GetTypeId()));
    }
    NS_LOG_INFO("TCP Congestion Control Algorithm set to: " << algorithm);
}

/**
 * @brief 运行单个测试场景
 */
void RunTestScenario(const std::string& scenarioName, 
                    const std::string& dataRate, 
                    const std::string& delay,
                    double errorRate,
                    const std::string& tcpAlgorithm,
                    uint32_t packetSize,
                    double simulationTime) {
    
    std::cout << "\n=== 测试场景: " << scenarioName << " ===" << std::endl;
    std::cout << "数据率: " << dataRate << ", 延迟: " << delay;
    if (errorRate > 0) std::cout << ", 错误率: " << errorRate;
    std::cout << ", TCP算法: " << tcpAlgorithm << std::endl;
    
    // 重置统计
    protocolStats.clear();
    protocolStats["TCP"] = ProtocolStats();
    protocolStats["UDP"] = ProtocolStats();
    
    // 设置TCP拥塞控制算法
    SetTcpCongestionControl(tcpAlgorithm);
    
    // 创建节点
    NodeContainer nodes;
    nodes.Create(2);
    
    NetDeviceContainer devices;
    Ipv4InterfaceContainer interfaces;
    
    // 配置网络
    SetupNetwork(nodes, devices, interfaces, dataRate, delay, errorRate);
    
    // 服务器端口
    uint16_t tcpPort = 5000;
    uint16_t udpPort = 5001;
    
    // 安装TCP服务器
    Ptr<TcpStatsServer> tcpServer = CreateObject<TcpStatsServer>();
    tcpServer->Setup(tcpPort);
    nodes.Get(1)->AddApplication(tcpServer);
    tcpServer->SetStartTime(Seconds(1.0));
    tcpServer->SetStopTime(Seconds(simulationTime));
    
    // 安装UDP服务器
    Ptr<UdpStatsServer> udpServer = CreateObject<UdpStatsServer>();
    udpServer->Setup(udpPort);
    nodes.Get(1)->AddApplication(udpServer);
    udpServer->SetStartTime(Seconds(1.0));
    udpServer->SetStopTime(Seconds(simulationTime));
    
    // 安装TCP客户端 (BulkSend)
    BulkSendHelper tcpClient("ns3::TcpSocketFactory", 
                            InetSocketAddress(interfaces.GetAddress(1), tcpPort));
    tcpClient.SetAttribute("MaxBytes", UintegerValue(0)); // 无限发送
    tcpClient.SetAttribute("SendSize", UintegerValue(packetSize));
    ApplicationContainer tcpClientApp = tcpClient.Install(nodes.Get(0));
    tcpClientApp.Start(Seconds(2.0));
    tcpClientApp.Stop(Seconds(simulationTime - 1));
    
    // 安装UDP客户端 (OnOff)
    OnOffHelper udpClient("ns3::UdpSocketFactory", 
                         InetSocketAddress(interfaces.GetAddress(1), udpPort));
    udpClient.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
    udpClient.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
    udpClient.SetAttribute("DataRate", DataRateValue(DataRate(dataRate)));
    udpClient.SetAttribute("PacketSize", UintegerValue(packetSize));
    ApplicationContainer udpClientApp = udpClient.Install(nodes.Get(0));
    udpClientApp.Start(Seconds(2.0));
    udpClientApp.Stop(Seconds(simulationTime - 1));
    
    // 安装FlowMonitor用于更精确的统计
    FlowMonitorHelper flowMonitor;
    Ptr<FlowMonitor> monitor = flowMonitor.InstallAll();
    
    // 运行仿真
    Simulator::Stop(Seconds(simulationTime));
    Simulator::Run();
    
    // 收集FlowMonitor统计
    monitor->CheckForLostPackets();
    Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(flowMonitor.GetClassifier());
    std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats();
    
    // 更新统计信息
    for (auto& flow : stats) {
        FlowMonitor::FlowStats flowStats = flow.second;
        Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(flow.first);
        
        if (t.destinationPort == tcpPort) {
            protocolStats["TCP"].totalPacketsSent = flowStats.txPackets;
            protocolStats["TCP"].totalPacketsReceived = flowStats.rxPackets;
            protocolStats["TCP"].totalBytesReceived = flowStats.rxBytes;
            if (flowStats.rxPackets > 0) {
                protocolStats["TCP"].totalDelay = flowStats.delaySum.GetSeconds();
            }
        } else if (t.destinationPort == udpPort) {
            protocolStats["UDP"].totalPacketsSent = flowStats.txPackets;
            protocolStats["UDP"].totalPacketsReceived = flowStats.rxPackets;
            protocolStats["UDP"].totalBytesReceived = flowStats.rxBytes;
            if (flowStats.rxPackets > 0) {
                protocolStats["UDP"].totalDelay = flowStats.delaySum.GetSeconds();
            }
        }
    }
    
    // 计算并输出性能指标
    std::cout << "\n性能统计结果:" << std::endl;
    std::cout << "协议\t吞吐量(Mbps)\t平均延迟(ms)\t丢包率(%)\t公平性指数" << std::endl;
    
    double totalThroughput = 0.0;
    std::vector<double> throughputs;
    
    for (auto& proto : protocolStats) {
        const std::string& protocol = proto.first;
        ProtocolStats& stats = proto.second;
        
        double effectiveTime = simulationTime - 3.0; // 减去启动和停止时间
        double throughput = (stats.totalBytesReceived * 8.0) / (effectiveTime * 1000000.0);
        double avgDelay = (stats.totalPacketsReceived > 0) ? 
                         (stats.totalDelay / stats.totalPacketsReceived) * 1000 : 0.0;
        double packetLoss = (stats.totalPacketsSent > 0) ? 
                          (1.0 - (double)stats.totalPacketsReceived / stats.totalPacketsSent) * 100 : 0.0;
        
        std::cout << protocol << "\t" 
                  << std::fixed << std::setprecision(4) << throughput << "\t\t"
                  << std::fixed << std::setprecision(2) << avgDelay << "\t\t"
                  << std::fixed << std::setprecision(2) << packetLoss << "\t\t";
        
        totalThroughput += throughput;
        throughputs.push_back(throughput);
    }
    
    // 计算公平性指数 (Jain's Fairness Index)
    double fairnessIndex = 0.0;
    if (throughputs.size() > 0) {
        double sum = 0.0, sumSquares = 0.0;
        for (double t : throughputs) {
            sum += t;
            sumSquares += t * t;
        }
        fairnessIndex = (sum * sum) / (throughputs.size() * sumSquares);
    }
    
    std::cout << "\n公平性指数: " << std::fixed << std::setprecision(4) << fairnessIndex << std::endl;
    
    Simulator::Destroy();
}

/**
 * @brief 主函数
 */
int main(int argc, char *argv[]) {
    // 默认参数
    std::string dataRate = "10Mbps";
    std::string delay = "2ms";
    double errorRate = 0.0;
    std::string tcpAlgorithm = "NewReno";
    uint32_t packetSize = 1024;
    double simulationTime = 20.0;
    
    // 命令行参数解析
    CommandLine cmd;
    cmd.AddValue("dataRate", "PointToPoint link data rate", dataRate);
    cmd.AddValue("delay", "PointToPoint link delay", delay);
    cmd.AddValue("errorRate", "Packet error rate", errorRate);
    cmd.AddValue("tcpAlgorithm", "TCP congestion control algorithm (NewReno, Cubic, Vegas)", tcpAlgorithm);
    cmd.AddValue("packetSize", "Packet size in bytes", packetSize);
    cmd.AddValue("simulationTime", "Simulation time in seconds", simulationTime);
    cmd.Parse(argc, argv);
    
    std::cout << "=== TCP vs UDP 协议性能对比研究 ===" << std::endl;
    std::cout << "默认参数: 数据率=" << dataRate << ", 延迟=" << delay;
    if (errorRate > 0) std::cout << ", 错误率=" << errorRate;
    std::cout << ", TCP算法=" << tcpAlgorithm << ", 包大小=" << packetSize << "B" << std::endl;
    
    // 测试场景1: 理想网络条件
    RunTestScenario("理想网络条件", "10Mbps", "2ms", 0.0, "NewReno", packetSize, simulationTime);
    
    // 测试场景2: 高延迟网络
    RunTestScenario("高延迟网络", "10Mbps", "50ms", 0.0, "NewReno", packetSize, simulationTime);
    
    // 测试场景3: 有丢包网络
    RunTestScenario("有丢包网络", "10Mbps", "2ms", 0.01, "NewReno", packetSize, simulationTime);
    
    // 测试场景4: 低带宽网络
    RunTestScenario("低带宽网络", "1Mbps", "2ms", 0.0, "NewReno", packetSize, simulationTime);
    
    // 测试场景5: 不同TCP拥塞控制算法
    RunTestScenario("TCP Cubic算法", "10Mbps", "2ms", 0.0, "Cubic", packetSize, simulationTime);
    RunTestScenario("TCP Vegas算法", "10Mbps", "2ms", 0.0, "Vegas", packetSize, simulationTime);
    
    // 测试场景6: 混合网络条件
    RunTestScenario("混合网络条件", "5Mbps", "20ms", 0.005, "NewReno", packetSize, simulationTime);
    
    std::cout << "\n=== 所有测试场景完成 ===" << std::endl;
    std::cout << "测试总结:" << std::endl;
    std::cout << "1. TCP在拥塞网络中表现更好，能够自适应调整发送速率" << std::endl;
    std::cout << "2. UDP在低延迟要求下表现更好，但缺乏拥塞控制" << std::endl;
    std::cout << "3. 不同TCP算法在不同网络条件下表现各异" << std::endl;
    std::cout << "4. 公平性指数反映了协议间的资源分配公平性" << std::endl;
    
    return 0;
}
