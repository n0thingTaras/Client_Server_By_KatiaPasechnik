import asyncio


async def read_request(reader, delimiter=b'!'):
    request = bytearray()
    while True:
        chunk = await reader.read(4)
        if not chunk:
            break
        request += chunk
        if delimiter in request:
            return request

    return None

# todo Надо сделать чтобы клиент вводил команды

async def input_func(reader, writer):
    data = await reader.read(10000)
    print(data.decode())
    username = input()
    writer.write(username.encode())
    data = await reader.read(10000)
    print(data.decode())
    password = input()
    writer.write(password.encode())


async def register(reader, writer):
    await input_func(reader, writer)
    data = await reader.read(10000)
    print(data.decode())


async def choise(reader, writer):
    while True:
        choise = input()
        if len(choise) == 0:
            continue
        writer.write(choise.encode())
        choise = choise.strip().split()
        if choise[0] == "exit":
            writer.close()
            print("Good buy")
            break
        if choise[0] == "register":
            await register(reader,writer)
        data = await reader.read(1000)
        print(data.decode())


async def login(reader, writer):
    await input_func(reader, writer)
    data = (await reader.read(1000)).decode()
    print(data)
    if "Welcome" in data:
        await choise(reader, writer)


async def start(reader, writer):
    data = await reader.read(10000)
    print(data.decode())
    answer = input()  # y or n
    writer.write(answer.encode())
    if answer == "n":
        await register(reader, writer)
        await login(reader, writer)
    elif answer == "y":
        await login(reader, writer)
    else:
        data = await reader.read(10000)
        print(data.decode())

async def main():
    reader, writer = await asyncio.open_connection('127.0.0.1', 8088)
    await start(reader, writer)


if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
