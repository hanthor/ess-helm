<!--
Copyright 2024 New Vector Ltd

SPDX-License-Identifier: AGPL-3.0-only OR LicenseRef-Element-Commercial
-->

# Element Server Suite Community Helm Chart

A Helm Chart to deploy the Element Server Suite (ESS).

**This readme is primarily aimed at developing on the chart. The user readme is at
[charts/matrix-stack/README.md](charts/matrix-stack/README.md)**

## Overview

Element Server Suite Community Edition allows you to deploy an official Element Matrix Stack using the very same helm-charts we used for our own production deployments. It allows you to very quickly configure a matrix stack supporting all the latest Matrix Features :

- Element X
- Next Gen Matrix Authentication
- Synapse Workers to scale your deployment
- …

ESS Community Edition configures the following components automatically. It is possible to enable/disable each one of them on a per-component basis. The can also be customized using dedicated values :

- HAProxy : Provides the routing to Synapse processes and Matrix Authentication Service
- Synapse : Provides the matrix homeserver, allowing you to communicate with the full matrix network.
- Matrix Authentication Service: Handles the authentication of your users, compatible with Element X.
- Element Web : This is the official Matrix Web Client provided by Element
- PostgreSQL : The installation comes with a packaged PostgreSQL server. It allows you to quickly set up the stack. For a better long-term experience, please consider using your own PostgreSQL server installed with your system packages.

# How to install

The documentation below assumes it is running on a dedicated server. If you wish to install ESS on a machine sharing other services, you might have a reverse proxy already installed. See the dedicated section if you need to configure ESS behind this reverse proxy.

## Prerequisites

You need to choose what your user's server name is going to be. Their server name is the server address part of their Matrix IDs. In the following user matrix id example, “server-name.tld” is the server name, and have to point to your Element Community Edition installation :  @alice:server-name.tld

## Preparing the environment

### DNS

You need to create 4 DNS entries to set up the Element Server Suite Community Edition. All of these DNS entries must point to your server.

- Server Name: This DNS should point to the cluster ingress. It should be the “server-name.tld” you chose above.
- Synapse : For example “matrix.\<server-name.tld\>”
- Matrix Authentication Service: For example “auth.\<server-name.tld\>”
- Element Web: This will be the address of the chat client of your server. For example “chat.\<server-name.tld”

### K3S \- Kubernetes Single Node

This guide suggests using K3S as the Kubernetes Node hosting ESS. Other options are possible, you can have your own Kubernetes cluster already, or use other clusters like [microk8s](https://microk8s.io/). Any Kubernetes distribution is compatible with Element Community Edition, so choose one according to your needs.

This will install K3S on the node, and configure its Traefik proxy automatically. If you want to configure K3S behind an existing reverse proxy on the same node, please see the dedicated section.

Run the following command to install K3S :

```
curl -sfL https://get.k3s.io | sh -
```

Once k3s is setup,  copy it’s kubeconfig to your home directory to get access to it :

```
mkdir ~/.kube
export KUBECONFIG=~/.kube/config
sudo k3s kubectl config view --raw > "$KUBECONFIG"
chmod 600 "$KUBECONFIG"
```

Install Helm, the Kubernetes Package Manager :

```
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

Create your Kubernetes Namespace where you will deploy the Element Server Suite Community Edition :

```
kubectl create namespace ess
```

Create a directory containing your Element Server Suite configuration values :

```
mkdir ~/ess-config-values
```

### Certificates

We present here 3 main options to set up certificates in Element Server Suite. To configure Element Server Suite behind an existing reverse proxy already serving TLS, you can skip this section.

#### Lets Encrypt

To use Let’s Encrypt with ESS Helm, you should use [Cert Manager](https://cert-manager.io/). This is a Kubernetes component which allows you to get certificates issues by an ACME provider. The installation follows the [official manual](https://cert-manager.io/docs/installation/helm/) :

Add Helm Jetstack Repository :

```
helm repo add jetstack https://charts.jetstack.io --force-update
```

Install Cert-Manager :

```
helm install \
  cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.17.0 \
  --set crds.enabled=true
```

Configure Cert-Manager to allow Element Server Suite Community Edition to request Let’s Encrypt certificates automatically. Create a “ClusterIssuer” resource in your k3s node to do so :

```
export USER_EMAIL=<your email>

kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: $USER_EMAIL
    privateKeySecretRef:
      name: letsencrypt-prod-private-key
    solvers:
      - http01:
          ingress:
            class: traefik
EOF
```

In your ess configuration values directory, create a file named “letsencrypt.yaml” containing :

```
ingress:
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod

# Configure the TLS Secret names created by Cert Manager below
elementWeb:
  ingress:
    tlsSecret: le-chat-tls

synapse:
  ingress:
    tlsSecret: le-matrix-tls

matrixAuthenticationService:
  ingress:
    tlsSecret: le-auth-tls

wellKnownDelegation:
  ingress:
    tlsSecret: le-well-known-tls
```

#### Certificate File

Import your certificate file in your namespace using [kubectl](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_create/kubectl_create_secret_tls/) :

```

kubectl create secret tls ess-certificate --cert=path/to/cert/file --key=path/to/key/file
```

If you have multiple certificates for each of your DNS names, you can run the command for each certificate to import, with a new name instead of “ess-certificate”.

In your ess configuration values directory, create a file named “certificate.yaml” containing :

```
elementWeb:
  ingress:
    tlsSecret: ess-certificate  # Adjust to Element Web Client TLS secret name if you create one for each DNS entry

synapse:
  ingress:
    tlsSecret: ess-certificate  # Adjust to Synapse TLS secret name if you create one for each DNS entry

matrixAuthenticationService:
  ingress:
    tlsSecret: ess-certificate  # Adjust to Matrix Authentication Service TLS secret name if you create one for each DNS entry

wellKnownDelegation:
  ingress:
    tlsSecret: ess-certificate  # Adjust to your Server Name TLS secret name if you create one for each DNS entry


```

### Configuring the database

This is optional but recommended.

You can use the database provided with ESS Community Edition, or use your own PostgreSQL Server. We recommend using a PostgreSQL server installed with your own distribution packages. For a quick set up, feel free to use the included postgres server.

#### Use of an existing postgres database

You need to create 2 databases :

- For Synapse [https://element-hq.github.io/synapse/v1.59/postgres.html\#set-up-database](https://element-hq.github.io/synapse/v1.59/postgres.html#set-up-database)

- For MAS [https://element-hq.github.io/matrix-authentication-service/setup/database.html](https://element-hq.github.io/matrix-authentication-service/setup/database.html)


To configure your own Postgres Database in your installation, create a file named “postgresql.yaml” in your ess configuration values directory :

```
synapse:
  postgres:
    host: # PostgreSQL database host
    port: 5432 # PostgreSQL port
    user: # PostgreSQL username
    password:
      value:  ## Postgres Password
    database: # PostgreSQL database name
    sslMode: prefer # TLS settings to use for the PostgreSQL connection

matrixAuthenticationService:
  postgres:
    host: # PostgreSQL database host
    port: 5432 # PostgreSQL port
    user: # PostgreSQL username
    password:
      value:  ## Postgres Password
    database: # PostgreSQL database name
    sslMode: prefer # TLS settings to use for the PostgreSQL connection
```

## Installation

Element Server Suite installation is done with Helm Package Manager. Helm requires to configure a values file according to Element Server Suite documentation.

#### Quick setup

For a quick setup using Element Server Suite default settings, write the following file named “hostnames.yaml” in your ess configuration values directory :

```
# The server name of your installation (That you chose when creating the DNS entries)
serverName: ess.localhost

synapse:
  ingress:
    host: # The DNS name of synapse. For example matrix.<server-name.tld>

matrixAuthenticationService:
  ingress:
    host: # The DNS name of Matrix Authentication Service. For example auth.<server-name.tld>

elementWeb:
  ingress:
    host: # The DNS name of Element Web Client. For example chat.<server-name.tld>
```

Run the setup using the following helm command. This command supports combining multiple values files depending on your setup. Typically you would pass to the command line a combination of :

- If using Lets Encrypt : `-f ~/ess-config-values/letsencrypt.yaml`
- If using Certificate Files : `-f ~/ess-config-values/certificate.yaml`
- If using your own PostgreSQL server : `-f ~/ess-config-values/postgresql.yaml`

#### Dev Installation (Temporary)

Create a ghcr.io secret:

```
kubectl create secret -n ess docker-registry ghcr --docker-username=user --docker-password=<github token> --docker-server=ghcr.io
```

Create a values file called ghcr.yaml in your ess configuration values directory for GHCR credentials: 

```
imagePullSecrets:
  - name: ghcr
```

Login helm against ghcr.io:

```
helm registry login -u <github username> ghcr.io
```


Finally, install ess, making sure to use the dev version by adding \--version 0.5.1-dev and including the ghcr.yaml values file:

```
helm upgrade --install --namespace "ess" ess oci://ghcr.io/element-hq/ess-helm/matrix-stack --version 0.5.1-dev -f ~/ess-config-values/hostnames.yaml -f ~/ess-config-values/ghcr.yaml <values files to pass> --wait
```

#### Standard Installation

```
helm upgrade --install --namespace "ess" ess oci://ghcr.io/element-hq/ess-helm/matrix-stack -f ~/ess-config-values/hostnames.yaml <values files to pass> --wait
```

Wait for the helm command to finish up. ESS is now installed \!

#### Create initial user

Element Server Suite Community Edition does not allow user registration by default. To create your initial user, use the “mas-cli manage register-user” command in the Matrix Authentication Service pod :

```
kubectl exec -n ess -it deploy/ess-matrix-authentication-service -- mas-cli manage register-user

Defaulted container "matrix-authentication-service" out of: matrix-authentication-service, render-config (init), db-wait (init), config (init)
✔ Username · alice
User attributes
    	Username: alice
   	Matrix ID: @alice:thisservername.tld
No email address provided, user will be prompted to add one
No password or upstream provider mapping provided, user will not be able to log in

Non-interactive equivalent to create this user:

 mas-cli manage register-user --yes alice

✔ What do you want to do next? (<Esc> to abort) · Set a password
✔ Password · ********
User attributes
    	Username: alice
   	Matrix ID: @alice:thisservername.tld
    	Password: ********
No email address provided, user will be prompted to add one

```

### Verifying the setup

To verify the setup, you should :

* Log into your Element Web Client website and log in with the user you created above
* Verify that Federation Works fine using [Matrix Federation Tester](https://federationtester.matrix.org/)
* Login with Element X mobile client with the user you created above

## Configuring Element Server Suite

Element Server Suite Community Edition allows you to configure a lot of values. You will find below the main settings you would want to configure :

#### Configure Element Web Client

Element Web configuration is written in JSON. The documentation can be found in [Element Web repository.](https://github.com/element-hq/element-web/blob/develop/docs/config.md)

To implement Element Web configuration in Element Server Suite, create a values file with the json config to inject under “additional” :

```
elementWeb:
  additional: {
    "some": "settings"
  }
```

#### Configure Synapse

Synapse configuration is written in YAML. The documentation can be found in [https://element-hq.github.io/synapse/latest/usage/configuration/config\_documentation.html](https://element-hq.github.io/synapse/latest/usage/configuration/config_documentation.html)

```
synapse:
  additional:
    user-config.yaml:
      config: |
        # Add your settings below, taking care of the spacing indentation
        some: settings
```

#### Configure Matrix Authentication Service

Matrix Authentication Service configuration is written in YAML. The documentation can be found in [https://element-hq.github.io/matrix-authentication-service/reference/configuration.html](https://element-hq.github.io/matrix-authentication-service/reference/configuration.html)

```
matrixAuthenticationService:
  additional:
    user-config.yaml:
      config: |
        # Add your settings below, taking care of the spacing indentation
        some: settings
```

## Advanced configuration

### Values documentation

 The helm chart values documentation is available in :

- The github repository [values files](https://github.com/element-hq/ess-helm/blob/main/charts/matrix-stack/values.yaml)
- Artifacthub.io

Configuration samples are available [in the github repository](https://github.com/element-hq/ess-helm/tree/main/charts/matrix-stack/ci).

### Set up Element Server Suite on a server  with an existing reverse proxy

If your server already has a reverse proxy, the port 80 and 443 are already used by it.

In such a case, you will need to set up K3S with custom ports. Create a file `/var/lib/rancher/k3s/server/manifests/traefik-config.yaml` with the following content :

```
apiVersion: helm.cattle.io/v1
kind: HelmChartConfig
metadata:
  name: traefik
  namespace: kube-system
spec:
  valuesContent: |-
    ports:
      web:
        exposedPort: 8080
      websecure:
        exposedPort: 8443
```

Configure your reverse proxy so that the DNS Names you configured are serving to localhost on the port 8080 (HTTP) and 8443 (HTTPS).

## Uninstallation

If you wish to remove ESS from your cluster, you can simply run the following commands to clean up the installation. Please note deleting the `ess` namespace will remove everything within it, including any resources you may have manually created within it:

```
helm uninstall ess -n ess
kubectl delete namespace ess
```

If you want to also uninstall other components installed in this guide, you can do so using the following commands:

```
# Remove cert-manager from cluster
helm uninstall cert-manager -n cert-manager

# Uninstall helm
rm -rf /usr/local/bin/helm $HOME/.cache/helm $HOME/.config/helm $HOME/.local/share/helm

# Uninstall k3s
/usr/local/bin/k3s-uninstall.sh
```
