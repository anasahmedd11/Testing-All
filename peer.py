from socket import *
import threading
import select
import maskpass


class PeerServer(threading.Thread):
    # Peer server initialization
    def __init__(self, username, peerServerPort):
        threading.Thread.__init__(self)
        self.username = username
        self.peerServerSocket = socket(AF_INET, SOCK_STREAM)
        self.peerServerHost = gethostbyname(gethostname())
        self.peerServerPort = peerServerPort
        self.peerServerSocket.bind((self.peerServerHost, self.peerServerPort))
        self.peerServerSocket.listen()
        self.inputs = [self.peerServerSocket]
        self.connectedPeers = []

    # main method of the peer server thread
    def run(self):
        while self.username != None:
            # monitors for the incoming connections
            readable, writable, exceptional = select.select(self.inputs + self.connectedPeers, [], [], 1)
            for sock in readable:
                # if the socket that is receiving the connection is the tcp socket of the peer's server, enters here
                if sock is self.peerServerSocket:
                    # accepts the connection, and adds its connection socket to the connected peers list
                    connectedPeerSocket, addr = sock.accept()
                    self.connectedPeers.append(connectedPeerSocket)

                # if the socket that receives the data is used to communicate with a connected peer, then enters here
                else:
                    message = None
                    try:
                        message = sock.recv(1024).decode().split("\n")
                    except:
                        pass
                    # print("DEBUG: " + ', '.join(message))
                    if message is None:
                        sock.close()
                        self.connectedPeers.remove(sock)
                    elif len(message) == 0:
                        sock.close()
                        self.connectedPeers.remove(sock)
                    elif message[0] == "chatroom-join":
                        print(message[1] + " joined the chatroom.")
                        sock.send("welcome".encode())
                    elif message[0] == "chatroom-leave":
                        print(message[1] + " left the chatroom.")
                        sock.close()
                        self.connectedPeers.remove(sock)
                    elif message[0] == "chat-message":
                        username = message[1]
                        content = "\n".join(message[2:])
                        print(username + " -> " + content)
                    elif message[0] == "welcome":
                        print("WELCOME!!")


class PeerClient(threading.Thread):
    def __init__(self, username, chatroom, peerServer, peersToConnect=None):
        threading.Thread.__init__(self)
        self.username = username
        self.chatroom = chatroom
        self.peerServer = peerServer
        if peersToConnect != None:
            for peer in peersToConnect:
                peer = peer.split(",")
                peerHost = peer[0]
                peerPort = int(peer[1])
                sock = socket(AF_INET, SOCK_STREAM)
                sock.connect((peerHost, peerPort))
                message = "chatroom-join\n{}".format(self.username)
                sock.send(message.encode())
                self.peerServer.connectedPeers.append(sock)

    # main method of the peer client thread
    def run(self):
        print('You have joined Chatroom. \nStart typing to send a message. Send ":quit" to leave the chatroom.')
        while self.chatroom != None:
            content = input()

            if content == ":quit":
                message = "chatroom-leave\n" + self.username
            else:
                message = "chat-message\n{}\n{}".format(self.username, content)

            for sock in self.peerServer.connectedPeers:
                sock.send(message.encode())

            if content == ":quit":
                self.chatroom = None
                for sock in self.peerServer.connectedPeers:
                    sock.close()


class peerMain:
    # peer initializations
    def __init__(self, username=None, peerServerPort=None):
        # registry host, port
        self.registryName = input("Enter IP address of registry: ")
        self.registryPort = 16600

        # connection initialization
        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        self.tcpClientSocket.connect((self.registryName, self.registryPort))
        self.udpClientSocket = socket(AF_INET, SOCK_DGRAM)
        self.registryUDPPort = 16500

        # peer info
        self.username = username
        self.peerServerPort = peerServerPort
        self.peerServer = None
        self.peerClient = None

        # timer for hello
        self.timer = None

        # run the main
        self.main()

    def main(self):
        # main loop for program
        while True:
            choice = "0"

            # in case that the user is not yet logged in
            if self.username == None:
                choice = input("\nOptions: \n\tCreate account: 1 \n\tLogin: 2 \nChoice: ")

                match choice:
                    # Account creation with entered username, password
                    case "1":
                        while True:
                            username = input("Username: ")
                            if len(username) < 6:
                                print("Username must be at least 6 characters long")
                            else:
                                break

                        while True:
                            password = maskpass.askpass("Password: ")
                            if len(password) < 10:
                                print("Password must be at least 10 characters long")
                            else:
                                break

                        # account creation
                        message = "JOIN {} {}".format(username, password)
                        self.tcpClientSocket.send(message.encode())
                        response = self.tcpClientSocket.recv(1024).decode()

                        match response:
                            case "join-success":
                                print("Account created successfully.")
                            case "join-exist":
                                print("Username already exists.")

                    # user is not logged in, log in with entered username, password
                    case "2":
                        username = input("Username: ")
                        password = maskpass.askpass("Password: ")
                        while True:
                            port = input("Port to receive messages: ")
                            if port.isdigit() == False:
                                print("Port number must be integer between 1024 and 65535")
                            else:
                                port = int(port)
                                if port < 1024 or port > 65535:
                                    print("Port number must be integer between 1024 and 65535")
                                else:
                                    break
                        message = "LOGIN {} {} {}".format(username, password, port)
                        self.tcpClientSocket.send(message.encode())
                        response = self.tcpClientSocket.recv(1024).decode()

                        match response:
                            case "login-account-not-exist":
                                print("No accounts exists with this username")
                            case "login-wrong-password":
                                print("Incorrect password")
                            case "login-online":
                                print("User is already online.")

                            case "login-success":
                                print("Successful Login!")
                                self.username = username
                                self.peerServerPort = port
                                self.peerServer = PeerServer(self.username, self.peerServerPort)
                                self.peerServer.start()
                                self.sendHelloMessage()

                    case _:
                        print("Something went wrong, please try again")

            # otherwise if user is already logged in
            else:
                choice = input(
                    "\nOptions: \n\tLogout: 1 \n\tSearch for User: 2 \n\tActive Users: 3"
                    + "\n\tJoin Chatroom: 4 \n\tShow Chatrooms: 5 \n\tCreate Chatroom: 6 \n\tChat with User: 7"
                    + "\nChoice: "
                )

                match choice:
                    # user logged out
                    case "1":
                        self.username = None
                        print("Logged out successfully")
                        if self.username != None:
                            message = "LOGOUT " + self.username
                        else:
                            message = "LOGOUT"
                        self.tcpClientSocket.send(message.encode())

                        if self.peerServer != None:
                            self.peerServer.username = None
                            self.peerServer.peerServerSocket.close()
                            for sock in self.peerServer.connectedPeers:
                                sock.close()
                            self.peerServer = None

                        if self.peerClient != None:
                            self.peerClient.chatroom = None
                            self.peerClient = None

                        if self.timer is not None:
                            self.timer.cancel()

                    # search for a user
                    case "2":
                        username = input("Username to be searched: ")
                        message = "SEARCH {}".format(username)
                        self.tcpClientSocket.send(message.encode())
                        response = self.tcpClientSocket.recv(1024).decode().split()

                        match response[0]:
                            case "search-success":
                                print("{} is logged in -> {} : ".format(username, response[1], response[2]))
                            case "search-user-not-online":
                                print("{} is not online.".format(username))
                            case "search-user-not-found":
                                print("{} was not found.".format(username))

                    # list of online users
                    case "3":
                        message = "USERS-LIST"
                        self.tcpClientSocket.send(message.encode())
                        response = self.tcpClientSocket.recv(1024).decode().split()

                        if response[0] == "users-list-success":
                            print("List of online users:")
                            for user in response[1:]:
                                print("\n\t" + user)

                    # join chatroom
                    case "4":
                        name = input("Chatroom name: ")
                        self.chatroomJoin(name)

                    # preview available chatrooms
                    case "5":
                        message = "CHATROOM-LIST"
                        self.tcpClientSocket.send(message.encode())
                        response = self.tcpClientSocket.recv(1024).decode().split("\n")

                        if response[0] == "chatroom-list-success":
                            print("Currently available chat rooms:")
                            for chatroom in response[1:]:
                                print("\n\t" + chatroom + " users connected")

                    # chatroom created
                    case "6":
                        while True:
                            name = input("Chatroom name: ")
                            if len(name) < 5:
                                print("Chatroom name must be at least 5 characters long")
                            else:
                                message = "CHATROOM-CREATE\n{}".format(name)
                                self.tcpClientSocket.send(message.encode())
                                response = self.tcpClientSocket.recv(1024).decode()

                                match response:
                                    case "chatroom-exists":
                                        print("There already exists a chatroom with such name.")
                                    case "chatroom-creation-success":
                                        print("Chatroom created successfully")
                                        self.chatroomJoin(name)
                            break
                    case "7":
                        username = input("username: ")
                        message = "PRIVATE-CHATROOM\n{}".format(username)
                        self.tcpClientSocket.send(message.encode())
                        response = self.tcpClientSocket.recv(1024).decode()

                        splitResponse = response.split()
                        match splitResponse[0]:
                            case "user does not exist":
                                print("user does not exist")
                                break
                        
                        self.chatroomJoin(splitResponse[1])

                    case _:
                        print("Something went wrong, please try again")

    def chatroomJoin(self, name):
        print(name)
        message = "CHATROOM-JOIN {}".format(name)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode().split("\n")

        match response[0]:
            case "chatroom-not-found":
                print("No chatroom exists with such name.")
            case "chatroom-join-success":
                if len(response) == 1:
                    self.peerClient = PeerClient(self.username, name, self.peerServer)
                else:
                    self.peerClient = PeerClient(self.username, name, self.peerServer, response[1:])
                self.peerClient.start()
                self.peerClient.join()

                # This section will only run after user quits the chatroom
                self.tcpClientSocket.send("chatroom-leave-request".encode())

    def sendHelloMessage(self):
        message = "HELLO {}".format(self.username)
        self.udpClientSocket.sendto(message.encode(), (self.registryName, self.registryUDPPort))
        self.timer = threading.Timer(1, self.sendHelloMessage)
        self.timer.start()


peerMain()
