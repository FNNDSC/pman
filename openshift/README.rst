##############
Example Kube Config Setup:
##############

.. code-block:: bash

    sudo oc login -u system:admin
    sudo oc create sa robot -n myproject
    sudo oc describe sa robot -n myproject
    sudo oc adm policy add-role-to-user edit system:serviceaccount:myproject:robot -n myproject
    sudo oc describe secret <Ex: robot-token-4vhxc> -n myproject
    rm -f ~/.kube/config
    oc login --token=<token from above>    # Note: Use 172.30.0.1:443 if running with oc cluster up
    oc project myproject
    oc create secret generic kubecfg --from-file=/home/dmcphers/.kube/config -n myproject
    rm -f ~/.kube/config
    oc login
    oc new-app openshift/pman-openshift-template.json

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
Creating a secret
**************
1) Create a text file with the name swift-credentials.cfg as shown above.


2) Now run the following command to create a secret

.. code-block:: bash

    oc create secret generic swift-credentials --from-file=<path-to-file>/swift-credentials.cfg