#!/usr/bin/env ruby

require './deployment/vagrant.rb'

hosts = JSON.parse(File.read('hosts.json'))
Vagrant::AutoConfigure.symbolize_keys_deep!(hosts)

Vagrant.autoconfigure(hosts)
