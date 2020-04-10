import network
import socket
import ure
import time
import machine
#from urllib.parse import unquote


def unquote(s):
    res = s.split('%')
    for i in range(1, len(res)):
        item = res[i]
        try:
            res[i] = chr(int(item[:2], 16)) + item[2:]
        except ValueError:
            res[i] = '%' + item
    return "".join(res)

GW_PROFILES = 'gw.dat'

server_socket = None

def get_setup():
    try:
        # Read GW config profiles from file
        setup = read_profiles()
        return setup

    except OSError as e:
        print("exception", str(e))

    # start web server for gw manager:
    start()
    setup = read_profiles()
    stop()
    return setup


def read_profiles():
    with open(GW_PROFILES) as f:
        lines = f.readlines()
    profiles = {}
    for line in lines:
        name, mode, host, port, username, password, epoch, dble = line.strip("\n").split(";")
        profiles["name"] = name
        profiles["mode"] = mode
        profiles["host"] = host
        profiles["port"] = port
        profiles["username"] = username
        profiles["password"] = password
        profiles["epoch"] = epoch
        profiles["dble"] = dble

    return profiles


def write_profiles(profiles):
    lines = []
    lines.append("%s;%s;%s;%s;%s;%s;%s;%s\n" % (profiles["name"],             
                                            profiles["mode"],           
                                            profiles["host"],
                                            profiles["port"],
                                            profiles["username"],
                                            profiles["password"],
                                            profiles["epoch"],
                                            profiles["dble"]))
    with open(GW_PROFILES, "w") as f:
        f.write(''.join(lines))


def send_header(client, status_code=200, content_length=None ):
    client.sendall("HTTP/1.0 {} OK\r\n".format(status_code))
    client.sendall("Content-Type: text/html\r\n")
    if content_length is not None:
      client.sendall("Content-Length: {}\r\n".format(content_length))
    client.sendall("\r\n")


def send_response(client, payload, status_code=200):
    content_length = len(payload)
    send_header(client, status_code, content_length)
    if content_length > 0:
        client.sendall(payload)
    client.close()


def handle_root(client):
    send_header(client)
    client.sendall("""\
        <html>
            <h1 style="color: #5e9ca0; text-align: center;">
                <span style="color: #ff0000;">
                    Configure your Ruuvi GW
                </span>
            </h1>
            <form action="configure" method="post">
                <table style="margin-left: auto; margin-right: auto;">
                    <tbody>
    """)
    client.sendall("""\
                        <tr>
                            <td>Name:</td>
                            <td><input name="name" type="name" value="Default" /></td>
                        </tr>
                        <tr>
                            <td>Mode:</td>
                            <td><input name="mode" type="number" min="0" max="1" value=0 /></td>
                        </tr>
                        <tr>
                            <td>Host/URL:</td>
                            <td><input name="host" type="host" /></td>
                        </tr>
                        <tr>
                            <td>Port:</td>
                            <td><input name="port" type="number" min="0" value=0 /></td>
                        </tr>
                        <tr>
                            <td>Username:</td>
                            <td><input name="username" type="username" /></td>
                        </tr>
                        <tr>
                            <td>Password:</td>
                            <td><input name="password" type="password" /></td>
                        </tr>
                        <tr>
                            <td>Use Epoch:</td>
                            <td><input name="epoch" type="number" min="0" max="1" value=0 /></td>
                        </tr>
                        <tr>
                            <td>Decode BLE:</td>
                            <td><input name="dble" type="number" min="0" max="1" value=0 /></td>
                        </tr>
                    </tbody>
                </table>
                <p style="text-align: center;">
                    <input type="submit" value="Submit" />
                </p>
            </form>
            <p>&nbsp;</p>
            <hr />
            <h5>
                <span style="color: #ff0000;">
                    Your Ruuvi GW configuration will be saved into the
                    "%(filename)s" file in your Ruuvi GW for future usage.
                    Ensure your Ruuvi GW is secured!
                </span>
            </h5>
            <hr />
        </html>
    """ % dict(filename=GW_PROFILES))
    client.close()

def handle_examples(client):
    send_header(client)
    client.sendall("""\
        <html>
            <h1 style="color: #5e9ca0; text-align: center;">
                <span style="color: #ff0000;">
                    Ruuvi GW Configuration Examples
                </span>
            </h1>
            <form action="configure" method="post">
                <table style="margin-left: auto; margin-right: auto;">
                    <tbody>
    """)
    client.sendall("""\
                       
                    </tbody>
            <hr />
            <h2 style="color: #2e6c80;">
                Exampe MQTT config is as follows:
            </h2>
            <ul>
                <li>
                    Name: test
                </li>
                <li>  
                    Mode: 1
                </li>
                <li>
                    Host: 192.168.0.2
                </li>
                <li>
                    Port: 1883
                </li>
                <li>
                    Username: user1
                </li>
                <li>
                    Password: safe
                </li>
                <li>
                    Use Epoch: 0
                </li>
                <li>
                    Decode BLE: 0
                </li>
            </ul>
            <hr />
            <h2 style="color: #2e6c80;">
                Exampe HTTP config is as follows:
            </h2>
            <ul>
                <li>
                    Name: test
                </li>
                <li>  
                    Mode: 0
                </li>
                <li>
                    Host: http://ptsv2.com/t/ruuvi-gw/post
                </li>
                <li>
                    Port: NA
                </li>
                <li>
                    Username: NA
                </li>
                <li>
                    Password: NA
                </li>
                <li>
                    Use Epoch: 0
                </li>
                <li>
                    Decode BLE: 0
                </li>
            </ul>
            <hr />
        </html>
    """)
    client.close()



def handle_configure(client, request):
    match = ure.search("name=(.*)&mode=(.*)&host=(.*)&port=(.*)&username=(.*)&password=(.*)&epoch=(.*)&dble=(.*)", request)

    if match is None:
        send_response(client, "Parameters not found", status_code=400)
        return False
    # version 1.9 compatibility
    try:
        name = match.group(1).decode("utf-8").replace("%3F", "?").replace("%21", "!")
        mode = match.group(2).decode("utf-8").replace("%3F", "?").replace("%21", "!")
        host = match.group(3).decode("utf-8").replace("%3F", "?").replace("%21", "!")
        port = match.group(4).decode("utf-8").replace("%3F", "?").replace("%21", "!")
        username = match.group(5).decode("utf-8").replace("%3F", "?").replace("%21", "!")
        password = match.group(6).decode("utf-8").replace("%3F", "?").replace("%21", "!")
        epoch = match.group(7).decode("utf-8").replace("%3F", "?").replace("%21", "!")
        dble = match.group(8).decode("utf-8").replace("%3F", "?").replace("%21", "!")
    except Exception:
        name = match.group(1).replace("%3F", "?").replace("%21", "!")
        mode = match.group(2).replace("%3F", "?").replace("%21", "!")
        host = match.group(3).replace("%3F", "?").replace("%21", "!")
        port = match.group(4).replace("%3F", "?").replace("%21", "!")
        username = match.group(5).replace("%3F", "?").replace("%21", "!")
        password = match.group(6).replace("%3F", "?").replace("%21", "!")
        epoch = match.group(7).replace("%3F", "?").replace("%21", "!")
        dble = match.group(8).replace("%3F", "?").replace("%21", "!")


    if len(name) == 0:
        send_response(client, "Name must be provided", status_code=400)
        return False
    
    if len(mode) == 0:
        send_response(client, "Mode must be provided", status_code=400)
        return False
    
    if len(host) == 0:
        send_response(client, "Host must be provided", status_code=400)
        return False
    
    if len(port) == 0:
        send_response(client, "Port must be provided", status_code=400)
        return False
    
    if len(username) == 0:
        send_response(client, "Username must be provided. If not required enter NA", status_code=400)
        return False
    
    if len(password) == 0:
        send_response(client, "Password must be provided. If not required enter NA", status_code=400)
        return False
    
    if len(epoch) == 0:
        send_response(client, "Use Epoch must be provided. If not required enter NA", status_code=400)
        return False
    
    if int(epoch) !=0 and int(epoch) !=1:
        send_response(client, "Use Epoch must be 0 or 1", status_code=400)
        return False
    
    if len(dble) == 0:
        send_response(client, "Decode BLE must be provided. If not required enter NA", status_code=400)
        return False
    
    if int(dble) !=0 and int(dble) !=1:
        send_response(client, "Decode BLE must be 0 or 1", status_code=400)
        return False

    if int(mode) !=0 and int(mode) !=1:
        send_response(client, "Mode must be 0 or 1", status_code=400)
        return False
    
    if int(mode) == 1:
        try:
            if not int(port) > 0:
                send_response(client, "Port must be greater then 0", status_code=400)
                return False
        except:
            send_response(client, "Port must be a number. For example 1883 for MQTT.", status_code=400)
            return False

    response = """\
            <html>
                <center>
                    <br><br>
                    <h1 style="color: #5e9ca0; text-align: center;">
                        <span style="color: #ff0000;">
                            Ruuvi GW successfully configured.
                        </span>
                    </h1>
                    <br><br>
                </center>
            </html>
        """
    host = unquote(host)
    password = unquote(password)
    username = unquote(username)

    send_response(client, response)
    profiles = {}
    profiles["name"] = name
    profiles["mode"] = mode
    profiles["host"] = host
    profiles["port"] = port
    profiles["username"] = username
    profiles["password"] = password
    profiles["epoch"] = epoch
    profiles["dble"] = epoch
    write_profiles(profiles)

    time.sleep(5)

    return True


def handle_not_found(client, url):
    send_response(client, "Path not found: {}".format(url), status_code=404)


def stop():
    global server_socket
    if server_socket:
        server_socket.close()
        server_socket = None


def start(port=80):
    global server_socket
    gw_configured = False
    try:
        addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]
        
        stop()

        server_socket = socket.socket()
        server_socket.bind(addr)
        server_socket.listen(1)
    except:
        machine.reset()

    print('To configure your Ruuvi GW, in a web browser')
    print('navigate to the assigned IP address of your Ruuvi GW')

    while True:
        if gw_configured:
            return True

        client, addr = server_socket.accept()
        print('client connected from', addr)
        try:
            client.settimeout(5.0)

            request = b""
            try:
                while "\r\n\r\n" not in request:
                    request += client.recv(512)
            except OSError:
                pass

            #print("Request is: {}".format(request))
            if "HTTP" not in request:  # skip invalid requests
                continue

            # version 1.9 compatibility
            try:
                url = ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request).group(1).decode("utf-8").rstrip("/")
            except Exception:
                url = ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request).group(1).rstrip("/")
            print("URL is {}".format(url))

            if url == "":
                handle_root(client)
            elif url == "configure":
                gw_configured = handle_configure(client, request)
            elif url == "examples":
                handle_examples(client)
            else:
                handle_not_found(client, url)

        finally:
            client.close()