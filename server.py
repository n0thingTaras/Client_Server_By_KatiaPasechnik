import asyncio
from datetime import datetime
import os
import re
import signal
import time

signal.signal(signal.SIGINT, signal.SIG_DFL)


class Client:
    def __init__(self, name):
        self.name = name
        self.current_folder = os.path.join(os.getcwd(), self.name)
        self.r_file = ""
        self.char_counter = 0
        os.makedirs(self.current_folder, exist_ok=True)

    def make_dir(self, name):
        if len(name) < 0:
            return "Name is empty"
        try:
            os.makedirs(os.path.join(self.current_folder, name))
            self.current_folder = os.path.join(self.current_folder, name)
        except FileExistsError:
            return "File already exists"
        return "Folder created successful"

    def list(self):
        message = "List of " + self.current_folder + "\n\n"
        message += "name\tsize\tcreate date\n"
        for file in os.listdir(self.current_folder):
            path = os.path.join(self.current_folder, file)
            date_time = datetime.fromtimestamp(os.stat(path).st_ctime)
            message += "{}\t{}\t{}\n".format(file, os.stat(path).st_size, date_time.strftime("%m/%d/%Y, %H:%M:%S"))
        return message

    def write_file(self, name, input):
        ##todo проверить есть ли файл
        if len(input) > 0:
            with open(os.path.join(self.current_folder, name.decode()), "a") as file:
                file.write(input.decode())
        else:
            with open(os.path.join(self.current_folder, name.decode(), ), "w") as file:
                if len(input) > 0:
                    file.write(input.decode())
        return "Operation 'write_file' is completed"

    def read_file(self, name=b""):
        file_name = name.decode()
        if len(file_name) == 0:
            file_name = os.path.basename(self.r_file)
            if file_name == "":
                return "File {} doesn't opened. You need open file for the first"
            self.r_file = ""
            self.char_counter = 0
            return "File {} is closed".format(file_name)
        file_path = os.path.join(self.current_folder, name.decode())
        if self.r_file != file_path:
            self.r_file = file_path
            self.char_counter = 0
        if os.path.isfile(file_path):
            with open(file_path, "r") as f:
                data = f.read()
                self.char_counter += 100
                data = data[self.char_counter - 100:self.char_counter]
                if len(data) > 0:
                    basename = os.path.basename(self.r_file)
                    return "Data from {}:\n\n{}".format(basename, data)
                else:
                    self.char_counter = 0
                    return "End of file"
        else:
            return "File {} doesn't exists".format(name.decode())

    def change_folder(self, name):
        if name.decode() == "..":
            if self.current_folder == os.path.join(os.getcwd(), self.name):
                return "Out of current working directory"
            dirname, _ = os.path.split(self.current_folder)
            self.current_folder = dirname
        else:
            path = os.path.join(self.current_folder, name.decode())
            if os.path.exists(path) and os.path.isdir(path):
                self.current_folder = path
            else:
                return "{} does not point to a folder in the current working directory".format(name.decode())
        return "Operation 'change_folder' is completed"


# todo Надо сделать чтобы клиент вводил команды

async def register(reader, writer):
    writer.write("Input username! ".encode())
    data = await reader.read(1000)
    username = data.decode()
    writer.write("Input password! ".encode())
    data = await reader.read(1000)
    password = data.decode()
    user_check = False
    with open("UserList.txt", "r") as file:
        for line in file:
            if username in line.split(":"):
                user_check = True
                break
    if user_check:
        writer.write("User already exists!".encode())
    else:
        with open("UserList.txt", "a") as file:
            file.write("{username}:{password}\n".format(username=username, password=password))
        Client(username)
        writer.write("User has been created!".encode())


async def replace(source_file_path, pattern, substring):
    file_handle = open(source_file_path, 'r')
    file_string = file_handle.read()
    file_handle.close()
    file_string = (re.sub(pattern, substring, file_string))
    file_handle = open(source_file_path, 'w')
    file_handle.write(file_string)
    file_handle.close()


async def login(reader, writer):
    writer.write("Input username: ".encode())
    data = await reader.read(1000)
    username = data.decode()
    writer.write("Input password".encode())
    data = await reader.read(1000)
    password = data.decode()
    user_check = False
    with open("UserList.txt", "r") as file:
        for line in file:
            user_info = line.strip().split(":")
            if username in user_info and password in user_info:
                if "Online" not in user_info:
                    user_check = True
                    break
                else:
                    user_check = "Online"
    if user_check == "Online":
        return False, username, password, "User already online"
    if user_check:
        await replace("UserList.txt", f'{username}:{password}\n', f'{username}:{password}:Online\n')
        return True, username, password, ""
    else:
        print("ERROR")
        return False, username, password, "Incorrect username or password"


def commands(writer, client):
    display_data = """Welcome
        How can I help you
                create_folder <name>   -->  Create new folder <name>
                write_file <name> <input>  -->  Write <input> into <name> or Create a new file <name>
                read_file <name>   -->  Read data from the file <name> in the current working directory
                list   -->  View list of folders and files
                change_folder <name>   -->  Move the current working directory for the current user to the specified folder residing in the current folder
                register <username> <password>   -->  Register a new user to the server using the <username> and <password> provided
                login <username> <password>   -->  Log in the user conforming with <username> onto the server if the <password> provided matches the password used while registering
                quit   -->  Logout
        Please select the option  
    Select (Current working directory: {}): """.format(client.current_folder)
    writer.write(display_data.encode())


async def menu(reader, writer, status, username, password, message="Error"):
    if status:
        client = Client(username)
        commands(writer, client)
        while True:
            try:
                data = await reader.read(1000)
                if len(data) > 0:
                    choise = data.decode().strip().split(' ', 2)
                    if "quit" in choise[0]:
                        await replace("UserList.txt", f'{username}:{password}:Online\n', f'{username}:{password}\n')
                        break
                    elif "create_folder" in choise[0]:
                        name = choise[1]
                        writer.write("{}\nSelect (Current working directory: {}): ".format(
                            client.make_dir(name),
                            client.current_folder).encode())
                        writer.write(client.make_dir(name).encode())
                    elif "list" in choise[0]:
                        writer.write("{}\nSelect (Current working directory: {}): ".format(
                            client.list(),
                            client.current_folder).encode())
                    elif "write_file" in choise[0]:
                        writer.write("{}\nSelect (Current working directory: {}): ".format(
                            client.write_file(choise[1].encode(), choise[2].encode()),
                            client.current_folder).encode())
                    elif "change_folder" in choise[0]:
                        writer.write("{}\nSelect (Current working directory: {}): ".format(
                            client.change_folder(choise[1].encode()),
                            client.current_folder).encode())
                    elif "read_file" in choise[0]:
                        if len(choise) > 1:
                            writer.write("{}\nSelect (Current working directory: {}): ".format(
                                client.read_file(choise[1].encode()),
                                client.current_folder).encode())
                        else:
                            writer.write("{}\nSelect (Current working directory: {}): ".format(
                                client.read_file("".encode()),
                                client.current_folder).encode())
                    elif "register" in choise[0]:
                        register(reader, writer)
                    elif "commands" in choise[0]:
                        commands(writer, client)
                    else:
                        writer.write("\nSelect (Current working directory: {}): ".format(
                            client.current_folder
                        ).encode())
                else:
                    writer.write("\nSelect (Current working directory: {}): ".format(
                        client.current_folder
                    ).encode())
            except OSError:
                await replace("UserList.txt", f'{username}:{password}:Online\n', f'{username}:{password}\n')
                break;
    else:
        writer.write(message.encode())


async def start(reader, writer):
    try:
        message = "Are you a registered user?\npress y to yes\tpress n to no\nEnter your choice::"
        writer.write(message.encode())
        data = await reader.read(1000)
        answer = data.decode()
        if answer == "y":
            status, username, password, message = await login(reader, writer)
            await menu(reader, writer, status, username, password, message)
        elif answer == "n":
            await register(reader, writer)
            status, username, password, message = await login(reader, writer)
            await menu(reader, writer, status, username, password, message)
        else:
            message = "Invalid choice\nPlease restart client"
            writer.write(message.encode())
    except ConnectionResetError:
        pass


async def main():
    server = await asyncio.start_server(
        start, '127.0.0.1', 8088)

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr} started')

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
