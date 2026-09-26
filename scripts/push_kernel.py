import argparse
from pathlib import Path

from ace_step.kernels import push_kernel


def main():
    parser = argparse.ArgumentParser(
        description="Envia um kernel (pasta com kernel-metadata.json) para o Kaggle."
    )
    parser.add_argument("folder", help="Caminho da pasta do kernel")
    args = parser.parse_args()

    ref = push_kernel(Path(args.folder))
    print(f"Kernel enviado: {ref}")


if __name__ == "__main__":
    main()
