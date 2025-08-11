import yaml
import sys
import requests
import os


def download_specifications(config_path: str) -> dict:
    """
    Downloads CAMARA API specifications declared in a central YAML config file
    that points to multiple remote OpenAPI v3 specifications.

    Args:
        config_path: Path to the main YAML configuration file.
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

    for apis_config in main_config.get("apis", []):
        spec_url = apis_config.get("spec")
        base_path = apis_config.get("base_path")

        if not all([base_path, spec_url]):
            print(
                f"Warning: Skipping an API due to missing, 'base_path', or 'spec'.",
                file=sys.stderr,
            )
            continue

        try:
            response = requests.get(spec_url)
            response.raise_for_status()
            spec = yaml.safe_load(response.text)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching spec from {spec_url}: {e}", file=sys.stderr)
            continue
        except yaml.YAMLError as e:
            print(f"Error parsing spec from {spec_url}: {e}", file=sys.stderr)
            continue

        if "openapi" not in spec or not spec["openapi"].startswith("3."):
            print(
                f"Warning: Skipping spec from {spec_url} as it's not a valid OpenAPI v3 spec.",
                file=sys.stderr,
            )
            continue

        dir = f"./specifications{base_path}"
        os.makedirs(dir, exist_ok=True)
        with open(f"{dir}/openapi.yaml", "w") as spec_file:
            yaml.dump(spec, spec_file, sort_keys=False, default_flow_style=False)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python download_specifications.py <path_to_config_yaml>")
        print("\nExample:")
        print("  python download_specifications.py ./config.yaml")
        sys.exit(1)

    config_file = sys.argv[1]
    download_specifications(config_file)
