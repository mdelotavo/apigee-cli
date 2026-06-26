from typing import Dict, Type
from .base import BaseBackup

from .resources.apis import APIsBackup
from .resources.developers import DevelopersBackup
from .resources.apps import AppsBackup
from .resources.apiproducts import ApiProductsBackup
from .resources.caches import CachesBackup
from .resources.keyvaluemaps import KeyValueMapsBackup
from .resources.targetservers import TargetServersBackup
from .resources.userroles import UserRolesBackup


RESOURCE_REGISTRY: Dict[str, Type[BaseBackup]] = {
  "apis": APIsBackup,
  "developers": DevelopersBackup,
  "apps": AppsBackup,
  "apiproducts": ApiProductsBackup,
  "caches": CachesBackup,
  "keyvaluemaps": KeyValueMapsBackup,
  "targetservers": TargetServersBackup,
  "userroles": UserRolesBackup,
}