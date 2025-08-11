import yaml
import sys
import re


def configure_camara_api_gateway(config_path: str) -> dict:
    """
    Generates a CAMARA API Gateway configuration from a central YAML config file
    that points to OpenAPI v3 specifications.

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

    routes = []

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

        scheme_name = None
        if "components" in spec and "securitySchemes" in spec["components"]:
            for name, scheme in spec["components"]["securitySchemes"].items():
                if scheme.get("type") == "openIdConnect":
                    scheme_name = name
                    break

        if not scheme_name:
            print(
                f"Warning: No OpenID Connect security scheme found for '{service_name}'. Cannot map scopes.",
                file=sys.stderr,
            )

        for path, path_item in spec.get("paths", {}).items():
            for method, operation in path_item.items():
                if method.lower() not in [
                    "get",
                    "post",
                    "put",
                    "patch",
                    "delete",
                    "options",
                    "head",
                ]:
                    continue

                # Convert OpenAPI path parameters ({param}) to a regex-friendly format
                # This simple regex matches any character except a slash.
                spec_path_regex = re.sub(r"\{[^}]+\}", r"[^/]+", path)

                operation_id = operation.get(
                    "operationId", f"{method}-{path.replace('/', '-')}"
                )
                route_name = f"{service_name}-{operation_id}"

                route = {
                    "id": route_name,
                    "uri": f"http://{service_name}:4010",
                    "predicates": [
                        f"Path={base_path}{spec_path_regex}",
                        f"Method={method.upper()}",
                    ],
                    "filters": [
                        {
                            "name": "RewritePath",
                            "args": {
                                "regexp": f"{base_path}/(?<segment>.*)",
                                "replacement": "/$\{segment}",
                            },
                        }
                    ],
                }

                if "security" in operation and scheme_name:
                    for security_req in operation["security"]:
                        if scheme_name in security_req:
                            scopes = security_req[scheme_name]
                            if scopes:
                                for scope in scopes:
                                    check_scope = {
                                        "name": "CheckScope",
                                        "args": {
                                            "scope": scope,
                                        },
                                    }
                                    route["filters"].append(check_scope)
                            break

                routes.append(route)

    return {
        "spring": {"cloud": {"gateway": {"server": {"webflux": {"routes": routes}}}}}
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
