import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
from socket import socket, AF_INET, SOCK_STREAM, error
import threading
import time
import timeit
from peer import PeerServer, PeerClient, peerMain

class TestPeerServer(unittest.TestCase):
    def setUp(self):
        self.server = PeerServer("TestUser", 12345)
        self.server.peerServerSocket = MagicMock(spec=socket)
        self.server.connectedPeers = []

    def test_handle_incoming_connections(self):
        with patch("select.select") as mock_select:
            mock_select.return_value = ([self.server.peerServerSocket], [], [])
            self.server.run()

            self.assertTrue(self.server.peerServerSocket.accept.called)
            self.assertEqual(len(self.server.connectedPeers), 1)

    def test_handle_invalid_message_format(self):
        mock_peer_socket = MagicMock(spec=socket)
        mock_peer_socket.recv.return_value = "invalid-format".encode()

        self.server.connectedPeers.append(mock_peer_socket)

        with patch("select.select") as mock_select:
            mock_select.return_value = ([mock_peer_socket], [], [])
            with patch("builtins.print") as mock_print:
                self.server.run()

                mock_peer_socket.close.assert_called_once()
                mock_print.assert_called_once_with("DEBUG: invalid-format")

    def test_handle_incoming_messages(self):
        mock_peer_socket = MagicMock(spec=socket)
        mock_peer_socket.recv.return_value = "chat-message\nTestUser\nHello".encode()

        self.server.connectedPeers.append(mock_peer_socket)

        with patch("select.select") as mock_select:
            mock_select.return_value = ([mock_peer_socket], [], [])
            self.server.run()

            mock_peer_socket.recv.assert_called_once_with(1024)
            self.assertEqual(mock_peer_socket.send.call_count, 0)

    def test_handle_chatroom_join(self):
        mock_peer_socket = MagicMock(spec=socket)
        mock_peer_socket.recv.return_value = "chatroom-join\nNewUser".encode()

        self.server.connectedPeers.append(mock_peer_socket)

        with patch("select.select") as mock_select:
            mock_select.return_value = ([mock_peer_socket], [], [])
            self.server.run()

            mock_peer_socket.recv.assert_called_once_with(1024)
            mock_peer_socket.send.assert_called_once_with("welcome".encode())

    def test_handle_chatroom_leave(self):
        mock_peer_socket = MagicMock(spec=socket)
        mock_peer_socket.recv.return_value = "chatroom-leave\nLeavingUser".encode()

        self.server.connectedPeers.append(mock_peer_socket)

        with patch("select.select") as mock_select:
            mock_select.return_value = ([mock_peer_socket], [], [])
            self.server.run()

            mock_peer_socket.recv.assert_called_once_with(1024)
            self.assertEqual(len(self.server.connectedPeers), 0)

    def test_handle_chat_message(self):
        mock_peer_socket = MagicMock(spec=socket)
        mock_peer_socket.recv.return_value = "chat-message\nTestUser\nHello".encode()

        self.server.connectedPeers.append(mock_peer_socket)

        with patch("select.select") as mock_select:
            mock_select.return_value = ([mock_peer_socket], [], [])
            with patch("builtins.print") as mock_print:
                self.server.run()

                mock_peer_socket.recv.assert_called_once_with(1024)
                mock_print.assert_called_once_with("TestUser -> Hello")

    def test_handle_empty_message(self):
        mock_peer_socket = MagicMock(spec=socket)
        mock_peer_socket.recv.return_value = "".encode()

        self.server.connectedPeers.append(mock_peer_socket)

        with patch("select.select") as mock_select:
            mock_select.return_value = ([mock_peer_socket], [], [])
            self.server.run()

            mock_peer_socket.close.assert_called_once()
            self.assertEqual(len(self.server.connectedPeers), 0)

    def test_handle_welcome_message(self):
        mock_peer_socket = MagicMock(spec=socket)
        mock_peer_socket.recv.return_value = "welcome".encode()

        self.server.connectedPeers.append(mock_peer_socket)

        with patch("select.select") as mock_select:
            mock_select.return_value = ([mock_peer_socket], [], [])
            with patch("builtins.print") as mock_print:
                self.server.run()

                mock_print.assert_called_once_with("WELCOME!!")

    for test_function in [
        test_handle_welcome_message,
        test_handle_empty_message,
        test_handle_chat_message,
        test_handle_chatroom_leave,
        test_handle_chatroom_join,
        test_handle_incoming_messages,
        test_handle_invalid_message_format,
        test_handle_incoming_connections
    ]:
        execution_time = timeit.timeit(test_function, number=1)
        print(f"Execution time for {test_function.__name__}: {execution_time} seconds")


class TestPeerClient(unittest.TestCase):
    def setUp(self):
        self.client = PeerClient("TestUser", "TestChatroom", MagicMock(spec=PeerServer))

    def test_send_chat_message(self):
        with patch("builtins.input", return_value="Hello"):
            with patch("socket.socket.connect") as mock_connect:
                with patch("socket.socket.send") as mock_send:
                    self.client.run()

                    mock_send.assert_called_once_with("chat-message\nTestUser\nHello".encode())

    def test_send_quit_message(self):
        with patch("builtins.input", return_value=":quit"):
            with patch("socket.socket.connect") as mock_connect:
                with patch("socket.socket.send") as mock_send:
                    self.client.run()
                    mock_send.assert_called_once_with("chatroom-leave\nTestUser".encode())

    def test_run_quit_message(self):
        with patch("builtins.input", return_value=":quit"):
            with patch("socket.socket.connect") as mock_connect:
                with patch("socket.socket.send") as mock_send:
                    self.client.run()
                    mock_send.assert_called_once_with("chatroom-leave\nTestUser".encode())

    def test_run_private_chatroom(self):
        with patch("builtins.input", side_effect=["7", "AnotherUser"]):
            with patch("socket.socket.connect") as mock_connect:
                with patch("socket.socket.send") as mock_send:
                    self.client.run()
                    mock_send.assert_called_once_with("PRIVATE-CHATROOM\nAnotherUser".encode())

    def test_run_private_chatroom_user_not_exist(self):
        with patch("builtins.input", side_effect=["7", "NonexistentUser"]):
            with patch("socket.socket.connect") as mock_connect:
                with patch("socket.socket.send") as mock_send:
                    with patch("socket.socket.recv") as mock_recv:
                        mock_recv.return_value = "user does not exist".encode()
                        with patch("builtins.print") as mock_print:
                            self.client.run()
                            mock_send.assert_called_once_with("PRIVATE-CHATROOM\nNonexistentUser".encode())
                            mock_print.assert_called_once_with("user does not exist")

    for test_function in [
        test_run_private_chatroom_user_not_exist,
        test_run_private_chatroom,
        test_run_quit_message,
        test_send_quit_message,
        test_send_chat_message

    ]:
        execution_time = timeit.timeit(test_function, number=1)
        print(f"Execution time for {test_function.__name__}: {execution_time} seconds")

class TestPeerMain(unittest.TestCase):
    def setUp(self):
        self.main = peerMain()

    def test_account_creation(self):
        with patch("builtins.input", side_effect=["1", "TestUser", "TestPassword"]):
            with patch("socket.socket.send") as mock_send:
                self.main.main()
                mock_send.assert_called_once_with("JOIN TestUser TestPassword".encode())

    def test_login_success(self):
        with patch("builtins.input", side_effect=["2", "TestUser", "TestPassword", "12345"]):
            with patch("socket.socket.send") as mock_send:
                with patch("socket.socket.recv") as mock_recv:
                    mock_recv.return_value = "login-success".encode()
                    self.main.main()
                    mock_send.assert_called_once_with("LOGIN TestUser TestPassword 12345".encode())

    def test_search_user_not_found(self):
        with patch("builtins.input", side_effect=["2", "NonexistentUser"]):
            with patch("socket.socket.send") as mock_send:
                with patch("socket.socket.recv") as mock_recv:
                    mock_recv.return_value = "search-user-not-found".encode()
                    with patch("builtins.print") as mock_print:
                        self.main.main()
                        mock_send.assert_called_once_with("SEARCH NonexistentUser".encode())
                        mock_print.assert_called_once_with("NonexistentUser was not found.")

    def test_chatroom_join_not_found(self):
        with patch("builtins.input", side_effect=["4", "NonexistentChatroom"]):
            with patch("socket.socket.send") as mock_send:
                with patch("socket.socket.recv") as mock_recv:
                    mock_recv.return_value = "chatroom-not-found".encode()
                    with patch("builtins.print") as mock_print:
                        self.main.main()
                        mock_send.assert_called_once_with("CHATROOM-JOIN NonexistentChatroom".encode())
                        mock_print.assert_called_once_with("No chatroom exists with such name.")

    def test_chatroom_create_success(self):
        with patch("builtins.input", side_effect=["6", "NewChatroom"]):
            with patch("socket.socket.send") as mock_send:
                with patch("socket.socket.recv") as mock_recv:
                    mock_recv.return_value = "chatroom-creation-success".encode()
                    with patch("builtins.print") as mock_print:
                        self.main.main()
                        mock_send.assert_called_once_with("CHATROOM-CREATE\nNewChatroom".encode())
                        mock_print.assert_called_once_with("Chatroom created successfully")

    def test_account_creation_existing_username(self):
        with patch("builtins.input", side_effect=["1", "TestUser", "TestPassword"]):
            with patch("socket.socket.send") as mock_send:
                with patch("socket.socket.recv") as mock_recv:
                    mock_recv.return_value = "join-exist".encode()
                    with patch("builtins.print") as mock_print:
                        self.main.main()
                        mock_send.assert_called_once_with("JOIN TestUser TestPassword".encode())
                        mock_print.assert_called_once_with("Username already exists.")

    for test_function in [
        test_chatroom_join_not_found,
        test_account_creation_existing_username,
        test_chatroom_create_success,
        test_chatroom_join_not_found,
        test_search_user_not_found,
        test_login_success,
        test_account_creation,

    ]:
        execution_time = timeit.timeit(test_function, number=1)
        print(f"Execution time for {test_function.__name__}: {execution_time} seconds")

if __name__ == '__main__':
    unittest.main()
