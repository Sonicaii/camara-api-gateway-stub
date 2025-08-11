# Certificate attributes
C = AU
ST = Victoria
L = Melbourne
O = PoochieOrg
OU = OpenGateway Stubs
CN_CA = PoochieCA
CN_SERVER = poochie.example.com

# File names
TLS_DIR = tls
CA_KEY = $(TLS_DIR)/$(CN_CA).key.pem
CA_CERT = $(TLS_DIR)/$(CN_CA).cert.pem
CA_CONFIG = $(TLS_DIR)/$(CN_CA)_config.txt

SERVER_KEY = $(TLS_DIR)/$(CN_SERVER).key.pem
SERVER_CSR = $(TLS_DIR)/$(CN_SERVER).csr.pem
SERVER_CERT = $(TLS_DIR)/$(CN_SERVER).cert.pem
SERVER_CONFIG = $(TLS_DIR)/$(CN_SERVER)_config.txt

APIS = apis.yaml

.PHONY: all
all: ca server  apis

ca: $(TLS_DIR) $(CA_KEY) $(CA_CERT)

$(TLS_DIR):
	mkdir $(TLS_DIR)

$(CA_KEY): 
	openssl genrsa -out $(CA_KEY) 4096

$(CA_CONFIG): 
	echo "[ req ]" > $(CA_CONFIG)
	echo "prompt = no" >> $(CA_CONFIG)
	echo "distinguished_name = req_distinguished_name" >> $(CA_CONFIG)
	echo "[ req_distinguished_name ]" >> $(CA_CONFIG)
	echo "C = $(C)" >> $(CA_CONFIG)
	echo "ST = $(ST)" >> $(CA_CONFIG)
	echo "L = $(L)" >> $(CA_CONFIG)
	echo "O = $(O)" >> $(CA_CONFIG)
	echo "OU = $(OU)" >> $(CA_CONFIG)
	echo "CN = $(CN_CA)" >> $(CA_CONFIG)

$(CA_CERT): $(CA_KEY) $(CA_CONFIG)
	openssl req -x509 -new -nodes -key $(CA_KEY) -sha256 -days 3650 -out $(CA_CERT) -config $(CA_CONFIG)

server: $(TLS_DIR) $(SERVER_KEY) $(SERVER_CSR) $(SERVER_CERT)

$(SERVER_KEY): 
	openssl genrsa -out $(SERVER_KEY) 2048

$(SERVER_CONFIG): 
	echo "[ req ]" > $(SERVER_CONFIG)
	echo "prompt = no" >> $(SERVER_CONFIG)
	echo "distinguished_name = req_distinguished_name" >> $(SERVER_CONFIG)
	echo "[ req_distinguished_name ]" >> $(SERVER_CONFIG)
	echo "C = $(C)" >> $(SERVER_CONFIG)
	echo "ST = $(ST)" >> $(SERVER_CONFIG)
	echo "L = $(L)" >> $(SERVER_CONFIG)
	echo "O = $(O)" >> $(SERVER_CONFIG)
	echo "OU = $(OU)" >> $(SERVER_CONFIG)
	echo "CN = $(CN_SERVER)" >> $(SERVER_CONFIG)

$(SERVER_CSR): $(SERVER_KEY) $(SERVER_CONFIG)
	openssl req -new -key $(SERVER_KEY) -out $(SERVER_CSR) -config $(SERVER_CONFIG)

$(SERVER_CERT): $(SERVER_CSR) $(CA_CERT) $(CA_KEY)
	openssl x509 -req -in $(SERVER_CSR) -CA $(CA_CERT) -CAkey $(CA_KEY) -CAcreateserial -out $(SERVER_CERT) -days 365 -sha256

.PHONY: apis
apis: specifications docker-compose.yaml application.yaml

specifications: $(APIS)
	uv run scripts/download_specifications.py $(APIS)

docker-compose.yaml: $(APIS)
	uv run scripts/configure_docker_compose.py $(APIS) > docker-compose.yaml

application.yaml: $(APIS)
	uv run scripts/configure_camara_api_gateway.py $(APIS) > application.yaml

.PHONY: clean
clean: clean-tls clean-apis clean-data

.PHONY: clean-tls
clean-tls:
	rm -f $(CA_KEY) $(CA_CERT) $(CA_CONFIG) $(SERVER_KEY) $(SERVER_CSR) $(SERVER_CERT) $(SERVER_CONFIG) *.srl

.PHONY: clean-apis
clean-apis:
	rm -r specifications
	rm docker-compose.yaml
	rm application.yaml

.PHONY: clean-data
clean-data:
	rm -r data

.PHONY: start
start:
	docker compose up -d --build

.PHONY: stop
stop:
	docker compose down
