import socket

HOST, PORT = 'localhost', 9999
BYTELENGTH = 1024

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

while True:
    conn, addr = server.accept()
    cmnd = conn.recv(BYTELENGTH)
    cmd = cmnd.decode("utf-8").strip()
    print(cmnd)

    if 'INIT' in str(cmnd):
        # Do the initialization action
        conn.sendall(b'INIT-DONE\n')

    elif 'PLAY' in str(cmnd):
        # Do the play action
        conn.sendall(b'PLAY-DONE\n')

    elif 'QUIT' in str(cmnd):
        # Do the quitting action
        conn.sendall(b'QUIT-DONE\n')
        break

server.close()
