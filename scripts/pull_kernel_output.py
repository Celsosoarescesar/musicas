import argparse
from pathlib import Path

from ace_step.kernels import pull_kernel_output


def main():
    parser = argparse.ArgumentParser(description="Baixa os arquivos de output de um kernel do Kaggle.")
    parser.add_argument("kernel_ref", help="Ref do kernel, ex: owner/kernel-slug")
    parser.add_argument("dest", help="Pasta de destino")
    args = parser.parse_args()

    dest_dir = pull_kernel_output(args.kernel_ref, Path(args.dest))
    print(f"Output salvo em: {dest_dir}")


if __name__ == "__main__":
    main()
