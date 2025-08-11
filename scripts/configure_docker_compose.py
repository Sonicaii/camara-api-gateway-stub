import yaml
import sys
import re


def configure_camara_api_gateway(config_path: str) -> dict:
    """
    Generates a Docker Compose configuration from a central YAML config file
    that points to OpenAPI v3 specifications and default services extended from 
    docker-compose.common.yaml.

    Args:
        config_path: Path to the main YAML configuration file.

    Returns:
        A dictionary representing the generated configuration.
    """
    try:
        with open(config_path, "r") as f:
            main_config = yaml.safe_load(f)
    except FileNotFoundError:
        print(
            f"Error: Configuration file not found at '{config_path}'", file=sys.stderr
        )
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Could not parse YAML file. {e}", file=sys.stderr)
        sys.exit(1)

    services = {}
    services["ingress"] = {
        "extends": {
            "file": "docker-compose.common.yaml",
            "service": "nginx",
        },
    }

    services["camara-api-gateway"] = {
        "extends": {
           "file": "docker-compose.common.yaml",
            "service": "camara-api-gateway", 
        },
    }

    services["keycloak"] = {
        "extends": {
           "file": "docker-compose.common.yaml",
            "service": "keycloak", 
        },
    }

    services["postgres"] = {
        "extends": {
           "file": "docker-compose.common.yaml",
            "service": "postgres", 
        },
    } 

    for apis_config in main_config.get("apis", []):
        base_path = apis_config.get("base_path")

        if not all([base_path]):
            print(
                f"Warning: Skipping an API due to missing, 'base_path'", file=sys.stderr
            )
            continue

        path = f"./specifications{base_path}/openapi.yaml"
        try:
            with open(path, "r") as spec_file:
                spec = yaml.safe_load(spec_file)
        except FileNotFoundError:
            print(f"Error reading spec from {path}: {e}", file=sys.stderr)
            continue
        except yaml.YAMLError as e:
            print(f"Error parsing spec from {path}: {e}", file=sys.stderr)
            continue

        if "openapi" not in spec or not spec["openapi"].startswith("3."):
            print(
                f"Warning: Skipping spec from {path} as it's not a valid OpenAPI v3 spec.",
                file=sys.stderr,
            )
            continue

        service_name = f"{spec['info']['title'].replace(' ', '-').lower()}-{spec['info']['version'].replace('.', '-')}"

        services[service_name] = {
            'build': {
                'dockerfile': "prism.Dockerfile"
            },
            "volumes": [
                f"./specifications{base_path}:/tmp:ro"
            ],
            "command": ["mock", "-h", "0.0.0.0", "/tmp/openapi.yaml"],
            "networks": ["camara"]
        }

    return {
        "services": services,
        "networks": {"camara": {}}
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python configure_camara_api_gateway.py <path_to_config_yaml>")
        print("\nExample:")
        print("  python configure_camara_api_gateway.py ./config.yaml")
        sys.exit(1)

    config_file = sys.argv[1]
    final_config = configure_camara_api_gateway(config_file)

    print("# Generated CAMARA API Gateway Configuration")
    print("---")
    yaml.dump(final_config, sys.stdout, sort_keys=False, default_flow_style=False)
