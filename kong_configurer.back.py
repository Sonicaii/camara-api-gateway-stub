import yaml
import sys
import json

def generate_kong_config(openapi_spec_path: str, service_name: str, service_url: str, issuer_url: str) -> dict:
    """
    Generates a Kong declarative configuration from an OpenAPI v3 specification.

    Args:
        openapi_spec_path: Path to the OpenAPI v3 specification file (YAML or JSON).
        service_name: The name for the Kong service.
        service_url: The upstream URL for the Kong service.
        issuer_url: The issuer URL for the OIDC provider (for the jwt-oidc plugin).

    Returns:
        A dictionary representing the Kong declarative configuration.
    """
    try:
        with open(openapi_spec_path, 'r') as f:
            spec = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: OpenAPI spec file not found at '{openapi_spec_path}'")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Could not parse YAML file. {e}")
        sys.exit(1)

    if 'openapi' not in spec or not spec['openapi'].startswith('3.'):
        print("Error: The provided file is not a valid OpenAPI v3 specification.")
        sys.exit(1)

    kong_routes = []

    # Find the name of the OAuth2 security scheme
    oauth_scheme_name = None
    if 'components' in spec and 'securitySchemes' in spec['components']:
        for name, scheme in spec['components']['securitySchemes'].items():
            if scheme.get('type') == 'oauth2':
                oauth_scheme_name = name
                break
    
    if not oauth_scheme_name:
        print("Warning: No OAuth2 security scheme found in components.securitySchemes. Cannot map scopes.")

    # Iterate over all paths and methods to generate routes
    for path, path_item in spec.get('paths', {}).items():
        for method, operation in path_item.items():
            # Supported methods in OpenAPI spec for operations
            if method.lower() not in ['get', 'post', 'put', 'patch', 'delete', 'options', 'head']:
                continue

            operation_id = operation.get('operationId', f"{method}-{path.replace('/', '-')}")
            route_name = f"{service_name}-{operation_id}"
            
            route = {
                'name': route_name,
                'paths': [path],
                'methods': [method.upper()],
                'strip_path': False, # Usually safer to set to false
                'plugins': []
            }

            # Check for security requirements on the operation
            if 'security' in operation and oauth_scheme_name:
                for security_req in operation['security']:
                    if oauth_scheme_name in security_req:
                        scopes = security_req[oauth_scheme_name]
                        if scopes:
                            jwt_oidc_plugin = {
                                'name': 'jwt-oidc',
                                'config': {
                                    'issuer': issuer_url,
                                    'scopes_required': scopes,
                                    'scopes_claim': ['scope']
                                }
                            }
                            route['plugins'].append(jwt_oidc_plugin)
                        break # Assume first matching scheme is the one to use

            kong_routes.append(route)

    # Assemble the final Kong declarative configuration
    kong_config = {
        '_format_version': '2.1',
        'services': [{
            'name': service_name,
            'url': service_url,
            'routes': kong_routes
        }]
    }

    return kong_config

if __name__ == '__main__':
    if len(sys.argv) != 5:
        print("Usage: python generate_kong_config.py <path_to_openapi_spec> <kong_service_name> <kong_service_url> <oidc_issuer_url>")
        print("\nExample:")
        print("  python generate_kong_config.py ./openapi.yaml my-api http://my-api-service:8080 https://idp.example.com/auth/realms/my-realm")
        sys.exit(1)

    spec_file = sys.argv[1]
    service_name_arg = sys.argv[2]
    service_url_arg = sys.argv[3]
    issuer_url_arg = sys.argv[4]

    final_config = generate_kong_config(spec_file, service_name_arg, service_url_arg, issuer_url_arg)

    # Print the final configuration as YAML
    print("# Generated Kong Declarative Configuration")
    print("---")
    yaml.dump(final_config, sys.stdout, sort_keys=False, default_flow_style=False)

