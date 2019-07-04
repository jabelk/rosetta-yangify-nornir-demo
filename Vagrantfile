# -*- mode: ruby -*-
# vi: set ft=ruby :

"""
Additional junos info 
junos user: root password: Juniper
multi_vendor$ vagrant ssh junos
--- JUNOS 12.1X47-D15.4 built 2014-11-12 02:13:59 UTC
root@vagrant-junos-test% cli
root@vagrant-junos-test> 
"""
Vagrant.configure(2) do |config|
  config.vbguest.auto_update = false
  config.vm.define "eos" do |eos|
    # get a free account and download from arista https://eos.arista.com/openconfig-4-20-2-1f-release-notes/
    eos.vm.box = "vEOS-lab-4.20.1F"
    # Configure a forwarded port to access eAPI on vEOS
    # https://username:password@localhost:8443/command-api
    eos.vm.network "forwarded_port", guest: 443, host: 8443, id: 'https'
    eos.vm.network :forwarded_port, guest: 443, host: 12443, id: 'https'
    # Add additional NICs to the VM:
    #   NIC1 (Management 1) - is created in the the basebox and vagrant always uses this via DHCP to communicate with the VM.
    #   The default Vagrantfile template includes Ethernet1 and Ethernet2.  Add lines similar to those below to create
    #     additional NICs which will be Ethernet 3-n                                
    #   Using link-local addresses to satisfy the Vagrantfile config parser, only.  They will not be used by vEOS.
    # Create Ethernet3
    eos.vm.network 'private_network', virtualbox__intnet: true, ip: '169.254.1.11', auto_config: false
    # Create Ethernet4
    eos.vm.network 'private_network', virtualbox__intnet: true, ip: '169.254.1.11', auto_config: false
    eos.vm.provider "virtualbox" do |v|
      # Patch Ethernet1 to a particular internal network
      v.customize ["modifyvm", :id, "--nic2", "intnet", "--intnet2", "vEOS-intnet1"]
      # Patch Ethernet2 to a particular internal network
      v.customize ["modifyvm", :id, "--nic3", "intnet", "--intnet3", "vEOS-intnet2"]
    end
    # The sample, below is preconfigured in the basebox
    # Enable eAPI in the EOS config
    # add vagrant user, thanks to Jere Julian
    eos.vm.provision 'shell', inline: <<-SHELL
      FastCli -p 15 -c "configure
      username vagrant privilege 15 role network-admin secret vagrant
      management api http-commands
        no shutdown
      end
      copy running-config startup-config"
    SHELL
  end
  config.vm.define "junos" do |junos|
    # thanks to https://keepingitclassless.net/2015/03/go-go-gadget-networking-lab/
    junos.vm.box = "juniper/ffp-12.1X47-D15.4-packetmode"
    junos.vm.network :forwarded_port, guest: 22, host: 12203, id: 'ssh'
    junos.vm.hostname = 'vagrant-junos-test'
    junos.vm.network "private_network",
                      ip: "192.168.33.10",
                      netmask: "255.255.252.0",
                      virtualbox__intnet: "teststatic"
    junos.vm.network "private_network",
                      type: "dhcp",
                      virtualbox__intnet: "testdhcp"
    junos.vm.network "private_network",
                      ip: "192.168.34.10",
                      virtualbox__intnet: "teststatic2"
    junos.vm.network "private_network",
                      type: "dhcp",
                      virtualbox__intnet: "testdhcp2"
    junos.vm.network "private_network",
                      ip: "192.168.35.10",
                      virtualbox__intnet: "teststatic3"
    junos.vm.network "private_network",
                      type: "dhcp",
                      virtualbox__intnet: "testdhcp3"
    junos.vm.network "private_network",
                      ip: "192.168.36.10",
                      virtualbox__intnet: "teststatic4"
  end
  config.vm.define "ios" do |ios|
    # see https://github.com/hpreston/vagrant_net_prog/tree/master/box_building to build with netconf/restconf ready
    ios.vm.box = "iosxe/16.06.02"
    ios.vm.network :forwarded_port, guest: 22, host: 12204, id: 'ssh'
    ios.vm.network "private_network", virtualbox__intnet: "link_1", ip: "169.254.1.11", auto_config: false
    ios.vm.network "private_network", virtualbox__intnet: "link_2", ip: "169.254.1.11", auto_config: false
  end
end
