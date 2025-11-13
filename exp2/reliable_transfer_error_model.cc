/*
 * SPDX-License-Identifier: GPL-2.0-only
 * 
 * Reliable Data Transfer Simulation with Error Models
 * Implements reliable client-server communication with sequence numbers,
 * ACK mechanism, timers, and error models on unreliable channels
 */

#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/internet-module.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/error-model.h"
#include "ns3/flow-monitor-helper.h"
#include "ns3/ipv4-flow-classifier.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("ReliableTransferSimulation");

// Custom packet header for reliable transfer
class ReliableHeader : public Header
{
public:
    ReliableHeader();
    virtual ~ReliableHeader();

    static TypeId GetTypeId(void);
    virtual TypeId GetInstanceTypeId(void) const;
    virtual uint32_t GetSerializedSize(void) const;
    virtual void Serialize(Buffer::Iterator start) const;
    virtual uint32_t Deserialize(Buffer::Iterator start);
    virtual void Print(std::ostream &os) const;

    void SetSequenceNumber(uint32_t seq);
    uint32_t GetSequenceNumber(void) const;
    void SetAckNumber(uint32_t ack);
    uint32_t GetAckNumber(void) const;
    void SetIsAck(bool isAck);
    bool GetIsAck(void) const;

private:
    uint32_t m_sequenceNumber;
    uint32_t m_ackNumber;
    bool m_isAck;
};

ReliableHeader::ReliableHeader()
    : m_sequenceNumber(0),
      m_ackNumber(0),
      m_isAck(false)
{
}

ReliableHeader::~ReliableHeader()
{
}

TypeId
ReliableHeader::GetTypeId(void)
{
    static TypeId tid = TypeId("ReliableHeader")
                            .SetParent<Header>()
                            .SetGroupName("Applications")
                            .AddConstructor<ReliableHeader>();
    return tid;
}

TypeId
ReliableHeader::GetInstanceTypeId(void) const
{
    return GetTypeId();
}

uint32_t
ReliableHeader::GetSerializedSize(void) const
{
    return sizeof(m_sequenceNumber) + sizeof(m_ackNumber) + sizeof(m_isAck);
}

void
ReliableHeader::Serialize(Buffer::Iterator start) const
{
    start.WriteHtonU32(m_sequenceNumber);
    start.WriteHtonU32(m_ackNumber);
    start.WriteU8(m_isAck ? 1 : 0);
}

uint32_t
ReliableHeader::Deserialize(Buffer::Iterator start)
{
    m_sequenceNumber = start.ReadNtohU32();
    m_ackNumber = start.ReadNtohU32();
    m_isAck = (start.ReadU8() == 1);
    return GetSerializedSize();
}

void
ReliableHeader::Print(std::ostream &os) const
{
    os << "Seq: " << m_sequenceNumber << " Ack: " << m_ackNumber 
       << " IsAck: " << (m_isAck ? "true" : "false");
}

void
ReliableHeader::SetSequenceNumber(uint32_t seq)
{
    m_sequenceNumber = seq;
}

uint32_t
ReliableHeader::GetSequenceNumber(void) const
{
    return m_sequenceNumber;
}

void
ReliableHeader::SetAckNumber(uint32_t ack)
{
    m_ackNumber = ack;
}

uint32_t
ReliableHeader::GetAckNumber(void) const
{
    return m_ackNumber;
}

void
ReliableHeader::SetIsAck(bool isAck)
{
    m_isAck = isAck;
}

bool
ReliableHeader::GetIsAck(void) const
{
    return m_isAck;
}

// Reliable Server Application
class ReliableServer : public Application
{
public:
    static TypeId GetTypeId(void);
    ReliableServer();
    virtual ~ReliableServer();

protected:
    virtual void StartApplication(void);
    virtual void StopApplication(void);

    void HandleRead(Ptr<Socket> socket);

private:
    Ptr<Socket> m_socket;
    uint32_t m_expectedSequence;
    uint32_t m_totalPacketsReceived;
    uint32_t m_totalBytesReceived;
};

TypeId
ReliableServer::GetTypeId(void)
{
    static TypeId tid = TypeId("ReliableServer")
                            .SetParent<Application>()
                            .SetGroupName("Applications")
                            .AddConstructor<ReliableServer>();
    return tid;
}

ReliableServer::ReliableServer()
    : m_expectedSequence(0),
      m_totalPacketsReceived(0),
      m_totalBytesReceived(0)
{
}

ReliableServer::~ReliableServer()
{
}

void
ReliableServer::StartApplication(void)
{
    m_socket = Socket::CreateSocket(GetNode(), UdpSocketFactory::GetTypeId());
    InetSocketAddress local = InetSocketAddress(Ipv4Address::GetAny(), 9);
    m_socket->Bind(local);
    m_socket->SetRecvCallback(MakeCallback(&ReliableServer::HandleRead, this));

    NS_LOG_INFO("ReliableServer: Started on port 9");
}

void
ReliableServer::StopApplication(void)
{
    if (m_socket)
    {
        m_socket->Close();
    }
    
    NS_LOG_INFO("ReliableServer: Total packets received: " << m_totalPacketsReceived);
    NS_LOG_INFO("ReliableServer: Total bytes received: " << m_totalBytesReceived);
}

void
ReliableServer::HandleRead(Ptr<Socket> socket)
{
    Ptr<Packet> packet;
    Address from;
    
    while ((packet = socket->RecvFrom(from)))
    {
        ReliableHeader header;
        packet->RemoveHeader(header);
        
        uint32_t packetSize = packet->GetSize();
        m_totalBytesReceived += packetSize;
        
        // Only process data packets (not ACKs)
        if (!header.GetIsAck())
        {
            uint32_t seq = header.GetSequenceNumber();
            
            NS_LOG_INFO("ReliableServer: Received data packet with seq=" << seq 
                       << ", expected=" << m_expectedSequence);
            
            // Check if this is the expected sequence number
            if (seq == m_expectedSequence)
            {
                m_totalPacketsReceived++;
                m_expectedSequence++;
                
                // Send ACK for this sequence number
                Ptr<Packet> ackPacket = Create<Packet>(0);
                ReliableHeader ackHeader;
                ackHeader.SetIsAck(true);
                ackHeader.SetAckNumber(seq);
                
                ackPacket->AddHeader(ackHeader);
                socket->SendTo(ackPacket, 0, from);
                
                NS_LOG_INFO("ReliableServer: Sent ACK for seq=" << seq);
            }
            else
            {
                NS_LOG_INFO("ReliableServer: Unexpected sequence number, expected=" 
                           << m_expectedSequence << ", received=" << seq);
            }
        }
    }
}

// Reliable Client Application
class ReliableClient : public Application
{
public:
    static TypeId GetTypeId(void);
    ReliableClient();
    virtual ~ReliableClient();

    void SetRemote(Address ip, uint16_t port);
    void SetRemote(Address addr);

protected:
    virtual void StartApplication(void);
    virtual void StopApplication(void);

    void SendPacket(void);
    void HandleRead(Ptr<Socket> socket);
    void TimeoutHandler(uint32_t seq);

private:
    Ptr<Socket> m_socket;
    Address m_peerAddress;
    uint16_t m_peerPort;
    
    uint32_t m_sequenceNumber;
    uint32_t m_nextSequence;
    uint32_t m_totalPacketsSent;
    uint32_t m_retransmissions;
    uint32_t m_totalBytesSent;
    
    EventId m_timerEvent;
    Time m_timeout;
    uint32_t m_maxPackets;
    Time m_interval;
    uint32_t m_packetSize;
    
    bool m_waitingForAck;
    uint32_t m_pendingAckSequence;
    
    Time m_startTime;
    Time m_endTime;
};

TypeId
ReliableClient::GetTypeId(void)
{
    static TypeId tid = TypeId("ReliableClient")
                            .SetParent<Application>()
                            .SetGroupName("Applications")
                            .AddConstructor<ReliableClient>()
                            .AddAttribute("MaxPackets",
                                          "The maximum number of packets to send",
                                          UintegerValue(100),
                                          MakeUintegerAccessor(&ReliableClient::m_maxPackets),
                                          MakeUintegerChecker<uint32_t>())
                            .AddAttribute("Interval",
                                          "The time to wait between packets",
                                          TimeValue(Seconds(1.0)),
                                          MakeTimeAccessor(&ReliableClient::m_interval),
                                          MakeTimeChecker())
                            .AddAttribute("PacketSize",
                                          "Size of data payload in bytes",
                                          UintegerValue(1024),
                                          MakeUintegerAccessor(&ReliableClient::m_packetSize),
                                          MakeUintegerChecker<uint32_t>())
                            .AddAttribute("Timeout",
                                          "Timeout for ACK reception",
                                          TimeValue(Seconds(0.5)),
                                          MakeTimeAccessor(&ReliableClient::m_timeout),
                                          MakeTimeChecker());
    return tid;
}

ReliableClient::ReliableClient()
    : m_sequenceNumber(0),
      m_nextSequence(0),
      m_totalPacketsSent(0),
      m_retransmissions(0),
      m_totalBytesSent(0),
      m_waitingForAck(false),
      m_pendingAckSequence(0)
{
}

ReliableClient::~ReliableClient()
{
}

void
ReliableClient::SetRemote(Address ip, uint16_t port)
{
    m_peerAddress = ip;
    m_peerPort = port;
}

void
ReliableClient::SetRemote(Address addr)
{
    m_peerAddress = addr;
}

void
ReliableClient::StartApplication(void)
{
    m_socket = Socket::CreateSocket(GetNode(), UdpSocketFactory::GetTypeId());
    m_socket->Bind();
    m_socket->SetRecvCallback(MakeCallback(&ReliableClient::HandleRead, this));
    
    m_startTime = Simulator::Now();
    
    // Schedule first packet transmission
    Simulator::Schedule(Seconds(0.1), &ReliableClient::SendPacket, this);
    
    NS_LOG_INFO("ReliableClient: Started, will send " << m_maxPackets << " packets");
}

void
ReliableClient::StopApplication(void)
{
    if (m_timerEvent.IsPending())
    {
        Simulator::Cancel(m_timerEvent);
    }
    
    m_endTime = Simulator::Now();
    Time totalTime = m_endTime - m_startTime;
    
    // Calculate effective throughput
    double effectiveThroughput = 0.0;
    if (totalTime.GetSeconds() > 0)
    {
        effectiveThroughput = (m_totalBytesSent * 8.0) / totalTime.GetSeconds() / 1000000.0; // Mbps
    }
    
    NS_LOG_INFO("=== RELIABLE CLIENT STATISTICS ===");
    NS_LOG_INFO("Total packets sent: " << m_totalPacketsSent);
    NS_LOG_INFO("Retransmissions: " << m_retransmissions);
    NS_LOG_INFO("Total bytes sent: " << m_totalBytesSent);
    NS_LOG_INFO("Total time: " << totalTime.GetSeconds() << " seconds");
    NS_LOG_INFO("Effective throughput: " << effectiveThroughput << " Mbps");
    NS_LOG_INFO("Packet loss rate: " << (m_retransmissions * 100.0 / m_totalPacketsSent) << "%");
}

void
ReliableClient::SendPacket(void)
{
    if (m_nextSequence >= m_maxPackets)
    {
        NS_LOG_INFO("ReliableClient: Finished sending all packets");
        return;
    }
    
    // Create packet with data
    Ptr<Packet> packet = Create<Packet>(m_packetSize);
    ReliableHeader header;
    header.SetSequenceNumber(m_nextSequence);
    header.SetIsAck(false);
    
    packet->AddHeader(header);
    
    // Send packet
    m_socket->SendTo(packet, 0, m_peerAddress);
    
    m_totalPacketsSent++;
    m_totalBytesSent += packet->GetSize();
    
    NS_LOG_INFO("ReliableClient: Sent packet with seq=" << m_nextSequence);
    
    // Set up timer for ACK
    m_waitingForAck = true;
    m_pendingAckSequence = m_nextSequence;
    m_timerEvent = Simulator::Schedule(m_timeout, &ReliableClient::TimeoutHandler, this, m_nextSequence);
    
    m_nextSequence++;
}

void
ReliableClient::HandleRead(Ptr<Socket> socket)
{
    Ptr<Packet> packet;
    Address from;
    
    while ((packet = socket->RecvFrom(from)))
    {
        ReliableHeader header;
        packet->RemoveHeader(header);
        
        if (header.GetIsAck())
        {
            uint32_t ackSeq = header.GetAckNumber();
            NS_LOG_INFO("ReliableClient: Received ACK for seq=" << ackSeq);
            
            if (m_waitingForAck && ackSeq == m_pendingAckSequence)
            {
                // Cancel timeout timer
                if (m_timerEvent.IsPending())
                {
                    Simulator::Cancel(m_timerEvent);
                }
                
                m_waitingForAck = false;
                
                // Schedule next packet
                Simulator::Schedule(m_interval, &ReliableClient::SendPacket, this);
            }
        }
    }
}

void
ReliableClient::TimeoutHandler(uint32_t seq)
{
    if (m_waitingForAck && seq == m_pendingAckSequence)
    {
        NS_LOG_INFO("ReliableClient: Timeout for seq=" << seq << ", retransmitting");
        
        m_retransmissions++;
        
        // Resend the packet
        Ptr<Packet> packet = Create<Packet>(m_packetSize);
        ReliableHeader header;
        header.SetSequenceNumber(seq);
        header.SetIsAck(false);
        
        packet->AddHeader(header);
        m_socket->SendTo(packet, 0, m_peerAddress);
        
        m_totalPacketsSent++;
        m_totalBytesSent += packet->GetSize();
        
        // Reset timer
        m_timerEvent = Simulator::Schedule(m_timeout, &ReliableClient::TimeoutHandler, this, seq);
    }
}

int
main(int argc, char* argv[])
{
    bool verbose = true;
    bool tracing = false;
    double errorRate = 0.1;  // 10% packet error rate by default
    uint32_t maxPackets = 50;
    double simulationTime = 30.0;
    uint32_t packetSize = 1024;
    double interval = 1.0;
    double timeout = 0.5;

    CommandLine cmd(__FILE__);
    cmd.AddValue("verbose", "Tell echo applications to log if true", verbose);
    cmd.AddValue("tracing", "Enable pcap tracing", tracing);
    cmd.AddValue("errorRate", "Packet error rate on the channel", errorRate);
    cmd.AddValue("maxPackets", "Maximum number of packets to send", maxPackets);
    cmd.AddValue("simulationTime", "Simulation time in seconds", simulationTime);
    cmd.AddValue("packetSize", "Packet size in bytes", packetSize);
    cmd.AddValue("interval", "Interval between packets in seconds", interval);
    cmd.AddValue("timeout", "Timeout for ACK in seconds", timeout);

    cmd.Parse(argc, argv);

    if (verbose)
    {
        LogComponentEnable("ReliableTransferSimulation", LOG_LEVEL_INFO);
    }

    // Create two nodes
    NodeContainer nodes;
    nodes.Create(2);

    // Create point-to-point link with error model
    PointToPointHelper pointToPoint;
    pointToPoint.SetDeviceAttribute("DataRate", StringValue("5Mbps"));
    pointToPoint.SetChannelAttribute("Delay", StringValue("2ms"));

    NetDeviceContainer devices;
    devices = pointToPoint.Install(nodes);

    // Add error model to the devices
    Ptr<RateErrorModel> em = CreateObject<RateErrorModel>();
    em->SetAttribute("ErrorRate", DoubleValue(errorRate));
    em->SetAttribute("ErrorUnit", StringValue("ERROR_UNIT_PACKET"));
    devices.Get(0)->SetAttribute("ReceiveErrorModel", PointerValue(em));
    devices.Get(1)->SetAttribute("ReceiveErrorModel", PointerValue(em));

    // Install internet stack
    InternetStackHelper stack;
    stack.Install(nodes);

    // Assign IP addresses
    Ipv4AddressHelper address;
    address.SetBase("10.1.1.0", "255.255.255.0");
    Ipv4InterfaceContainer interfaces = address.Assign(devices);

    // Install reliable server on node 1
    Ptr<ReliableServer> serverApp = CreateObject<ReliableServer>();
    nodes.Get(1)->AddApplication(serverApp);
    serverApp->SetStartTime(Seconds(1.0));
    serverApp->SetStopTime(Seconds(simulationTime));

    // Install reliable client on node 0
    Ptr<ReliableClient> clientApp = CreateObject<ReliableClient>();
    clientApp->SetRemote(interfaces.GetAddress(1), 9);
    clientApp->SetAttribute("MaxPackets", UintegerValue(maxPackets));
    clientApp->SetAttribute("PacketSize", UintegerValue(packetSize));
    clientApp->SetAttribute("Interval", TimeValue(Seconds(interval)));
    clientApp->SetAttribute("Timeout", TimeValue(Seconds(timeout)));
    nodes.Get(0)->AddApplication(clientApp);
    clientApp->SetStartTime(Seconds(2.0));
    clientApp->SetStopTime(Seconds(simulationTime));

    // Install UDP echo applications for comparison
    UdpEchoServerHelper echoServer(10);
    ApplicationContainer serverApps = echoServer.Install(nodes.Get(1));
    serverApps.Start(Seconds(1.0));
    serverApps.Stop(Seconds(simulationTime));

    UdpEchoClientHelper echoClient(interfaces.GetAddress(1), 10);
    echoClient.SetAttribute("MaxPackets", UintegerValue(maxPackets));
    echoClient.SetAttribute("Interval", TimeValue(Seconds(interval)));
    echoClient.SetAttribute("PacketSize", UintegerValue(packetSize));
    ApplicationContainer clientApps = echoClient.Install(nodes.Get(0));
    clientApps.Start(Seconds(2.0));
    clientApps.Stop(Seconds(simulationTime));

    // Install FlowMonitor for performance analysis
    FlowMonitorHelper flowHelper;
    Ptr<FlowMonitor> flowMonitor = flowHelper.InstallAll();

    // Set up routing
    Ipv4GlobalRoutingHelper::PopulateRoutingTables();

    if (tracing)
    {
        pointToPoint.EnablePcapAll("reliable_transfer");
    }

    // Set simulation stop time
    Simulator::Stop(Seconds(simulationTime));

    std::cout << "Starting simulation with parameters:" << std::endl;
    std::cout << "  Error rate: " << errorRate * 100 << "%" << std::endl;
    std::cout << "  Max packets: " << maxPackets << std::endl;
    std::cout << "  Packet size: " << packetSize << " bytes" << std::endl;
    std::cout << "  Interval: " << interval << " seconds" << std::endl;
    std::cout << "  Timeout: " << timeout << " seconds" << std::endl;
    std::cout << "  Simulation time: " << simulationTime << " seconds" << std::endl;

    Simulator::Run();

    // Collect and display flow statistics
    flowMonitor->CheckForLostPackets();
    Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(flowHelper.GetClassifier());
    std::map<FlowId, FlowMonitor::FlowStats> stats = flowMonitor->GetFlowStats();

    std::cout << "\n=== FLOW STATISTICS ===" << std::endl;
    for (auto const &flow : stats)
    {
        Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(flow.first);
        
        std::cout << "Flow " << flow.first << " (" << t.sourceAddress << ":" << t.sourcePort 
                  << " -> " << t.destinationAddress << ":" << t.destinationPort << ")" << std::endl;
        std::cout << "  Tx Packets: " << flow.second.txPackets << std::endl;
        std::cout << "  Rx Packets: " << flow.second.rxPackets << std::endl;
        std::cout << "  Tx Bytes: " << flow.second.txBytes << std::endl;
        std::cout << "  Rx Bytes: " << flow.second.rxBytes << std::endl;
        
        if (flow.second.txPackets > 0)
        {
            double lossRate = (flow.second.txPackets - flow.second.rxPackets) * 100.0 / flow.second.txPackets;
            std::cout << "  Packet Loss Rate: " << lossRate << "%" << std::endl;
        }
        
        if (flow.second.rxPackets > 0)
        {
            double throughput = flow.second.rxBytes * 8.0 / 
                               (flow.second.timeLastRxPacket.GetSeconds() - 
                                flow.second.timeFirstTxPacket.GetSeconds()) / 1000000.0;
            double meanDelay = flow.second.delaySum.GetSeconds() / flow.second.rxPackets * 1000.0;
            
            std::cout << "  Throughput: " << throughput << " Mbps" << std::endl;
            std::cout << "  Mean Delay: " << meanDelay << " ms" << std::endl;
        }
        std::cout << std::endl;
    }

    Simulator::Destroy();

    return 0;
}
