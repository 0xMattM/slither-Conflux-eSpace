import os
import sys
import subprocess
from pathlib import Path

def run_analysis():
    try:
        if len(sys.argv) != 2:
            print(f"Usage: {sys.argv[0]} <contract-address>")
            return False

        contract_address = sys.argv[1]
        current_dir = Path(__file__).parent.absolute()
        print("[+] Starting analysis process...")
        
        print("[+] Step 1: Downloading source code and managing dependencies...")
        downloader_script = current_dir / "source_downloader.py"
        result = subprocess.run([sys.executable, str(downloader_script), contract_address], 
                              capture_output=True, 
                              text=True)
        
        if result.returncode != 0:
            print("[!] Error in source_downloader.py:")
            print(result.stderr)
            return False
            
        print("[+] Download and setup completed successfully")
        
        project_dir = Path.cwd() / f"{contract_address}_analysis"
        
        print("[+] Step 2: Running security analysis...")
        analyzer_script = current_dir / "security_analyzer.py"
        result = subprocess.run([sys.executable, str(analyzer_script), str(project_dir)], 
                              capture_output=True, 
                              text=True)
        
        if result.returncode != 0:
            print("[!] Error in security_analyzer.py:")
            print(result.stderr)
            return False
            
        print("[+] Security analysis completed successfully")
        print("[+] Analysis process finished successfully")
        print(f"[+] Report location: {project_dir / 'analysis_summary.md'}")
        return True
        
    except Exception as e:
        print(f"[!] Error during execution: {str(e)}")
        return False

def main():
    success = run_analysis()
    sys.exit(0 if success else 1)

if __name__ == "_main_":
    main()
