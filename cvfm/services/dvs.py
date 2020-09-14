import logging

from cvfm.services.base import Service

logger = logging.getLogger(__name__)

__all__ = ["DistributedVirtualSwitchService"]


class DistributedVirtualSwitchService(Service):
    def populate_db_with_supported_dvses(self):
        ports = self._vnc_api_client.read_all_ports(fields=["esxi_port_info"])
        for port in ports:
            esxi_props = port.get("esxi_port_info")
            if not esxi_props:
                continue
            dvs_name = esxi_props.get("dvs_name")
            if dvs_name:
                self._database.add_supported_dvs(dvs_name)
                logger.debug("DVS %s added as a supported DVS", dvs_name)
