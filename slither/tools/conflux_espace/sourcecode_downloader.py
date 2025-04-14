import os
import json
import requests
import subprocess
import sys
import re
from importlib.metadata import distributions
from typing import Optional, Dict, Set, Tuple
from collections import defaultdict
from pathlib import Path

def install_dependencies():
    required_packages = {
        'requests': 'requests'
    }
    
    installed_packages = {dist.metadata['Name'] for dist in distributions()}
    
    for package, command in required_packages.items():
        if package.lower() not in installed_packages:
            print(f"[+] Installing {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"[+] {package} installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"[!] Error installing {package}: {e}")
                sys.exit(1)

def get_dependency_info(dependency: str) -> Optional[Dict]:
    try:
        npm_url = f"https://registry.npmjs.org/{dependency}"
        response = requests.get(npm_url)
        
        if response.status_code == 200:
            npm_data = response.json()
            versions = list(npm_data.get('versions', {}).keys())
            if not versions:
                return None
                
            versions.sort(key=lambda x: [int(y) for y in x.split('.')], reverse=True)
            repository = npm_data.get('repository', {})
            repo_url = repository.get('url', '') if isinstance(repository, dict) else str(repository)
            
            github_match = re.search(r'github\.com[:/]([^/]+/[^/]+?)(\.git)?$', repo_url)
            if github_match:
                return {
                    'github': github_match.group(1),
                    'versions': versions,
                    'registry': 'npm',
                    'package': dependency
                }
            
            return {
                'versions': versions,
                'registry': 'npm',
                'package': dependency
            }
                
    except Exception as e:
        print(f"[!] Error fetching dependency info {dependency}: {e}")
    
    return None

def process_imports(content: str, file_path: str, project_dir: str) -> Set[str]:
    dependencies = set()
    import_pattern = r'import\s+(?:{[^}]+}|[^;]+)\s+from\s+["\']([^"\']+)["\']'
    
    for match in re.finditer(import_pattern, content):
        import_path = match.group(1)
        
        if import_path.startswith('@'):
            parts = import_path.split('/')
            package_name = parts[0]
            relative_path = '/'.join(parts[1:])
            
            if setup_dependency(package_name, relative_path, project_dir):
                dependencies.add(package_name)
        else:
            if import_path.startswith('./') or import_path.startswith('../'):
                abs_import_path = os.path.normpath(
                    os.path.join(os.path.dirname(file_path), import_path)
                )
            else:
                abs_import_path = os.path.join(project_dir, 'contracts', import_path)
            
            os.makedirs(os.path.dirname(abs_import_path), exist_ok=True)
            
            if not os.path.exists(abs_import_path):
                for dep in dependencies:
                    dep_path = os.path.join(project_dir, dep, import_path)
                    if os.path.exists(dep_path):
                        os.makedirs(os.path.dirname(abs_import_path), exist_ok=True)
                        if os.name == 'nt':
                            import shutil
                            shutil.copy2(dep_path, abs_import_path)
                        else:
                            os.symlink(dep_path, abs_import_path)
                        break

    return dependencies

def setup_dependency(dependency: str, relative_path: str, project_dir: str) -> bool:
    try:
        dep_info = get_dependency_info(dependency)
        if not dep_info:
            print(f"[!] Could not get info for: {dependency}")
            return False

        full_path = os.path.join(project_dir, dependency, relative_path)
        
        if os.path.exists(full_path):
            return True

        content = fetch_dependency_content(dep_info, relative_path)
        if not content:
            print(f"[!] Could not get content for {dependency}/{relative_path}")
            return False

        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)

        print(f"[+] Dependency saved: {dependency}/{relative_path}")
        return True

    except Exception as e:
        print(f"[!] Error setting up dependency {dependency}: {e}")
        return False

def fetch_dependency_content(dep_info: Dict, file_path: str) -> Optional[str]:
    try:
        if 'github' in dep_info:
            github_url = f"https://raw.githubusercontent.com/{dep_info['github']}/{dep_info['versions'][0]}/{file_path}"
            response = requests.get(github_url)
            if response.status_code == 200:
                return response.text

        if dep_info['registry'] == 'npm':
            npm_url = f"https://registry.npmjs.org/{dep_info['package']}/{dep_info['versions'][0]}"
            response = requests.get(npm_url)
            if response.status_code == 200:
                print(f"[!] NPM fallback not implemented for {dep_info['package']}")

    except Exception as e:
        print(f"[!] Error fetching dependency content: {e}")

    return None

def get_source_code(address: str) -> Tuple[str, str, str, Set[str]]:
    try:
        base_dir = os.getcwd()
        analysis_dir = f"{address}_analysis"
        contracts_dir = os.path.join(analysis_dir, "contracts")
        os.makedirs(contracts_dir, exist_ok=True)

        url = f"https://evmapi.confluxscan.org/api?module=contract&action=getsourcecode&address={address}"
        print(f"[+] Fetching source code from {url}")
        response = requests.get(url)
        data = response.json()

        if data["status"] != "1":
            raise Exception(f"Error fetching source code: {data.get('message', 'Unknown error')}")

        source_code = data["result"][0]["SourceCode"]
        if not source_code:
            raise Exception("No source code found.")

        dependencies = set()
        contract_filename = None

        if source_code.startswith("{"):
            try:
                sources = json.loads(source_code)
                if "sources" in sources:
                    for path, content in sources["sources"].items():
                        if isinstance(content, dict):
                            content = content["content"]
                        
                        if path.startswith("@"):
                            file_path = os.path.join(base_dir, path)
                            dependencies.add(path.split('/')[0])
                            os.makedirs(os.path.dirname(file_path), exist_ok=True)
                            with open(file_path, "w") as f:
                                f.write(content)
                            print(f"[+] Dependency saved: {path}")
                        else:
                            if path.startswith("contracts/"):
                                path = path[len("contracts/"):]
                            file_path = os.path.join(contracts_dir, path)
                            if not contract_filename:
                                contract_filename = path
                            os.makedirs(os.path.dirname(file_path), exist_ok=True)
                            with open(file_path, "w") as f:
                                f.write(content)
                            print(f"[+] Contract saved: {path}")
                else:
                    contract_filename = "contract.sol"
                    contract_path = os.path.join(contracts_dir, contract_filename)
                    with open(contract_path, "w") as f:
                        f.write(source_code)
                    print(f"[+] Contract saved: {contract_filename}")
            except json.JSONDecodeError:
                contract_filename = "contract.sol"
                contract_path = os.path.join(contracts_dir, contract_filename)
                with open(contract_path, "w") as f:
                    f.write(source_code)
                print(f"[+] Contract saved: {contract_filename}")
        else:
            contract_filename = "contract.sol"
            contract_path = os.path.join(contracts_dir, contract_filename)
            with open(contract_path, "w") as f:
                f.write(source_code)
            print(f"[+] Contract saved: {contract_filename}")

        if not contract_filename:
            raise Exception("Could not determine main contract file")

        return analysis_dir, contracts_dir, contract_filename, dependencies

    except Exception as e:
        print(f"[!] Error getting source code: {e}")
        print(f"[!] URL: {url}")
        if 'response' in locals():
            print(f"[!] Response status: {response.status_code}")
            print(f"[!] Response content: {response.text[:200]}...")
    
    return "", "", "", set()

def main():
    install_dependencies()
    
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <contract-address>")
        exit(1)

    address = sys.argv[1]
    
    try:
        project_dir, contracts_dir, contract_filename, dependencies = get_source_code(address)
        if not project_dir:
            print("[!] Error: Could not get source code")
            exit(1)
            
        for dependency in dependencies:
            print(f"[+] Processing dependency: {dependency}")
            
        print(f"\n[+] Download completed successfully:")
        print(f"    - Project directory: {project_dir}")
        print(f"    - Main contract: {contract_filename}")
        print(f"    - Dependencies found: {len(dependencies)}")
        print(f"\nYou can continue with analysis using:")
        print(f"slither {project_dir}/contracts")
        
    except Exception as e:
        print(f"[!] Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
