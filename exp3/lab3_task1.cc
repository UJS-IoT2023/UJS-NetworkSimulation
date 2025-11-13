/* lab3_task1.cc - 网络传输协议仿真实验任务1 - 修复版本
 * 修复内容：
 * 1. 修复数据包头部处理
 * 2. 优化拥塞控制参数
 * 3. 改进数据包组装逻辑
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/stats-module.h"
#include <vector>
#include <cstring>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("Lab3Task1");

// 全局统计变量
uint32_t totalReceivedPackets = 0;
uint32_t totalLostPackets = 0;
double totalDelay = 0.0;
uint32_t totalBytesReceived = 0;

// 简化自定义头部结构
struct CustomHeader {
    uint32_t sequenceNumber;
    double sendTime;
    uint32_t payloadSize;
    
    CustomHeader() : sequenceNumber(0), sendTime(0.0), payloadSize(0) {}
    
    static constexpr uint32_t GetSize() {
        return sizeof(sequenceNumber) + sizeof(sendTime) + sizeof(payloadSize);
    }
};

/**
 * @brief 接收端应用层，增强统计功能
 */
class EnhancedUdpServer : public Application {
public:
    EnhancedUdpServer();
    virtual ~EnhancedUdpServer();

    static TypeId GetTypeId(void);
    
protected:
    virtual void DoDispose(void);

private:
    virtual void StartApplication(void);
    virtual void StopApplication(void);
    
    void HandleRead(Ptr<Socket> socket);
    
    uint16_t m_port;
    Ptr<Socket> m_socket;
};

EnhancedUdpServer::EnhancedUdpServer() : 
    m_port(9) {
}

EnhancedUdpServer::~EnhancedUdpServer() {
}

TypeId EnhancedUdpServer::GetTypeId(void) {
    static TypeId tid = TypeId("EnhancedUdpServer")
        .SetParent<Application>()
        .SetGroupName("Applications")
        .AddConstructor<EnhancedUdpServer>()
        .AddAttribute("Port", "Port on which we listen for incoming packets.",
                     UintegerValue(9),
                     MakeUintegerAccessor(&EnhancedUdpServer::m_port),
                     MakeUintegerChecker<uint16_t>());
    return tid;
}

void EnhancedUdpServer::DoDispose(void) {
    NS_LOG_FUNCTION(this);
    if (m_socket) {
        m_socket->Close();
        m_socket = 0;
    }
    Application::DoDispose();
}

void EnhancedUdpServer::StartApplication(void) {
    NS_LOG_FUNCTION(this);
    
    if (!m_socket) {
        TypeId tid = TypeId::LookupByName("ns3::UdpSocketFactory");
        m_socket = Socket::CreateSocket(GetNode(), tid);
        InetSocketAddress local = InetSocketAddress(Ipv4Address::GetAny(), m_port);
        if (m_socket->Bind(local) == -1) {
            NS_FATAL_ERROR("Failed to bind socket");
        }
    }
    
    m_socket->SetRecvCallback(MakeCallback(&EnhancedUdpServer::HandleRead, this));
    NS_LOG_INFO("UDP Server started on port " << m_port);
}

void EnhancedUdpServer::StopApplication(void) {
    NS_LOG_FUNCTION(this);
    
    if (m_socket) {
        m_socket->SetRecvCallback(MakeNullCallback<void, Ptr<Socket>>());
    }
}

void EnhancedUdpServer::HandleRead(Ptr<Socket> socket) {
    NS_LOG_FUNCTION(this << socket);
    
    Ptr<Packet> packet;
    Address from;
    
    while ((packet = socket->RecvFrom(from))) {
        uint32_t packetSize = packet->GetSize();
        
        // 检查数据包是否足够大以包含自定义头部
        if (packetSize >= CustomHeader::GetSize()) {
            // 提取自定义头部信息
            uint8_t buffer[CustomHeader::GetSize()];
            packet->CopyData(buffer, CustomHeader::GetSize());
            
            CustomHeader header;
            std::memcpy(&header.sequenceNumber, buffer, sizeof(header.sequenceNumber));
            std::memcpy(&header.sendTime, buffer + sizeof(header.sequenceNumber), sizeof(header.sendTime));
            std::memcpy(&header.payloadSize, buffer + sizeof(header.sequenceNumber) + sizeof(header.sendTime), sizeof(header.payloadSize));
            
            // 计算延迟
            double receiveTime = Simulator::Now().GetSeconds();
            double delay = receiveTime - header.sendTime;
            
            // 更新全局统计
            totalReceivedPackets++;
            totalBytesReceived += packetSize;
            totalDelay += delay;
            
            NS_LOG_INFO("Packet " << header.sequenceNumber << " received with delay: " << delay * 1000 << "ms, size: " << packetSize << " bytes");
        } else {
            NS_LOG_WARN("Received packet too small to contain custom header: " << packetSize << " bytes");
        }
    }
}

/**
 * @brief 增强的UDP客户端，支持可变数据包大小和拥塞控制模拟
 */
class EnhancedUdpClient : public Application {
public:
    EnhancedUdpClient();
    virtual ~EnhancedUdpClient();

    static TypeId GetTypeId(void);
    
    void SetRemote(Address addr);
    void SetPacketSize(uint32_t size);
    void SetMaxPackets(uint32_t max);
    void SetInterval(Time interval);

protected:
    virtual void DoDispose(void);

private:
    virtual void StartApplication(void);
    virtual void StopApplication(void);
    
    void ScheduleTransmit(void);
    void SendPacket(void);
    
    // 拥塞控制相关函数
    void CongestionControl(void);
    
    Ptr<Socket> m_socket;
    Address m_peerAddress;
    EventId m_sendEvent;
    
    uint32_t m_packetSize;
    uint32_t m_maxPackets;
    uint32_t m_packetsSent;
    Time m_interval;
    
    // 拥塞控制参数 - 修复：使用更合理的初始值
    uint32_t m_cwnd;
    uint32_t m_ssthresh;
    bool m_congestionAvoidance;
    
    uint32_t m_sequenceNumber;
};

EnhancedUdpClient::EnhancedUdpClient() : 
    m_socket(0),
    m_packetSize(1024),
    m_maxPackets(100),
    m_packetsSent(0),
    m_interval(Seconds(0.05)),  // 修复：更合理的初始间隔
    m_cwnd(4),                  // 修复：更大的初始窗口
    m_ssthresh(32),             // 修复：更高的慢启动阈值
    m_congestionAvoidance(false),
    m_sequenceNumber(0) {
}

EnhancedUdpClient::~EnhancedUdpClient() {
}

TypeId EnhancedUdpClient::GetTypeId(void) {
    static TypeId tid = TypeId("EnhancedUdpClient")
        .SetParent<Application>()
        .SetGroupName("Applications")
        .AddConstructor<EnhancedUdpClient>()
        .AddAttribute("PacketSize", "The size of packets transmitted.",
                     UintegerValue(1024),
                     MakeUintegerAccessor(&EnhancedUdpClient::m_packetSize),
                     MakeUintegerChecker<uint32_t>())
        .AddAttribute("MaxPackets", "The maximum number of packets the application will send.",
                     UintegerValue(100),
                     MakeUintegerAccessor(&EnhancedUdpClient::m_maxPackets),
                     MakeUintegerChecker<uint32_t>())
        .AddAttribute("Interval", "The time to wait between packets.",
                     TimeValue(Seconds(0.05)),
                     MakeTimeAccessor(&EnhancedUdpClient::m_interval),
                     MakeTimeChecker());
    return tid;
}

void EnhancedUdpClient::DoDispose(void) {
    NS_LOG_FUNCTION(this);
    if (m_socket) {
        m_socket->Close();
        m_socket = 0;
    }
    Application::DoDispose();
}

void EnhancedUdpClient::SetRemote(Address addr) {
    NS_LOG_FUNCTION(this << addr);
    m_peerAddress = addr;
}

void EnhancedUdpClient::SetPacketSize(uint32_t size) {
    NS_LOG_FUNCTION(this << size);
    m_packetSize = size;
}

void EnhancedUdpClient::SetMaxPackets(uint32_t max) {
    NS_LOG_FUNCTION(this << max);
    m_maxPackets = max;
}

void EnhancedUdpClient::SetInterval(Time interval) {
    NS_LOG_FUNCTION(this << interval);
    m_interval = interval;
}

void EnhancedUdpClient::StartApplication(void) {
    NS_LOG_FUNCTION(this);
    
    if (!m_socket) {
        TypeId tid = TypeId::LookupByName("ns3::UdpSocketFactory");
        m_socket = Socket::CreateSocket(GetNode(), tid);
        
        if (m_socket->Bind() == -1) {
            NS_FATAL_ERROR("Failed to bind socket");
        }
    }
    
    m_socket->Connect(m_peerAddress);
    NS_LOG_INFO("UDP Client started, connecting to " << m_peerAddress);
    
    ScheduleTransmit();
}

void EnhancedUdpClient::StopApplication(void) {
    NS_LOG_FUNCTION(this);
    
    if (m_socket) {
        m_socket->Close();
    }
    
    if (m_sendEvent.IsPending()) {  // 修复：使用IsPending替代IsRunning
        Simulator::Cancel(m_sendEvent);
    }
}

void EnhancedUdpClient::ScheduleTransmit(void) {
    NS_LOG_FUNCTION(this);
    m_sendEvent = Simulator::Schedule(m_interval, &EnhancedUdpClient::SendPacket, this);
}

void EnhancedUdpClient::SendPacket(void) {
    NS_LOG_FUNCTION(this);
    
    if (m_packetsSent >= m_maxPackets) {
        NS_LOG_INFO("Reached maximum packet count: " << m_maxPackets);
        return;
    }
    
    // 创建自定义头部
    CustomHeader header;
    header.sequenceNumber = m_sequenceNumber++;
    header.sendTime = Simulator::Now().GetSeconds();
    header.payloadSize = m_packetSize;
    
    // 序列化头部
    uint8_t headerBuffer[CustomHeader::GetSize()];
    std::memcpy(headerBuffer, &header.sequenceNumber, sizeof(header.sequenceNumber));
    std::memcpy(headerBuffer + sizeof(header.sequenceNumber), &header.sendTime, sizeof(header.sendTime));
    std::memcpy(headerBuffer + sizeof(header.sequenceNumber) + sizeof(header.sendTime), &header.payloadSize, sizeof(header.payloadSize));
    
    // 创建完整的数据包 - 修复：确保总大小正确
    uint32_t totalPacketSize = m_packetSize;
    uint32_t payloadSize = totalPacketSize - CustomHeader::GetSize();
    
    // 创建包含头部的数据包
    Ptr<Packet> packet = Create<Packet>(headerBuffer, CustomHeader::GetSize());
    
    // 如果需要，添加有效载荷
    if (payloadSize > 0) {
        Ptr<Packet> payload = Create<Packet>(payloadSize);
        packet->AddAtEnd(payload);
    }
    
    // 发送数据包
    int actualBytes = m_socket->Send(packet);
    if (actualBytes > 0) {
        m_packetsSent++;
        NS_LOG_INFO("Sending packet " << header.sequenceNumber << " at time " << header.sendTime << ", size: " << actualBytes << " bytes");
        
        // 模拟拥塞控制 - 修复：更温和的控制
        if (m_packetsSent % 15 == 0) {  // 减少触发频率
            CongestionControl();
        }
        
        if (m_packetsSent < m_maxPackets) {
            ScheduleTransmit();
        } else {
            NS_LOG_INFO("Finished sending all " << m_maxPackets << " packets");
        }
    } else {
        NS_LOG_ERROR("Failed to send packet " << header.sequenceNumber);
        totalLostPackets++;
    }
}

void EnhancedUdpClient::CongestionControl(void) {
    NS_LOG_FUNCTION(this);
    
    // 修复：更温和的拥塞控制
    if (!m_congestionAvoidance) {
        // 慢启动阶段 - 更温和的增长
        m_cwnd = std::min(m_cwnd + 2, m_ssthresh);
        if (m_cwnd >= m_ssthresh) {
            m_congestionAvoidance = true;
            NS_LOG_INFO("Entering congestion avoidance phase, cwnd: " << m_cwnd);
        }
    } else {
        // 拥塞避免阶段 - 线性增长
        m_cwnd += 1;
    }
    
    // 修复：更少的模拟丢包事件
    if (m_packetsSent % 40 == 0 && m_packetsSent > 0) {  // 减少丢包频率
        m_ssthresh = std::max(m_cwnd / 2, 4u);  // 确保阈值不会太小
        m_cwnd = 4;  // 重置到合理值而不是1
        m_congestionAvoidance = false;
        NS_LOG_INFO("Simulated packet loss! ssthresh: " << m_ssthresh << " cwnd: " << m_cwnd);
        totalLostPackets += 2;  // 模拟少量丢包
    }
    
    // 调整发送间隔 - 修复：限制最小间隔
    double minInterval = 0.001;  // 最小1ms间隔
    double calculatedInterval = 1.0 / m_cwnd;
    m_interval = Seconds(std::max(calculatedInterval, minInterval));
    
    NS_LOG_INFO("Congestion control: cwnd=" << m_cwnd << ", interval=" << m_interval.GetSeconds() << "s");
}

/**
 * @brief 主函数
 */
int main(int argc, char *argv[]) {
    // 配置参数
    uint32_t packetSize = 1024;
    uint32_t maxPackets = 100;
    double simulationTime = 20.0;
    std::string dataRate = "5Mbps";
    std::string delay = "2ms";
    
    // 命令行参数解析
    CommandLine cmd;
    cmd.AddValue("packetSize", "Packet size in bytes", packetSize);
    cmd.AddValue("maxPackets", "Total number of packets to send", maxPackets);
    cmd.AddValue("simulationTime", "Simulation time in seconds", simulationTime);
    cmd.AddValue("dataRate", "PointToPoint link data rate", dataRate);
    cmd.AddValue("delay", "PointToPoint link delay", delay);
    cmd.Parse(argc, argv);
    
    // 重置全局统计变量
    totalReceivedPackets = 0;
    totalBytesReceived = 0;
    totalDelay = 0.0;
    totalLostPackets = 0;
    
    // 创建节点
    NodeContainer nodes;
    nodes.Create(2);
    
    // 创建点对点链路
    PointToPointHelper pointToPoint;
    pointToPoint.SetDeviceAttribute("DataRate", StringValue(dataRate));
    pointToPoint.SetChannelAttribute("Delay", StringValue(delay));
    
    NetDeviceContainer devices;
    devices = pointToPoint.Install(nodes);
    
    // 安装协议栈
    InternetStackHelper stack;
    stack.Install(nodes);
    
    // 分配IP地址
    Ipv4AddressHelper address;
    address.SetBase("10.1.1.0", "255.255.255.0");
    Ipv4InterfaceContainer interfaces = address.Assign(devices);
    
    // 设置UDP服务器
    uint16_t port = 9;
    Ptr<EnhancedUdpServer> server = CreateObject<EnhancedUdpServer>();
    server->SetAttribute("Port", UintegerValue(port));
    nodes.Get(1)->AddApplication(server);
    server->SetStartTime(Seconds(1.0));
    server->SetStopTime(Seconds(simulationTime));
    
    // 设置UDP客户端
    Ptr<EnhancedUdpClient> client = CreateObject<EnhancedUdpClient>();
    InetSocketAddress remoteAddr = InetSocketAddress(interfaces.GetAddress(1), port);
    client->SetRemote(remoteAddr);
    client->SetPacketSize(packetSize);
    client->SetMaxPackets(maxPackets);
    client->SetInterval(Seconds(0.05));
    nodes.Get(0)->AddApplication(client);
    client->SetStartTime(Seconds(2.0));
    client->SetStopTime(Seconds(simulationTime - 1));
    
    // 启用详细日志（可选）
    // LogComponentEnable("Lab3Task1", LOG_LEVEL_INFO);
    // LogComponentEnable("EnhancedUdpClient", LOG_LEVEL_INFO);
    // LogComponentEnable("EnhancedUdpServer", LOG_LEVEL_INFO);
    
    std::cout << "Starting simulation with parameters:" << std::endl;
    std::cout << "  Packet Size: " << packetSize << " bytes" << std::endl;
    std::cout << "  Max Packets: " << maxPackets << std::endl;
    std::cout << "  Simulation Time: " << simulationTime << " seconds" << std::endl;
    std::cout << "  Data Rate: " << dataRate << std::endl;
    std::cout << "  Delay: " << delay << std::endl;
    
    // 运行仿真
    Simulator::Stop(Seconds(simulationTime));
    Simulator::Run();
    
    // 输出统计结果
    double throughput = (totalBytesReceived * 8.0) / (simulationTime * 1000000.0); // Mbps
    double averageDelay = totalReceivedPackets > 0 ? totalDelay / totalReceivedPackets : 0;
    double packetLossRate = (maxPackets > 0) ? 
        (double)(maxPackets - totalReceivedPackets) / maxPackets : 0;
    
    std::cout << "\n=== 网络性能统计结果 ===" << std::endl;
    std::cout << "仿真时间: " << simulationTime << " 秒" << std::endl;
    std::cout << "数据包大小: " << packetSize << " 字节" << std::endl;
    std::cout << "发送数据包总数: " << maxPackets << std::endl;
    std::cout << "接收数据包总数: " << totalReceivedPackets << std::endl;
    std::cout << "总接收字节数: " << totalBytesReceived << " 字节" << std::endl;
    std::cout << "网络吞吐量: " << throughput << " Mbps" << std::endl;
    std::cout << "平均延迟: " << averageDelay * 1000 << " ms" << std::endl;
    std::cout << "丢包率: " << packetLossRate * 100 << "%" << std::endl;
    std::cout << "========================\n" << std::endl;
    
    Simulator::Destroy();
    return 0;
}

