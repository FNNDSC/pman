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