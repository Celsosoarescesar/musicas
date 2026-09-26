import argparse

from ace_step.kernels import get_kernel_status


def main():
    parser = argparse.ArgumentParser(description="Consulta o status de um kernel no Kaggle.")
    parser.add_argument("kernel_ref", help="Ref do kernel, ex: owner/kernel-slug")
    args = parser.parse_args()

    result = get_kernel_status(args.kernel_ref)
    print(f"Status: {result['status']}")
    if result["failure_message"]:
        print(f"Mensagem de falha: {result['failure_message']}")


if __name__ == "__main__":
    main()
