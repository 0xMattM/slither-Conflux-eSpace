#!/usr/bin/env python3

import sys
import os
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Conflux Slither - Analiza contratos en Conflux eSpace",
        usage="conflux-slither <ContractAddress>"
    )
    
    parser.add_argument(
        "address",
        help="Dirección del contrato a analizar",
        type=str
    )
    
    args = parser.parse_args()
    
    # Obtener la ruta al script analize_confluxscan.py
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "slither", "tools", "analize_confluxscan.py")
    
    # Ejecutar el script con la dirección del contrato
    print(f"Analizando contrato Conflux eSpace en {args.address}")
    os.system(f"python {script_path} {args.address}")

if __name__ == "__main__":
    main()