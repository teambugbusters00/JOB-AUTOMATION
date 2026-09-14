from getpass import getpass
from web.security import hash_password

password = getpass("Admin password (8+ characters): ")
print("ADMIN_PASSWORD_HASH=" + hash_password(password))
