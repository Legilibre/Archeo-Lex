#!/usr/bin/env ruby

module Vagrant
  module AutoConfigure

    DIRECTORY_MAPPING = {
      "." => {
        :dest => "/vagrant",
        :mount_options => [],
        :limit => false
      }
    }

    class AutoConfigurePlugin < Vagrant.plugin('2')
      name 'auto_configure_plugin'

      Vagrant.define_singleton_method(:autoconfigure) do |inventory|
        Vagrant.configure('2') do |config|
          AutoConfigure::install_plugins([
            "vagrant-cachier",
            "vagrant-managed-servers",
            "vagrant-triggers"
          ])

          inventory.each do |key, value|
            if value.key?(:provider)
              value[:provider] = "virtualbox" if not value.key?(:provider)
              value[:box] = "ubuntu/trusty64" if not value.key?(:box)
              value[:memory] = 4096 if not value.key?(:memory)
              value[:skip_tags] = [] if not value.key?(:skip_tags)
              AutoConfigure::send("define_#{value[:provider]}", config, key.to_s, value)
            end
          end
        end
      end
    end

    def self.install_plugins(plugins)
      should_restart = false

      plugins.each do |plugin|
        unless Vagrant.has_plugin? plugin
          system "vagrant plugin install #{plugin}"
          should_restart = true
        end
      end

      if should_restart
        puts "Plugins were installed. Please run the Vagrant command again if there's an error."
      end
    end

    def self.provision_with_ansible(config, name, params)
      script_path = "deployment/ansible.sh"

      script = <<-SH
        export PLAYBOOK=provisioning/provision.yml
        export INVENTORY=provisioning/inventory
        export LIMIT=#{name}
        export SKIP_TAGS=#{params[:skip_tags].join(",")}
        export VERBOSE=vvv
        export PROVIDER=#{params[:provider]}

        cd /vagrant
        source #{script_path}
      SH

      config.vm.provision :shell, :inline => script
    end

    def self.define_managed(config, name, params)
      # Workaround for https://github.com/tknerr/vagrant-managed-servers/issues/34
      return unless ARGV.include?(name)

      config.vm.define name, autostart: false do |config|
        config.vm.box = "tknerr/managed-server-dummy"

        config.vm.hostname = params[:vars][:hostname]

        config.vm.provider :managed do |managed, override|
          managed.server = params[:hosts][0] # FIXME: Deal with multiple hosts.

          override.ssh.username = params[:vars][:ansible_ssh_user]
          override.ssh.private_key_path = params[:vars][:ansible_ssh_private_key_file]
        end

        DIRECTORY_MAPPING.each {
          |src, dest|

          if (src && File.exist?(src)) && (!dest[:limit] || dest[:limit].include?(name))
            config.vm.synced_folder src, dest[:dest], mount_options: dest[:mount_options]
          end
        }

        self.provision_with_ansible config, name, params
      end
    end

    def self.define_virtualbox(config, name, params)

      require 'rbconfig'

      is_windows = (RbConfig::CONFIG['host_os'] =~ /mswin|mingw|cygwin/)
      if is_windows
        is_admin = system('reg query "HKU\S-1-5-19" >nul 2>nul')
        if !is_admin
          raise "You must have administrator privileges."
        end
      end

      config.vm.define name, primary: true do |config|
        config.vm.box = params[:box]

        # Read the first host in the list. Might support multiple hosts in the future.
        config.vm.network :private_network, ip: params[:hosts][0]

        config.vm.hostname = params[:vars][:hostname]

        config.vm.provider :virtualbox do |vbox, override|
          vbox.customize ["setextradata", :id, "VBoxInternal2/SharedFoldersEnableSymlinksCreate/v-root", "1"]
          vbox.customize ["setextradata", :id, "VBoxInternal/Devices/VMMDev/0/Config/GetHostTimeDisabled", "0"]
          vbox.customize ["guestproperty", "set", :id, "/VirtualBox/GuestAdd/VBoxService/--timesync-set-threshold", 10000]
          vbox.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
          vbox.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
          vbox.customize ["modifyvm", :id, "--memory", params[:memory]]
          vbox.customize ["modifyvm", :id, "--cpus", 2]
          vbox.customize ["modifyvm", :id, "--ioapic", "on"]
          vbox.customize ["modifyvm", :id, "--rtcuseutc", "on"]

          # Resolve "stdin: is not a tty" errors.
          # Disabling because it breaks `vagrant ssh -c COMMAND`.
          # override.ssh.shell = "bash -c 'BASH_ENV=/etc/profile exec bash'"
        end

        DIRECTORY_MAPPING.each {
          |src, dest|

          if (src && File.exist?(src)) && (!dest[:limit] || dest[:limit].include?(name))
            config.vm.synced_folder src, dest[:dest], mount_options: dest[:mount_options]
          end
        }

        self.provision_with_ansible config, name, params

        config.vm.post_up_message = "Please add this line to your /etc/hosts:\n" +
        "#{params[:hosts][0]} #{params[:vars][:hostname]}"

        if Vagrant.has_plugin?("vagrant-cachier")
          config.cache.scope = :box
        end
      end
    end

    def self.define_docker(config, name, params)
      return unless ARGV.include?(name)

      export_path = "../docker-export/archeo-lex.tar"
      script_path = "deployment/ansible.sh"


      config.trigger.before :up, :vm => name do |trigger|
        if not File.exist? export_path
          data = { "provisioners" => [] }

          DIRECTORY_MAPPING.each {
            |src, dest|

            data["provisioners"].push({
              :type => "file",
              :source => (Pathname.new(src).absolute? ? "#{src}/" : "{{ pwd }}/#{src}/"),
              :destination => dest[:dest]
            }) if src && File.exist?(src)
          }

          data["provisioners"].push({
            :type => "shell",
            :environment_vars => [
              "PLAYBOOK=provisioning/provision.yml",
              "INVENTORY=provisioning/inventory",
              "LIMIT=#{name}",
              "SKIP_TAGS=#{params[:skip_tags].join(",")}",
              "VERBOSE=vvv",
              "PROVIDER=#{params[:provider]}"
            ],
            :script => script_path
          })

          docker_image_mapping = {
            "ubuntu/trusty64" => "ansible/ubuntu14.04-ansible:stable",
            "bento/centos-6.7" => "centos:6.7"
          }

          raise "Unsupported box for Docker: #{params[:box]}" unless docker_image_mapping.key?(params[:box])

          data["builders"] = [{
            :name => "archeo-lex",
            :type => "docker",
            :image => docker_image_mapping[params[:box]],
            :export_path => export_path
          }]

          data["post-processors"] = [{
            :type => "docker-import",
            :repository => "archeo-lex",
            :tag => "latest",
            :keep_input_artifact => true
          }]

          Vagrant::AutoConfigure::write(data, "provisioning/generated/packer.json")

          `mkdir -p $(dirname #{export_path})`

          system "packer build provisioning/generated/packer.json"
          print("ok\n")
        end
      end

      config.vm.define name, autostart: false do |config|
        config.vm.network :forwarded_port, guest: 80, host: 80
        config.vm.network :forwarded_port, guest: 443, host: 443

        config.vm.hostname = params[:vars][:hostname]

        config.vm.provider :docker do |d|
          d.image = "archeo-lex:latest"
          d.name = "archeo-lex"
          d.cmd = ["/usr/local/bin/archeo-lex-run.sh"]
          d.create_args = ["--add-host='#{params[:vars][:hostname]}:127.0.0.1'"]
        end
      end
    end

    def self.write(inventory, filename)
      require 'fileutils'

      FileUtils.mkdir_p(File.dirname(filename))

      File.open(filename, "w") do |f|
        f.write(JSON.pretty_generate(inventory))
      end
    end

    def self.symbolize_keys_deep!(h)
        h.keys.each do |k|
            ks    = k.to_sym
            h[ks] = h.delete k
            symbolize_keys_deep! h[ks] if h[ks].kind_of? Hash
        end
    end

  end

end
