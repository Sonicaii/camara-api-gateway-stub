# CAMARA API Stubs

This project implements stubbing for the [CAMARA APIs](https://camaraproject.org/)

## TL;DR

For experienced developers with all prerequisites installed

```shell
# Install python dependencies
uv sync

# Configure services and download API specs
make all

# Create and populate your environment file
cp .env.example .env
# --> now edit .env and fill in values for your environment

# Start all services
make start

# Follow the steps below to get an access token and test an API
# ...

# Stop all services when finished
make stop
```

## Why does this exist

This project was originally developed to assist University of Melbourne students developing against CAMARA APIs as part of the requirement for [IT Project (COMP30022)](https://handbook.unimelb.edu.au/subjects/comp30022). At the time, access to live CAMARA APIs was limited, and this project was created to enable student project groups to prototype against reliable stubs.

It remains a useful tool for any developer or team that needs to simulate the CAMARA API ecosystem for prototyping, testing, or development purposes.

## Architecture

This project deploys and manages the following services:

![Architecture](/docs/architecture.drawio.png)

- [Prism](https://stoplight.io/open-source/prism) - OpenAPI mock server, used to deliver CAMARA API stubs that validate incoming requests and return example responses
- [Keycloak](https://www.keycloak.org/) - OpenID Connect (OIDC) compliant Auth Server, used to simulate OIDC flows that protect CAMARA APIs
- [nginx](https://nginx.org/en/) - Reverse proxy, simulates TLS
- [Spring Cloud Gateway](https://spring.io/projects/spring-cloud-gateway) - an API gateway that exposes CAMARA APIs and enforces OIDC security according to CAMARA OpenAPI specifications

## Usage

### Prerequisites

This project assumes you have access to the following tools:

- [Docker](https://www.docker.com/) - consider installing [Docker Desktop](https://docs.docker.com/desktop/), other systems such as Podman are a available but this project has only been verified with Docker Desktop
- [Docker Compose](https://docs.docker.com/compose/) - a tool for running multi-container applications, used to simplify starting the stub services - installed with most Docker installations
- [uv](https://docs.astral.sh/uv/) - a package and project manager for Python, used to run a number of scripts that that configure the gateway
- [curl](https://curl.se/docs/manpage.html) - pre-installed on most OS, used in examples in this guide
- [jq](https://jqlang.org/) - a utility for working with JSON, used in examples in this guide to extract data from responses
- [make](https://www.gnu.org/software/make/manual/make.html) - a build tool, used to run custom scripts, such as fetching CAMARA API specifications, or preparing certificates for TLS
- [openssl](https://www.openssl.org/) - a utility for working with TLS, used to generate private keys and certificates
- a browser - any will do

> IMPORTANT (Windows users): This project assumes a unix-like environment, [Windows Subsystem for Linux (WSL)](https://learn.microsoft.com/en-us/windows/wsl/) is recommended. PRs welcome for Windows users that get this guide working outside WSL :).

#### Networking

> IMPORTANT: This is a critical step. Gateway services will not be accessible from your browser or terminal if you do not perform this action.

You will need to add a number of hosts to your OS known hosts list - `/etc/hosts` on unix-like machines, add:

```shell
127.0.0.1 poochie.example.com
```

### Set-up ([day-1 operations (ops)](https://octopus.com/blog/difference-between-day-0-1-2-operations) configuration)

Primary day-1 ops targets are the configuration of TLS and sourcing CAMARA API specifications.

Day-1 ops scripts require `uv`, [install `uv`](https://docs.astral.sh/uv/getting-started/installation/) and initialize the project

```shell
uv sync
```

All day-1 ops can be triggered via the provided `Makefile`

```shell
make all
```

`make all` will:

- Create a Certificate Authority and server certificates for Nginx
- Download CAMARA OpenAPI specifications declared in `apis.yaml`
- Generate an `application.yaml` configuration file for the CAMARA API Gateway
- Generate a `docker-compose.yaml` to start all gateway services

#### Sourcing CAMARA APIs

OpenAPI v3 specifications for each CAMARA API can be accessed via the project's official [GitHub Organization](https://github.com/camaraproject/). this project provides a simple script to fetch CAMARA API specifications and configure the gateway accordingly.

To add APIs to the stub system add entries to `apis.yaml`, and example for the [Number Verification API](https://github.com/camaraproject/NumberVerification) is provided. Each entry must declare:

- `spec` - a link to the raw OpenAPI v3 CAMARA API specification to be stubbed
- `base_path`: - the base path that the CAMARA API Gateway should serve the stub. Left to the user to configure but a common convention is to follow the following format `/<api-name>/<api-major-version>` - make sure that this base path is unique to each stub.

If you update APIs declared in `apis.yaml`, run make to re-configure the Gateway and Docker Compose:

```shell
make all
```

#### TLS

CAMARA APIs are protected by TLS and this project makes efforts to simulate that.

> A key limitation of this project is that the certificates generated by default are self signed, if you use these certificates you will need to add these certificates to the list of certificates trusted by your OS and possibly any http client you use in a consuming project. A simply why to trust these certificates is to visit the [Keycloak Admin UI](https://poochie.example.com/auth/) and proceed when your browser prompts you.

### Start

Copy `.env.example`, rename to `.env`, and set values for `<value>`,

Start all gateway services:

```shell
make start
```

Acquire an access token via the Authorization Code Flow (Curity provides a good [guide](https://curity.io/resources/learn/openid-code-flow/), or see Appendix below). Note that Keycloak is configured with a single client for this purpose, it's details can be discovered in `./keycloak/realms/realm.json`, and below for convenience:

| attribute | value |
| ---- | --- |
| client_id | developer-client |
| client_secret | Yqp2jao1Ruc8UBwk7jwAIJ6Y1jsVT4qJHvQVpduK |

The following Keycloak endpoints (exposed via the gateway) will also be of use:

| endpoint | url |
| ---- | ---- |
| authorization | <https://poochie.example.com/auth/realms/operator/protocol/openid-connect/auth> |
| token | <https://poochie.example.com/auth/realms/operator/protocol/openid-connect/token> |

Keycloak is also configured with a single test user that can be used to login:

- username: rex@poochie.com
- password: password

```shell
export ACCESS_TOKEN=<access-token>
```

Providing the access token as bearer authorization, make a request to the Number Verification API:

```shell
curl -ikX POST https://poochie.example.com/camara/number-verification/v1/verify -H "Authorization: Bearer ${ACCESS_TOKEN}" -d '{"phoneNumber": "+61234567890"}' -H "Content-Type: application/json"
```

Finally, once you are done, stop the gateway services

```shell
make stop
```

## Caveats and issues

- Keycloak is configured to import the gateway realm on start up, however this only occurs if the realm does not yet exist. If you make changes to `apis.yaml` or the realm configuration directly you will need to purge the database - simply trash the `./data` directory and restart the services

## Appendix

### Obtain an Access Token

To call the secure APIs, you must first get an access token from the Keycloak server using the OIDC Authorization Code Flow.

**Step 1:** Get an Authorization Code
Construct the following URL and paste it into your browser.

```shell
https://poochie.example.com/auth/realms/operator/protocol/openid-connect/auth?client_id=developer-client&redirect_uri=http://localhost:8080/callback&response_type=code&scope=openid
```

**Step 2:** Authenticate
Your browser will show a Keycloak login page. Because the project uses self-signed certificates, you may need to accept a browser security warning. Log in with the pre-configured test user:

- username: rex@poochie.com
- password: password

**Step 3:** Extract the Code
After logging in, Keycloak will redirect you to `http://localhost:8080/callback...`. The page won't load (this is expected), but the URL in your browser's address bar will contain the authorization code. Copy the value of the code parameter from the URL.

It will look something like this: `http://localhost:8080/callback?session_state=...&iss=...&code=1a2b3c4d-5e6f-7890-abcd-ef1234567890`

**Step 4:** Exchange the Code for an Access Token
Use the code you just copied in the following curl command to get an access token. Replace `<PASTE_YOUR_CODE_HERE>` with your code.

```shell
export AUTH_CODE="<PASTE_YOUR_CODE_HERE>"

curl -sX POST https://poochie.example.com/auth/realms/operator/protocol/openid-connect/token \
-d "grant_type=authorization_code" \
-d "client_id=developer-client" \
-d "client_secret=Yqp2jao1Ruc8UBwk7jwAIJ6Y1jsVT4qJHvQVpduK" \
-d "code=${AUTH_CODE}" \
-d "redirect_uri=http://localhost:8080/callback"
```

**Step 5:** Export the Access Token
The command above will return a JSON object containing the access_token. You can use jq to extract it and export it as an environment variable for easy use.

Re-run the command above, but pipe the output to jq to extract the token

```shell
export ACCESS_TOKEN=$(curl -sX POST https://poochie.example.com/auth/realms/operator/protocol/openid-connect/token -d "grant_type=authorization_code" -d "client_id=developer-client" -d "client_secret=Yqp2jao1Ruc8UBwk7jwAIJ6Y1jsVT4qJHvQVpduK" -d "code=${AUTH_CODE}" -d "redirect_uri=http://localhost:8080/callback" | jq -r .access_token)
```

Verify the token is set

```shell
echo $ACCESS_TOKEN
```
