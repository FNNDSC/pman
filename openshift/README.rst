##############
Example Kube Config Setup to run locally:
##############

Assuming oc cluster up has been run.

.. code-block:: bash

    sudo oc login -u system:admin
    sudo oc create sa robot -n myproject
    sudo oc describe sa robot -n myproject
    sudo oc adm policy add-role-to-user edit system:serviceaccount:myproject:robot -n myproject
    sudo oc describe secret <Ex: robot-token-4vhxc> -n myproject
    
    ############################
    # Changes for using hostPath in container. These are not needed, if you want to use swift as backend storage.
    mkdir /tmp/share           # Create a directory that could be mounted in container. This is mounted as /shareDir in container.
    chcon -R -t svirt_sandbox_file_t /tmp/share/ # Change selinux label so that containers can read/write from/to directory.
    oc edit scc restricted     # Update allowHostDirVolumePlugin to true and runAsUser: type: RunAsAny.
    A restricted SCC should look like this: https://gist.github.com/ravisantoshgudimetla/91748a20766672d2f26b93b3c42517b4
    ############################   

    rm -f ~/.kube/config
    oc login --token=<token from above>    # Note: Use 172.30.0.1:443 if running with oc cluster up
    oc project myproject
    oc create secret generic kubecfg --from-file=/home/dmcphers/.kube/config -n myproject
    rm -f ~/.kube/config
    oc login
    # Ignore this step, if you are using swift as backend storage.
    oc new-app openshift/pman-openshift-template-without-swift.json

##############
Temoporary Dependancy Errors
##############
There is a dependancy error with the current versoin of the skopeo-containers library that is preventing pods from running in local Openshift instances. If you are getting errors resembling:

::

    container_linux.go:247: starting container process caused "process_linux.go:364: container init caused \"rootfs_linux.go:54: mounting \\\"/var/lib/origin/openshift.local.volumes/pods/ba2cd7c2-b5b9-11e7-b32d-64006a559656/volumes/kubernetes.io~secret/service-catalog-controller-token-smgtf\\\" to rootfs \\\"/var/lib/docker/devicemapper/mnt/c96d3bac59427d2b2d5c0cafd40cd5a8d1d31e380561adeb444598deec488bf8/rootfs\\\" at \\\"/var/lib/docker/devicemapper/mnt/c96d3bac59427d2b2d5c0cafd40cd5a8d1d31e380561adeb444598deec488bf8/rootfs/run/secrets/kubernetes.io/serviceaccount\\\" caused \\\"mkdir /var/lib/docker/devicemapper/mnt/c96d3bac59427d2b2d5c0cafd40cd5a8d1d31e380561adeb444598deec488bf8/rootfs/run/secrets/kubernetes.io: read-only file system\\\"\"


The current workaround is to move or delete the /usr/share/rhel/secrets directory. To be on the safe side, it is recommended you just move it somewhere temporary, which can be done with the command:

.. code-block:: bash 

    mv /usr/share/rhel/secrets <desired destination>


#############
Script
#############
A script named pmanSetup.sh can be used to run most of the above commands, and will leave you off in vim editing the scc restricted file. You will have to procede manually from then on, but it should cut a lot of the tedious work out. Its a work in progress. To run the script, just use the command: 

.. code-block:: bash 

    bash pmanSetup.sh

##############
Swift Object Store
##############

The OpenStack Object Store project, known as Swift, offers cloud storage software so that you can store and retrieve lots of data with a simple API. It's built for scale and optimized for durability, availability, and concurrency across the entire data set. Swift is ideal for storing unstructured data that can grow without bound. 

To enable Swift Object store option for pfioh, start pfioh with --swift-storage option

.. code-block:: bash

    pfioh --forever --httpResponse --swift-storage --createDirsAsNeeded

The pushPath and pullPath operations are same as mentioned for mounting directories method.

The credentials file for Swift should be stored in a **secret**, mounted at /etc/swift in the pod with the name ‘swift-credentials.cfg’. It should contain the swift credentials in the following format:


.. code-block:: bash
    
    [AUTHORIZATION]
    osAuthUrl  =   
    username   = 
    password   = 

    [PROJECT]
    osProjectDomain  = 
    osProjectName    = 

**************
Creating a secret and running pman.
**************
1) Create a text file with the name swift-credentials.cfg as shown above.


2) Now run the following command to create a secret

.. code-block:: bash

    oc create secret generic swift-credentials --from-file=<path-to-file>/swift-credentials.cfg

3) Run pman template.

.. code-block:: bash
   
    oc new-app openshift/pman-openshift-template.json
