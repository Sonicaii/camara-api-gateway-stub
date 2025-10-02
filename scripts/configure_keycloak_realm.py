import yaml
import sys
import json


def configure_keycloak_realm(config_path: str) -> dict:
    """
    Generates a Keycloak realm configuration from a central YAML config file
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

    realm_configuration_file = "./keycloak/realms/realm.json"
    try:
        with open(realm_configuration_file, "r") as f:
            realm = json.load(f)
    except FileNotFoundError:
        print(
            f"Error: Realm configuration file not found at '{realm_configuration_file}'",
            file=sys.stderr,
        )
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Could not parse JSON file. {e}", file=sys.stderr)
        sys.exit(1)

    scopes = set()

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

        service_name = f"api{base_path.replace('/', '-').lower()}"

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
            continue

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

                if "security" in operation:
                    for security_req in operation["security"]:
                        if scheme_name in security_req:

                            for scope in security_req.get(scheme_name, []):
                                scopes.add(scope)

    client_scopes = realm.get("clientScopes", [])
    for scope in scopes:
        client_scopes.append(
            {
                "name": scope,
                "description": "number verification verify scope",
                "protocol": "openid-connect",
                "attributes": {
                    "include.in.token.scope": "true",
                    "display.on.consent.screen": "true",
                },
            }
        )

    realm["clientScopes"] = client_scopes

    for client in realm.get("clients", []):
        default_scopes = client.get("defaultClientScopes", [])
        for scope in scopes:
            default_scopes.append(scope)
        client["defaultClientScopes"] = default_scopes

        optional_scopes = client.get("optionalClientScopes", [])
        for scope in scopes:
            optional_scopes.append(scope)
        client["optionalClientScopes"] = optional_scopes

    return realm


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python configure_keycloak_realm.py <path_to_config_yaml>")
        print("\nExample:")
        print("  python configure_keycloak_realm.py ./config.yaml")
        sys.exit(1)

    config_file = sys.argv[1]
    final_config = configure_keycloak_realm(config_file)

    json.dump(final_config, sys.stdout, sort_keys=False, indent=2)
