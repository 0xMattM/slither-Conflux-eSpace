import os
import json
import subprocess
import sys
import re
from importlib.metadata import distributions
from typing import Optional, Set
from collections import defaultdict

def install_dependencies():
    required_packages = {
        'slither-analyzer': 'slither',
        'solc-select': 'solc-select'
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

def detect_solidity_version(file_path: str) -> Optional[str]:
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        pragma_match = re.search(r'pragma\s+solidity\s+([^;]+);', content)
        if pragma_match:
            version = pragma_match.group(1).strip()
            
            if version.startswith('^'):
                base_version = version[1:]
                try:
                    major, minor, patch = map(int, base_version.split('.'))
                    available_versions = ["0.8.19", "0.8.17", "0.8.16", "0.8.15", "0.8.14", "0.8.13", 
                                       "0.8.12", "0.8.11", "0.8.10", "0.8.9", "0.8.8", "0.8.7", 
                                       "0.8.6", "0.8.5", "0.8.4", "0.8.3", "0.8.2", "0.8.1", "0.8.0",
                                       "0.7.6", "0.7.5", "0.7.4", "0.7.3", "0.7.2", "0.7.1", "0.7.0",
                                       "0.6.12", "0.6.11", "0.6.10", "0.6.9", "0.6.8", "0.6.7", "0.6.6"]
                    
                    compatible_versions = []
                    for v in available_versions:
                        v_major, v_minor, v_patch = map(int, v.split('.'))
                        if v_major == major and v_minor == minor and v_patch >= patch:
                            compatible_versions.append(v)
                    
                    if compatible_versions:
                        return max(compatible_versions)
                    else:
                        for v in available_versions:
                            v_major, v_minor, v_patch = map(int, v.split('.'))
                            if v_major == major:
                                compatible_versions.append(v)
                        if compatible_versions:
                            return max(compatible_versions)
                except ValueError:
                    pass
                return base_version
            elif '>=' in version and '<' in version:
                min_version = version.split('>=')[1].split('<')[0].strip()
                max_version = version.split('<')[1].strip()
                
                try:
                    min_major, min_minor, min_patch = map(int, min_version.split('.'))
                    max_major, max_minor, max_patch = map(int, max_version.split('.'))
                    
                    compatible_versions = []
                    for v in available_versions:
                        v_major, v_minor, v_patch = map(int, v.split('.'))
                        if (v_major >= min_major and v_major <= max_major and
                            v_minor >= min_minor and v_minor <= max_minor and
                            v_patch >= min_patch and v_patch <= max_patch):
                            compatible_versions.append(v)
                    
                    if compatible_versions:
                        return max(compatible_versions)
                except ValueError:
                    pass
            elif '>=' in version:
                version = version.split('>=')[1].strip()
            elif '<' in version:
                version = version.split('<')[1].strip()
            
            if re.match(r'^\d+\.\d+\.\d+$', version):
                return version
            
    except Exception as e:
        print(f"[!] Error detecting Solidity version: {e}")
    
    return "0.8.19"

def setup_solc(version: str) -> bool:
    try:
        try:
            subprocess.run(['solc-select', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[+] Installing solc-select...")
            subprocess.run(['pip', 'install', 'solc-select'], check=True)
            print("[+] solc-select installed successfully")
        
        result = subprocess.run(['solc-select', 'versions'], capture_output=True, text=True)
        installed_versions = [v.strip() for v in result.stdout.split('\n') if v.strip()]
        
        if version not in installed_versions:
            print(f"[+] Installing solc version {version}...")
            try:
                subprocess.run(['solc-select', 'install', version], check=True)
                print(f"[+] solc {version} installed successfully")
            except subprocess.CalledProcessError:
                print(f"[!] Could not install version {version}")
                return False
        
        subprocess.run(['solc-select', 'use', version], check=True)
        print(f"[+] Using solc version {version}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[!] Error setting up solc: {e}")
        return False

def run_slither_analysis(project_dir: str) -> Optional[str]:
    try:
        contracts_dir = os.path.join(project_dir, "contracts")
        json_output = os.path.join(project_dir, "slither_report.json")
        
        cmd = [
            "slither",
            contracts_dir,
            "--json", json_output
        ]
        
        print(f"[+] Running Slither analysis: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if os.path.exists(json_output):
            print(f"[+] Analysis completed. Report saved to: {json_output}")
            return json_output
        else:
            print(f"[!] Analysis error. Slither output:")
            print(result.stdout)
            print(result.stderr)
            
    except Exception as e:
        print(f"[!] Error running Slither: {e}")
        if 'result' in locals():
            print(f"Slither output:")
            print(result.stdout)
            print(result.stderr)
    
    return None

def generate_summary(json_file: str, summary_file: str) -> None:
    try:
        with open(json_file, 'r') as f:
            report = json.load(f)
        
        with open(summary_file, 'w') as f:
            f.write("# Smart Contract Security Analysis Report\n\n")
            
            findings_by_check = defaultdict(list)
            for detector in report.get('results', {}).get('detectors', []):
                check = detector.get('check', '')
                findings_by_check[check].append(detector)
            
            for check, findings in findings_by_check.items():
                if check:
                    f.write(f"## {check}\n\n")
                
                for finding in findings:
                    if 'description' in finding:
                        f.write(f"{finding['description']}\n\n")
                    
                    for element in finding.get('elements', []):
                        source_mapping = element.get('source_mapping', {})
                        if 'lines' in source_mapping:
                            lines = source_mapping['lines']
                            filename = source_mapping.get('filename', '')
                            if filename and lines:
                                f.write(f"- {filename}#{','.join(map(str, lines)) if isinstance(lines, list) else lines}\n")
                    
                    if 'check' in finding:
                        f.write(f"\nReference: https://github.com/crytic/slither/wiki/Detector-Documentation#{finding['check']}\n")
                    
                    f.write("\n---\n\n")
            
            f.write("## Analysis Statistics\n\n")
            impact_count = defaultdict(int)
            for detector in report.get('results', {}).get('detectors', []):
                impact = detector.get('impact', '')
                if impact:
                    impact_count[impact] += 1
            
            for impact in ['High', 'Medium', 'Low', 'Informational']:
                if impact in impact_count:
                    count = impact_count[impact]
                    f.write(f"- {impact}: {count} finding{'s' if count > 1 else ''}\n")
            
    except Exception as e:
        print(f"[!] Error generating summary: {e}")

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <project-dir>")
        exit(1)

    project_dir = sys.argv[1]
    
    try:
        if not os.path.exists(project_dir):
            raise Exception(f"Directory {project_dir} does not exist")
            
        install_dependencies()
            
        contracts_dir = os.path.join(project_dir, "contracts")
        contract_files = [f for f in os.listdir(contracts_dir) if f.endswith('.sol')]
        
        if not contract_files:
            raise Exception("No .sol files found in directory")
            
        contract_file = os.path.join(contracts_dir, contract_files[0])
        
        solc_version = detect_solidity_version(contract_file)
        if not solc_version or not setup_solc(solc_version):
            print("[!] Could not setup Solidity version")
            exit(1)
        
        json_output = run_slither_analysis(project_dir)
        if json_output:
            summary_file = os.path.join(project_dir, "analysis_summary.md")
            generate_summary(json_output, summary_file)
            print(f"[+] Analysis completed. Summary saved to: {summary_file}")
            
    except Exception as e:
        print(f"[!] Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()