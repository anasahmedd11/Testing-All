import unittest
from pymongo import MongoClient
from db import DB

class TestDB(unittest.TestCase):
    def setUp(self):
        self.client = MongoClient("mongodb://localhost:27017/")
        self.test_db = self.client["test_p2p_chat"]
        self.db = DB()

    def test_is_account_exist(self):
        self.db.register("test_user", "test_password")
        self.assertTrue(self.db.is_account_exist("test_user"))
        self.assertFalse(self.db.is_account_exist("nonexistent_user"))

    def test_register(self):
        self.db.register("test_user", "test_password")
        self.assertTrue(self.db.is_account_exist("test_user"))

    def test_get_password(self):
        # Test retrieving password
        self.db.register("test_user", "test_password")
        self.assertEqual(self.db.get_password("test_user"), "test_password")

    def test_is_account_online(self):
        # Test account online status
        self.db.user_login("test_user", "127.0.0.1", 12345)
        self.assertTrue(self.db.is_account_online("test_user"))
        self.assertFalse(self.db.is_account_online("nonexistent_user"))

    def test_user_login(self):
        # Test user login
        self.db.user_login("test_user", "127.0.0.1", 12345)
        self.assertTrue(self.db.is_account_online("test_user"))

    def test_user_logout(self):
        # Test user logout
        self.db.user_login("test_user", "127.0.0.1", 12345)
        self.db.user_logout("test_user")
        self.assertFalse(self.db.is_account_online("test_user"))

    def test_get_peer_ip_port(self):
        # Test retrieving peer IP and port
        self.db.user_login("test_user", "127.0.0.1", 12345)
        ip, port = self.db.get_peer_ip_port("test_user")
        self.assertEqual(ip, "127.0.0.1")
        self.assertEqual(port, 12345)

    def test_multiple_users(self):
        # Test multiple user accounts
        self.db.register("user1", "pass1")
        self.db.register("user2", "pass2")

        self.assertTrue(self.db.is_account_exist("user1"))
        self.assertTrue(self.db.is_account_exist("user2"))
        self.assertFalse(self.db.is_account_exist("user3"))

        self.assertEqual(self.db.get_password("user1"), "pass1")
        self.assertEqual(self.db.get_password("user2"), "pass2")

    def test_login_wrong_password(self):
        # Test login with wrong password
        self.db.register("test_user", "test_password")
        status = self.db.user_login("test_user", "127.0.0.1", 12345)
        self.assertEqual(status, "login-wrong-password")

    def test_logout_nonexistent_user(self):
        # Test logout for nonexistent user
        self.db.user_login("test_user", "127.0.0.1", 12345)
        self.db.user_logout("nonexistent_user")  # Should not raise an

    def tearDown(self):
        self.client.drop_database("test_p2p_chat")

if __name__ == '__main__':
    unittest.main()
