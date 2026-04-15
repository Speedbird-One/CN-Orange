from mininet.topo import Topo

class StaticTopo(Topo):
    def build(self):
        # Add 3 Switches
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')

        # Add 3 Hosts
        h1 = self.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', ip='10.0.0.3/24', mac='00:00:00:00:00:03')

        # Connect Hosts to Switches
        self.addLink(h1, s1)
        self.addLink(h2, s2)
        self.addLink(h3, s3)

        # Connect Switches (The Triangle)
        self.addLink(s1, s2) # s1-eth2 <-> s2-eth2
        self.addLink(s2, s3) # s2-eth3 <-> s3-eth2
        self.addLink(s3, s1) # s3-eth3 <-> s1-eth3

topos = {'statictopo': (lambda: StaticTopo())}
