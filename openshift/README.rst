##############
Example to run locally:
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
    mkdir /tmp/share           # Create a directory that could be mounted in container. This is mounted as /share in container.
    chcon -R -t svirt_sandbox_file_t /tmp/share/ # Change selinux label so that containers can read/write from/to directory.
    sudo oc edit scc restricted     # Update allowHostDirVolumePlugin to true and runAsUser type to RunAsAny
    ############################  

    rm -f ~/.kube/config
    oc login --token=<token from describe secret call above>    # Note: Use 172.30.0.1:443 if running with oc cluster up
    oc project myproject
    oc create secret generic kubecfg --from-file=$HOME/.kube/config -n myproject
    # To set the passwords, follow the instructions in the "Setting up authorization" section. Simply editing example-config.cfg DOES NOT DO ANYTHING.
    oc create -f example-secret.yml # Uses the default password ("password")
    rm -f ~/.kube/config
    oc login # As developer
    # Ignore this step, if you are using swift as backend storage.
    oc new-app openshift/pman-openshift-template-without-swift.json
    oc set env dc/pman OPENSHIFTMGR_PROJECT=myproject

**************
Setting up authorization
**************
1) Edit the configuration file:

.. code-block:: bash
    
    #example-config.cfg
    [AUTH TOKENS]
    examplekey1 = examplepassword1
    examplekey2 = examplepassword2

2) Convert the configuration to base64:

.. code-block:: bash
  
    cat example-config.cfg | base64

3) Place the output in a new file:

.. code-block:: bash
  
    apiVersion: v1
    kind: Secret
    metadata:
      name: pman-config
    type: Opaque
    data:
      pman_config.cfg: <base64 encoded configuration>

##############
Swift Object Store
##############

The OpenStack Object Store project, known as Swift, offers cloud storage software so that you can store and retrieve lots of data with a simple API. It's built for scale and optimized for durability, availability, and concurrency across the entire data set. Swift is ideal for storing unstructured data that can grow without bound. 

To enable Swift Object store option for pfioh, start pfioh with --swift-storage option

.. code-block:: bash

    pfioh --forever --httpResponse --swift-storage --createDirsAsNeeded


To use the default password, simply run

.. code-block:: bash
    
    oc create -f example-secret.yml


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
