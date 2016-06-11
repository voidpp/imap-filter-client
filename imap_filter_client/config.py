
import yaml
from voidpp_tools.config_loader import ConfigLoader, ConfigFormatter, ConfigFileNotFoundException

class YamlConfigFormatter(ConfigFormatter):

    def encode(self, data):
        return yaml.safe_dump(data)

    def decode(self, data):
        return yaml.load(data)

loader = ConfigLoader(YamlConfigFormatter(), __file__, nested = True)

try:
    config = loader.load('imap-filter-client.yaml')
except ConfigFileNotFoundException as e:
    print(e)
    print("See the example: https://github.com/voidpp/imap-filter-client/blob/master/imap-filter-client-example.yaml")
    config = None
