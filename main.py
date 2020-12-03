#!/usr/bin/python3
import time
from OpenSSL.SSL import (
    Connection,
    Error,
    WantReadError
)
from support.SocketSetup import SocketSetup
from support.argparsing import parser
from support.Verifier import Verifier
from support.HostNameClean import HostNameCleaner
from support.CertCheck import CertificateChecker
from support.CertChainLList import SinglyLinkedList


if __name__ == '__main__':

    CertificateChecker.openssl_version()
    args = parser.parse_args()
    with args.hostnames_file as file:
        sanitized_hosts = HostNameCleaner(file)
    hosts = sanitized_hosts.hostnames

    verifier = Verifier(ca_dir=args.certs_path, c_rehash_loc=args.rehash_path)
    assert (verifier.cert_hash_count > 0)

    for host in hosts:
        s = SocketSetup(host)
        s.connect_socket()

    SocketSetup.print_all_connections()

    for s in SocketSetup.open_sockets:
        s.sock.setblocking(True)
        tls_client = Connection(verifier.context, s.sock)
        tls_client.set_tlsext_host_name(bytes(s.host, 'utf-8'))     # Ensures ServerName when Verify callback invokes
        tls_client.set_connect_state()                              # set to work in client mode
        cert_chain = SinglyLinkedList(s.host)
        cert_chain.start_time = time.time()
        Verifier.certificate_chains.append(cert_chain)
        try:
            tls_client.do_handshake()
        except WantReadError:
            print("[!]WantReadError. Generated by non-blocking Socket")
        except Error as e:                                      # OpenSSL.SSL.Error
            print("[!]error with {0}\t{1}".format(s.host, e))
            pass                                                # pass: I already write the errors to a LinkedList
        except:
            print("[!]general exception")
        finally:
            cert_chain.tls_version = tls_client.get_cipher_name()
            cert_chain.cipher_version = tls_client.get_cipher_version()
            new_cert_chain = tls_client.get_peer_cert_chain()
            cert_chain.end_time = time.time()

    SocketSetup.clean_up()

    for chain in Verifier.certificate_chains:
        chain.print_chain_details()

#    Verifier.print_time_to_handshake()
