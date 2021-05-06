from os import path

#########################
# Paths                 #
#########################

APP_NAME = "esok"
APP_CONFIG_BASENAME = "{}.ini".format(APP_NAME)

ROOT_DIR = path.dirname(path.realpath(__file__))
RESOURCE_DIR = path.join(ROOT_DIR, "resources")
DEFAULT_CONFIG = path.join(RESOURCE_DIR, APP_CONFIG_BASENAME)


#########################
# Exit codes            #
#########################
UNKNOWN_ERROR = 1
USER_ERROR = 2
CONFIGURATION_ERROR = 3
CLUSTER_ERROR = 4
CLI_ERROR = 5
