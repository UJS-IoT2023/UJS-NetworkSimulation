#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("Task6Debug");

class MyDebugApp : public Application
{
public:
    MyDebugApp() : m_count(0) {}
    virtual ~MyDebugApp() {}

private:
    virtual void StartApplication() override
    {
        NS_LOG_INFO("MyDebugApp START at " << Simulator::Now().GetSeconds() << "s");
        ScheduleNext();
    }

    virtual void StopApplication() override
    {
        NS_LOG_INFO("MyDebugApp STOP at " << Simulator::Now().GetSeconds() << "s");
    }

    void ScheduleNext()
    {
        if (m_count < 5)
        {
            Simulator::Schedule(Seconds(1.0), &MyDebugApp::PrintTime, this);
        }
    }

    void PrintTime()
    {
        m_count++;
        NS_LOG_INFO(">>> [Time: " << Simulator::Now().GetSeconds()
                    << "s] Packet count = " << m_count);

        // 故意制造一个“可调试点”：当 count == 3 时，触发条件
        if (m_count == 3)
        {
            NS_LOG_WARN("COUNT == 3! Ready for breakpoint inspection.");
            // 可选：取消注释下面这行，制造段错误用于崩溃调试
            // int* p = nullptr; *p = 42;
        }

        ScheduleNext();
    }

    uint32_t m_count;
};

int main(int argc, char* argv[])
{
    Time::SetResolution(Time::NS);
    LogComponentEnable("Task6Debug", LOG_LEVEL_INFO);

    CommandLine cmd(__FILE__);
    cmd.Parse(argc, argv);

    // === 拓扑 ===
    NodeContainer nodes;
    nodes.Create(2);

    PointToPointHelper p2p;
    p2p.SetDeviceAttribute("DataRate", StringValue("5Mbps"));
    p2p.SetChannelAttribute("Delay", StringValue("2ms"));
    NetDeviceContainer devices = p2p.Install(nodes);

    InternetStackHelper stack;
    stack.Install(nodes);

    Ipv4AddressHelper addr;
    addr.SetBase("10.1.1.0", "255.255.255.0");
    Ipv4InterfaceContainer ifaces = addr.Assign(devices);

    // === 服务器 ===
    UdpEchoServerHelper server(9);
    ApplicationContainer serverApp = server.Install(nodes.Get(1));
    serverApp.Start(Seconds(1.0));
    serverApp.Stop(Seconds(10.0));

    // === 客户端 ===
    UdpEchoClientHelper client(ifaces.GetAddress(1), 9);
    client.SetAttribute("MaxPackets", UintegerValue(3));
    client.SetAttribute("Interval", TimeValue(Seconds(2.0)));
    client.SetAttribute("PacketSize", UintegerValue(1024));
    ApplicationContainer clientApp = client.Install(nodes.Get(0));
    clientApp.Start(Seconds(2.0));
    clientApp.Stop(Seconds(10.0));

    // === 自定义 App ===
    Ptr<MyDebugApp> debugApp = CreateObject<MyDebugApp>();
    nodes.Get(0)->AddApplication(debugApp);
    debugApp->SetStartTime(Seconds(3.0));
    debugApp->SetStopTime(Seconds(10.0));

    NS_LOG_INFO("=== Simulation Start ===");

    AsciiTraceHelper ascii;
    p2p.EnableAsciiAll(ascii.CreateFileStream("task8-p2p.tr"));
    // p2p.EnablePcapAll("task8-p2p");  // 可选：生成 .pcap

    Simulator::Run();
    Simulator::Destroy();
    NS_LOG_INFO("=== Simulation End ===");

    return 0;
}
