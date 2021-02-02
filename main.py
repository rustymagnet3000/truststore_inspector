#!/usr/bin/python3

import OpenSSL
from OpenSSL.SSL import Error, WantReadError
from OpenSSL.crypto import load_certificate, FILETYPE_PEM
from socket import gaierror, timeout
from support.YDCertFilesChecker import YDCertFilesChecker
from support.YDSocket import YDSocket
from support.YDTLSClient import YDTLSClient
from support.YDArgParse import parser
from support.YDVerifier import Verifier
from support.YDHostNameClean import HostNameCleaner
import os


if __name__ == "__main__":
    args = parser.parse_args()
    with Verifier(ca_dir=args.certs_path, c_rehash_loc=args.rehash_path) as verifier:
        if args.print_truststore_info:
            for filename in os.listdir(verifier.path_to_ca_certs):
                if filename.endswith('crt') or filename.endswith('.pem') or filename.endswith('.der'):
                    try:
                        with open(os.path.join(verifier.path_to_ca_certs, filename), "r") as f:
                            cert_buffer = f.read()
                            orig_cert = load_certificate(FILETYPE_PEM, cert_buffer)
                            checker = YDCertFilesChecker(orig_cert, filename)
                            checker.add_cert_to_summary_table()
                    except OpenSSL.crypto.Error:
                        print("Error happened in Load Certificate call:", filename)
            YDCertFilesChecker.print_cert_files_summary()

        if args.hostnames_file:
            with HostNameCleaner(args.hostnames_file) as hosts:
                for host in hosts:
                    try:
                        with YDSocket(host) as s:
                            YDSocket.table.add_row([host, 'connected', s.sock.getpeername()])
                            YDSocket.open_sockets += 1

                    except timeout:
                        YDSocket.table.add_row([host, 'fail', 'timeout'])
                        YDSocket.bad_sockets += 1
                    except gaierror as e:
                        YDSocket.table.add_row([host, 'fail', 'getaddrinfo error'])
                        YDSocket.bad_sockets += 1
                    except WantReadError:
                        print("[!]WantReadError. Generated by non-blocking Socket")
                    except Error as e:  # OpenSSL.SSL.Error
                        print("[!]error with {0}\t{1}".format(s.host, e))
                    except:
                        YDSocket.table.add_row([host, 'fail', 'Socket error. unhandled'])
                        YDSocket.bad_sockets += 1
            YDSocket.print_all_connections()

            for chain in Verifier.certificate_chains:
                chain.print_chain_details()
