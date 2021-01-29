"""This section is responsible for decryption the encrypted data"""
def decrypt(path):
    """Decryption for encrypted Riot api and bot Token"""
    with open(path, 'r') as file:
        data = file.readline()

    message = data
    key = 47
    decrypt_text = ''

    for i in range(len(message)):
        temp = ord(message[i]) - key
        if ord(message[i]) == 32:
            decrypt_text += " "
        elif temp < 32:
            temp += 94
            decrypt_text += chr(temp)
        else:
            decrypt_text += chr(temp)

    return decrypt_text