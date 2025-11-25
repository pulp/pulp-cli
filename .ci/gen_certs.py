import argparse
import os
import sys

import trustme


def main() -> None:

    parser = argparse.ArgumentParser(prog="gen_certs")
    parser.add_argument(
        "-d",
        "--dir",
        default=os.getcwd(),
        help="Directory where certificates and keys are written to. Defaults to cwd.",
    )

    args = parser.parse_args(sys.argv[1:])
    cert_dir = args.dir

    if not os.path.isdir(cert_dir):
        raise ValueError(f"--dir={cert_dir} is not a directory")

    key_type = trustme.KeyType["ECDSA"]

    # Generate the CA certificate
    ca = trustme.CA(key_type=key_type)
    # Write the certificate the client should trust
    ca_cert_path = os.path.join(cert_dir, "ca.pem")
    ca.cert_pem.write_to_path(path=ca_cert_path)

    # Generate the server certificate
    server_cert = ca.issue_cert("localhost", "127.0.0.1", "::1", key_type=key_type)
    # Write the certificate and private key the server should use
    server_key_path = os.path.join(cert_dir, "server.key")
    server_cert_path = os.path.join(cert_dir, "server.pem")
    server_cert.private_key_pem.write_to_path(path=server_key_path)
    with open(server_cert_path, mode="w") as f:
        f.truncate()
    for blob in server_cert.cert_chain_pems:
        blob.write_to_path(path=server_cert_path, append=True)

    # Generate the client certificate
    client_cert = ca.issue_cert("admin@example.com", common_name="admin", key_type=key_type)
    # Write the certificate and private key the client should use
    client_key_path = os.path.join(cert_dir, "client.key")
    client_cert_path = os.path.join(cert_dir, "client.pem")
    client_cert.private_key_pem.write_to_path(path=client_key_path)
    with open(client_cert_path, mode="w") as f:
        f.truncate()
    for blob in client_cert.cert_chain_pems:
        blob.write_to_path(path=client_cert_path, append=True)


if __name__ == "__main__":
    main()
