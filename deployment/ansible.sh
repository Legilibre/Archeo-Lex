#!/bin/bash

shopt -s nullglob

echo PLAYBOOK=${PLAYBOOK}
echo INVENTORY=${INVENTORY}
echo LIMIT=${LIMIT}
echo SKIP_TAGS=${SKIP_TAGS}
echo VERBOSE=${VERBOSE}
echo PROVIDER=${PROVIDER}

test -z "${PLAYBOOK}" || test -z "${INVENTORY}" || test -z "${LIMIT}"  || test -z "${PROVIDER}" && {
    echo "Environment variables not set." > /dev/stderr
    exit 1
}

ROOT=/vagrant

test -d "${ROOT}" || {
    echo "Invalid root directory '${ROOT}'" > /dev/stderr
    exit 1
}

cd ${ROOT}

# Fix output buffering and colors.
export PYTHONUNBUFFERED=1
export ANSIBLE_FORCE_COLOR=true
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Check internet.
test -x /bin/ping && {
    ping -q -c 1 google.com > /dev/null
    if [ "$?" != 0 ]; then
        echo "No internet connectivity!" > /dev/stderr
        # exit 1
    fi
}

# Install Ansible locally.
if [ ! -x /usr/local/bin/ansible-playbook ]; then
    echo "Installing Ansible."

    if [ -f /etc/debian_version ]; then
        export DEBIAN_FRONTEND=noninteractive
        apt-get update -qq
        apt-get install -qq -y software-properties-common apt-transport-https
        apt-add-repository -y ppa:fkrull/deadsnakes-python2.7
        apt-add-repository -y ppa:ansible/ansible
        apt-get update -qq
        apt-get install -qq -y python2.7 python-pip
        pip install markupsafe ansible
    elif [ -f /etc/redhat-release ]; then
        rpm -Uvh http://download.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm
        yum install centos-release-SCL -y
        yum install ansible -y
        yum install python27 -y
    fi
fi

# Show versions.
ansible --version 2> /dev/null | head -n1
python --version 2>&1

# Make sure Ansible playbook exists.
if [ ! -f ${PLAYBOOK} ]; then
    echo "Cannot find Ansible playbook."
    exit 1
fi

# Mark inventory scripts as executable (otherwise Ansible treats them differently).
chmod +x ${INVENTORY}/*.sh

# Run the playbook.
echo "Running Ansible provisioner defined in Vagrantfile."
ansible-playbook ${PLAYBOOK} -i provisioning/inventory --extra-vars "provider=${PROVIDER} limit=${LIMIT}" --connection=local ${LIMIT:+--limit=$LIMIT} ${SKIP_TAGS:+--skip-tags=$SKIP_TAGS} ${VERBOSE:+-$VERBOSE}
