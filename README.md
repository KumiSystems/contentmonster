# ContentMonster

ContentMonster is a Python package used to replicate the contents of directories on one server ("shore") to other servers ("vessels") using SFTP over unstable network connections. The files are split into smaller chunks which are transferred separately and reassembled on the server.

It comes with a daemon application (worker.py) which monitors the configured local directories for changes and instantly pushes them to the vessels. Once a file has been replicated to all vessels, it is moved to a "processed" subdirectory of its source directory and removed from the queue.

## Prerequisites

ContentMonster is written in Python3 and makes use of syntactical features introduced in Python 3.8. It depends on two packages installable by pip, paramiko (for SSH/SFTP connections) and watchdog (to monitor local directories for changes).

It was tested on Ubuntu 21.04 and Debian 10, but I don't see a reason why it would not work on other Unixoids or even Windows (although it might need some changes to properly work on the latter) as all dependencies are platform-independent.

Vessels (destination servers) need to have an SSH server with SFTP support. This has been tested with a default OpenSSH server as well as a Dropbear server with OpenSSH's sftp-server. They also have to provide the `cat` command which is used to reassemble the uploaded chunks.

## Installation

It is recommended that you use a virtual environment in order to maintain a clean Python environment independent from system updates and other Python projects on the same host. Note that you may have to install the `venv` package from your OS's package repositories first (on Debian-based distributions: `apt install python3-venv`).

In a terminal, navigate to the ContentMonster directory, then (assuming you are running bash) execute the following commands:

```bash
python3 -m venv venv  # Create a virtual environment in the "venv" subdirectory
. venv/bin/activate  # Activate the virtual environment (just in case)
pip install -Ur requirements.txt  # Install the package dependencies (paramiko/watchdog)
```

## Configuration

The application is configured using the `settings.ini` file. Start off by copying the provided `settings.example.ini` to `settings.ini` and opening it in a text editor. Note that all keys and values are case-sensitive. Required keys are identified as such in the comments below, all other keys are optional. The file consists of (at least) three sections:

### MONSTER

The `MONSTER` section contains a few global configuration options for the application:

```ini
[MONSTER]
ChunkSize = 10485760  # Size of individual chunks in bytes (default: 10 MiB)
```

### Directory

You can configure as many directories to be replicated as you want by adding multiple `Directory` sections. The directories are replicated to the same location on the vessels that they are located at on the shore.

```ini
[Directory sampledir]  # Each directory needs a unique name - here: "sampledir"
Location = /home/user/replication  # Required: File system location of the directory
```

Note: Currently, the same Location value is used on both the shore and the vessels, although this may be configurable in a future version. The directory has to be writable by the configured users on all of the configured vessels. In the above example, files are taken from /home/user/replication on the shore and put into /home/user/replication on each of the vessels.

### Vessel

You can configure as many vessels to replicate your files to as you want by adding multiple `Vessel` sections. All configured directories are replicated to all vessels. If you want to use an SSH key to authenticate on the vessels, make sure that it is picked up by the local SSH agent (i.e. you can login using the key when connecting with the `ssh` command).

```ini
[Vessel samplevessel]  # Each vessel needs a unique name - here: "samplevessel"
Address = example.com  # Required: Hostname / IP address of the vessel
TempDir = /tmp/.ContentMonster  # Temporary directory for uploaded chunks (default: /tmp/.ContentMonster) - needs to be writable
Username = replication  # Username to authenticate as on the vessel (default: same as user running ContentMonster)
Password = verysecret  # Password to use to authenticate on the vessel (default: none, use SSH key)
Passphrase = moresecret  # Passphrase of the SSH key you use to authenticate (default: none, key has no passphrase)
Port = 22  # Port of the SSH server on the vessel (default: 22)
```

Note: All configured directories are replicated to all of the configured vessels. This may be configurable in a future version.

## Running

To run the application after creating the `settings.ini`, navigate to ContentMonster's base directory in a terminal and make sure you are in the right virtual environment:

```bash
. venv/bin/activate
```

Then, you can run the worker like this:

```bash
python worker.py
```

Keep an eye on the output for the first minute or so, to check for any issues during initialization.

### systemd Service

You may want to run ContentMonster as a systemd service to make sure it starts automatically after a system reboot. Assuming that it is installed into `/opt/ContentMonster/` following the instructions above and supposed to run as the `replication` user, something like this should work:

```ini
[Unit]
Description=ContentMonster
After=syslog.target network.target

[Service]
Type=simple
User=replication
WorkingDirectory=/opt/ContentMonster/
ExecStart=/opt/ContentMonster/venv/python /opt/ContentMonster/worker.py
Restart=on-abort

[Install]
WantedBy=multi-user.target
```

Write this to `/etc/systemd/system/contentmonster.service`, then enable the service like this:

```bash
systemctl daemon-reload
systemctl enable --now contentmonster
systemctl status contentmonster  # Check that the service started properly
```

The service should now start automatically after every reboot. You can use commands like `systemctl status contentmonster` and `journalctl -xeu contentmonster` to keep an eye on the status of the service.