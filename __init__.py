
try:
    from vistrails.core.configuration import ConfigurationObject
except ImportError:
    from core.configuration import ConfigurationObject


name = "GeoDataPortal"
identifier = "gov.usgs.GeoDataPortal"
version = '0.0.2'

configuration = \
    ConfigurationObject(cur_session_folder = r'C:\temp\SAHM_workspace',
                        cur_WPS_URL = "default")
