import socket
import select

# Set up server socket
s_sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
        )
s_sock.bind( ('localhost', 45678) )
s_sock.listen()
s_sock.setblocking(False)

# set up poller and register server
# socket with this poller
poller = select.poll()
poller.register(s_sock, select.POLLIN)

# This dictionary maps file descriptors to
# client sockets
fd_sock = {}

# Start poller mainloop
while True:
    # Poll for events
    events = poller.poll(1000000)

    # Now process the events
    for fd, flag in events:
        # New connection on s_sock, accept it.
        if fd == s_sock.fileno():
            c_sock, addr = s_sock.accept()
            c_sock.setblocking(False)
            fd_sock[c_sock.fileno()] = c_sock
            poller.register(
                    c_sock.fileno(),
                    select.POLLIN | select.POLLPRI
                    )
            print(f"New connection from {addr}")
        # If we get here, the traffic is on a client socket.
        elif fd in fd_sock:
            # Data ready for input.
            if flag & select.POLLIN:
                try:
                    data = fd_sock[fd].recv(1024)
                    if data:
                        print(
                                f"Data received: fd: {fd} data: {data.decode()}",
                                end=''
                                )
                        poller.modify(fd, select.POLLOUT)
                    else:
                        ## Connection has closed, unregister
                        ## and close the socket.
                        poller.unregister(fd_sock[fd])
                        fd_sock[fd].close()
                        del fd_sock[fd]
                        print("Closed connection: {fd}")
                except BlockingIOError as e:
                    print(f"{e}: {fd}: data not available yet.")
            ## Client disconnected.
            elif flag & select.POLLHUP:
                poller.unregister(fd_sock[fd])
                fd_sock[fd].close()
                del fd_sock[fd]
                print(f"Closed connection: {fd}")
            ## Data ready for output
            elif flag & select.POLLOUT:
                try:
                    fd_sock[fd].send(b"Got the data\n")
                except BlockingIOError as e:
                    print(f"{e}: {fd}: tried to send data.")
                else:
                    poller.modify(fd, select.POLLIN)
            ## Socket error
            elif flag & select.POLLERR:
                poller.unregister(fd_sock[fd])
                fd_sock[fd].close()
                del fd_sock[fd]
                print(f"Socket error: {fd}")

