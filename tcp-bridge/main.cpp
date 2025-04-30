#include <iostream>
#include <thread>
#include <unistd.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <cstring>
#include <sys/socket.h>

#define BUFFER_SIZE 4096

void relay(int src, int dst) {
    char buffer[BUFFER_SIZE];
    ssize_t n;
    while ((n = read(src, buffer, BUFFER_SIZE)) > 0) {
        if (write(dst, buffer, n) < 0) break;
    }
    shutdown(dst, SHUT_RDWR);
    shutdown(src, SHUT_RDWR);
}

int create_listener(const char* ip, int port) {
    int server_fd;
    sockaddr_in address{};
    socklen_t addrlen = sizeof(address);

    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd == -1) {
        perror("Socket creation failed");
        exit(EXIT_FAILURE);
    }

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    address.sin_family = AF_INET;
    address.sin_port = htons(port);
    inet_pton(AF_INET, ip, &address.sin_addr);

    if (bind(server_fd, (sockaddr*)&address, sizeof(address)) < 0) {
        perror("Bind failed");
        exit(EXIT_FAILURE);
    }

    listen(server_fd, 1);
    std::cout << "[*] Listening on " << ip << ":" << port << "...\n";

    int client_socket = accept(server_fd, (sockaddr*)&address, &addrlen);
    if (client_socket < 0) {
        perror("Accept failed");
        exit(EXIT_FAILURE);
    }

    std::cout << "[+] Connection accepted on port " << port << "\n";
    close(server_fd);
    return client_socket;
}

int main(int argc, char* argv[]) {
    if (argc != 5) {
        std::cerr << "Usage: " << argv[0] << " <destination_ip> <port_destination> <source_ip> <port_source>\n";
        return EXIT_FAILURE;
    }
    while(true){
    const char* ip = argv[1];
    int portB = std::stoi(argv[2]);
    int portA = std::stoi(argv[4]);

    std::cout << "=== TCP Bridge Server ===\n";

    std::cout << "[*] Waiting for Client B on port " << portB << "...\n";
    int socketB = create_listener(ip, portB);

    std::cout << "[*] Waiting for Client A on port " << portA << "...\n";
    int socketA = create_listener(ip, portA);

    std::cout << "[+] Both connections received. Bridging now...\n";

    std::thread t1(relay, socketA, socketB);
    std::thread t2(relay, socketB, socketA);

    t1.join();
    t2.join();

    std::cout << "[-] Bridge closed.\n";
    }
    return 0;
}
