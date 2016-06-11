# About
This is a small python IMAP client daemon for filtering email messages.

# Install
`pip install imap-filter-client`

# Config
The config file will be searched in the next places:
- current working directory
- near the `imap-filter-client` executable file
- current user home directory
- under the `/etc` folder

The file name must be `imap-filter-client.yaml`

Example config: [imap-filter-client-example.yaml](https://github.com/voidpp/imap-filter-client/blob/master/imap-filter-client-example.yaml)

# Filtering
Filter config (at this time) must be written in python.
- create a python file
- set this python file's path to the config (`filters`)
- for examples see [filters-example.py](https://github.com/voidpp/imap-filter-client/blob/master/filters-example.py)

# CLI
For help see `imap-filter-client -h`
