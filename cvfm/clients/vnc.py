import json

from builtins import object
import logging

from vnc_api import vnc_api

from cvfm import constants as const
from cvfm.clients import utils
from cvfm.exceptions import VNCAdminProjectNotFound

__all__ = ["VNCAPIClient", "has_proper_creator"]

logger = logging.getLogger(__name__)


def has_proper_creator(vnc_object):
    id_perms = vnc_object.get("id_perms")
    if id_perms is not None:
        return id_perms.get("creator") == const.ID_PERMS.get_creator()
    return False


@utils.api_client_error_translator(utils.raises_vnc_conn_error)
class VNCAPIClient(object):
    def __init__(self, vnc_cfg, auth_cfg=None):
        if auth_cfg is None:
            auth_cfg = {}
        self.vnc_lib = vnc_api.VncApi(
            api_server_host=vnc_cfg.get("api_server_host"),
            api_server_port=vnc_cfg.get("api_server_port"),
            api_server_use_ssl=vnc_cfg.get("api_server_use_ssl"),
            apicertfile=vnc_cfg.get("api_certfile"),
            apikeyfile=vnc_cfg.get("api_keyfile"),
            apicafile=vnc_cfg.get("api_cafile"),
            apiinsecure=vnc_cfg.get("api_server_insecure"),
            username=auth_cfg.get("auth_user"),
            password=auth_cfg.get("auth_password"),
            tenant_name=auth_cfg.get("auth_tenant"),
            auth_token_url=auth_cfg.get("auth_token_url"),
            timeout=180,
        )
        self.project_name = vnc_cfg.get("project_name", const.VNC_PROJECT_NAME)
        self.check_project()

    def get_project(self):
        try:
            return self.vnc_lib.project_read(
                [const.VNC_PROJECT_DOMAIN, self.project_name]
            )
        except vnc_api.NoIdError:
            logger.error("Unable to read project %s in VNC", self.project_name)
            raise VNCAdminProjectNotFound()

    def check_project(self):
        logger.info("Checking admin project existence in VNC...")
        self.get_project()
        logger.info("admin project exists in VNC")

    def read_fabric(self, fabric_uuid):
        return self.vnc_lib.fabric_read(id=fabric_uuid)

    def create_vn(self, vnc_vn):
        try:
            self.vnc_lib.virtual_network_create(vnc_vn)
            logger.info("Created VN with name: %s in VNC", vnc_vn.name)
        except vnc_api.RefsExistError:
            logger.info("VN %s already exists in VNC", vnc_vn.name)

    def create_vpg(self, vnc_vpg):
        try:
            self.vnc_lib.virtual_port_group_create(vnc_vpg)
            logger.info("Created VPG with name: %s in VNC", vnc_vpg.name)
        except vnc_api.RefsExistError:
            logger.info("VPG %s already exists in VNC", vnc_vpg.name)

    def create_vmi(self, vnc_vmi):
        try:
            self.vnc_lib.virtual_machine_interface_create(vnc_vmi)
            logger.info("Created VMI with name: %s in VNC", vnc_vmi.name)
        except vnc_api.RefsExistError:
            logger.info("VMI %s already exists in VNC", vnc_vmi.name)

    def read_all_vns(self):
        vns_in_vnc = self.vnc_lib.virtual_networks_list(
            parent_id=self.get_project().get_uuid(), fields=["id_perms"]
        )["virtual-networks"]
        return [vn for vn in vns_in_vnc if has_proper_creator(vn)]

    def read_all_vpgs(self):
        vpgs_in_vnc = self.vnc_lib.virtual_port_groups_list(
            fields=["id_perms"]
        )["virtual-port-groups"]
        return [vpg for vpg in vpgs_in_vnc if has_proper_creator(vpg)]

    def read_all_vmis(self):
        vmis_in_vnc = self.vnc_lib.virtual_machine_interfaces_list(
            parent_id=self.get_project().get_uuid(), fields=["id_perms"]
        )["virtual-machine-interfaces"]
        return [vmi for vmi in vmis_in_vnc if has_proper_creator(vmi)]

    def read_vn(self, vn_uuid):
        try:
            return self.vnc_lib.virtual_network_read(id=vn_uuid)
        except vnc_api.NoIdError:
            logger.info("VN %s not found in VNC", vn_uuid)
        return None

    def read_vpg(self, vpg_uuid):
        try:
            return self.vnc_lib.virtual_port_group_read(id=vpg_uuid)
        except vnc_api.NoIdError:
            logger.info("VPG %s not found in VNC", vpg_uuid)
        return None

    def read_vmi(self, vmi_uuid):
        try:
            return self.vnc_lib.virtual_machine_interface_read(id=vmi_uuid)
        except vnc_api.NoIdError:
            logger.info("VMI %s not found in VNC", vmi_uuid)
        return None

    def update_vpg(self, vnc_vpg):
        try:
            self.vnc_lib.virtual_port_group_update(vnc_vpg)
            logger.info("Updated VPG with name: %s", vnc_vpg.name)
        except vnc_api.NoIdError:
            logger.info(
                "VPG %s not found in VNC, unable to update", vnc_vpg.uuid
            )

    def delete_vmi(self, vmi_uuid):
        self.detach_vmi_from_vpg(vmi_uuid)
        try:
            self.vnc_lib.virtual_machine_interface_delete(id=vmi_uuid)
            logger.info("VMI %s deleted from VNC", vmi_uuid)
        except vnc_api.NoIdError:
            logger.info("VMI %s not found in VNC, unable to delete", vmi_uuid)

    def delete_vpg(self, vpg_uuid):
        try:
            self.vnc_lib.virtual_port_group_delete(id=vpg_uuid)
            logger.info("VPG %s deleted from VNC", vpg_uuid)
        except vnc_api.NoIdError:
            logger.info("VPG %s not found in VNC, unable to delete", vpg_uuid)

    def delete_vn(self, vn_uuid):
        vnc_vn = self.read_vn(vn_uuid)

        vmi_refs = vnc_vn.get_virtual_machine_interface_back_refs() or ()
        vmi_uuids = [vmi_ref["uuid"] for vmi_ref in vmi_refs]
        for vmi_uuid in vmi_uuids:
            self.delete_vmi(vmi_uuid)

        try:
            self.vnc_lib.virtual_network_delete(id=vn_uuid)
            logger.info("VN %s deleted from VNC", vn_uuid)
        except vnc_api.NoIdError:
            logger.info("VN %s not found in VNC, unable to delete", vn_uuid)

    def read_all_physical_routers(self, fields=None):
        return self.vnc_lib.physical_routers_list(fields=fields)[
            "physical-routers"
        ]

    def get_nodes_by_host_names(self, esxi_names, fields=None):
        filters = {"name": esxi_names}
        return self.vnc_lib.nodes_list(fields=fields, filters=filters)["nodes"]

    def get_node_ports(self, node, fields=None):
        port_uuids = [port_ref["uuid"] for port_ref in node.get("ports")]
        return self.vnc_lib.ports_list(fields=fields, obj_uuids=port_uuids)[
            "ports"
        ]

    def read_all_ports(self, fields=None):
        return self.vnc_lib.ports_list(fields=fields)["ports"]

    def read_pi(self, pi_uuid):
        try:
            return self.vnc_lib.physical_interface_read(id=pi_uuid)
        except vnc_api.NoIdError:
            logger.info("Physical Interface %s not found in VNC", pi_uuid)

    def get_pis_by_port(self, port, fields=None):
        pi_uuids = [
            pi_ref["uuid"]
            for pi_ref in port.get("physical_interface_back_refs", ())
        ]
        return self.vnc_lib.physical_interfaces_list(
            fields=fields, obj_uuids=pi_uuids
        )["physical-interfaces"]

    def attach_pis_to_vpg(self, vpg, physical_interfaces):
        if not physical_interfaces:
            return
        for pi in physical_interfaces:
            vpg.add_physical_interface(pi)
            pi_display_name = ":".join(pi.fq_name[1:])
            logger.info(
                "Attached physical interface %s to VPG %s",
                pi_display_name,
                vpg.name,
            )
        self.vnc_lib.virtual_port_group_update(vpg)

    def detach_pis_from_vpg(self, vpg, physical_interface_uuids):
        if not physical_interface_uuids:
            return
        for pi_uuid in physical_interface_uuids:
            pi = self.read_pi(pi_uuid)
            vpg.del_physical_interface(pi)
            pi_display_name = ":".join(pi.fq_name[1:])
            logger.info(
                "Detached physical interface %s from VPG %s",
                pi_display_name,
                vpg.name,
            )
        self.vnc_lib.virtual_port_group_update(vpg)

    def detach_vmi_from_vpg(self, vmi_uuid):
        vmi = self.read_vmi(vmi_uuid)
        if vmi is None:
            return
        vpg_refs = vmi.get_virtual_port_group_back_refs()
        if vpg_refs is None:
            return
        vpg_ref = vpg_refs[0]
        vpg = self.read_vpg(vpg_ref["uuid"])
        vpg.del_virtual_machine_interface(vmi)
        self.update_vpg(vpg)
        logger.info("VMI %s detached from VPG %s", vmi.name, vpg.name)
        if not vpg.get_virtual_machine_interface_refs():
            self.delete_vpg(vpg.uuid)

    def create_vmi_bindings(self, vnc_vmi, vnc_vpg):
        pi_info = [
            (pi_ref["to"][2], pi_ref["to"][1])
            for pi_ref in vnc_vpg.get_physical_interface_refs() or ()
        ]

        profile = {
            "local_link_information": [
                {
                    "port_id": port_id,
                    "switch_id": port_id,
                    "fabric": vnc_vpg.fq_name[1],
                    "switch_info": switch_name,
                }
                for port_id, switch_name in pi_info
            ]
        }

        kv_pairs = vnc_api.KeyValuePairs(
            [
                vnc_api.KeyValuePair(key="vpg", value=vnc_vpg.name),
                vnc_api.KeyValuePair(key="vnic_type", value="baremetal"),
                vnc_api.KeyValuePair(key="profile", value=json.dumps(profile)),
            ]
        )

        existing_bindings = vnc_vmi.get_virtual_machine_interface_bindings()
        if existing_bindings is not None and set(
            existing_bindings.get_key_value_pair()
        ) == set(kv_pairs.get_key_value_pair()):
            return

        vnc_vmi.set_virtual_machine_interface_bindings(kv_pairs)
        self.vnc_lib.virtual_machine_interface_update(vnc_vmi)

    def get_vn_vlan(self, vnc_vn):
        vmi_refs = vnc_vn.get_virtual_machine_interface_back_refs() or ()
        if len(vmi_refs) == 0:
            return None
        vmi_ref = vmi_refs[0]
        vmi_uuid = vmi_ref["uuid"]
        vnc_vmi = self.read_vmi(vmi_uuid)
        vmi_properties = vnc_vmi.get_virtual_machine_interface_properties()
        return vmi_properties.get_sub_interface_vlan_tag()

    def get_vmis_by_vn(self, vnc_vn):
        vmi_uuids = [
            vmi_ref["uuid"]
            for vmi_ref in vnc_vn.get_virtual_machine_interface_back_refs()
            or ()
        ]
        return self.vnc_lib.virtual_machine_interfaces_list(
            detail=True, obj_uuids=vmi_uuids
        )

    def recreate_vmi_with_new_vlan(self, old_vnc_vmi, vnc_vn, new_vlan):
        logger.info(
            "Recreating VMI %s with new vlan %s in VNC",
            old_vnc_vmi.name,
            new_vlan,
        )
        vpg_ref = old_vnc_vmi.get_virtual_port_group_back_refs()[0]
        vnc_vpg = self.read_vpg(vpg_ref["uuid"])
        new_vnc_vmi = self._create_vnc_vmi_obj_with_new_vlan(
            new_vlan, old_vnc_vmi, vnc_vn
        )
        self._delete_old_vmi(old_vnc_vmi, vnc_vpg)
        self._create_new_vmi(new_vnc_vmi, vnc_vpg)
        logger.info(
            "Recreated VMI %s with new vlan %s in VNC",
            old_vnc_vmi.name,
            new_vlan,
        )

    def _create_vnc_vmi_obj_with_new_vlan(self, new_vlan, old_vnc_vmi, vnc_vn):
        new_vnc_vmi = vnc_api.VirtualMachineInterface(
            name=old_vnc_vmi.name, parent_obj=self.get_project()
        )
        new_vnc_vmi.set_uuid(old_vnc_vmi.uuid)
        new_vnc_vmi.add_virtual_network(vnc_vn)
        vmi_properties = vnc_api.VirtualMachineInterfacePropertiesType(
            sub_interface_vlan_tag=new_vlan
        )
        new_vnc_vmi.set_virtual_machine_interface_properties(vmi_properties)
        new_vnc_vmi.set_id_perms(const.ID_PERMS)
        vmi_bindings = old_vnc_vmi.get_virtual_machine_interface_bindings()
        new_vnc_vmi.set_virtual_machine_interface_bindings(vmi_bindings)
        return new_vnc_vmi

    def _delete_old_vmi(self, vnc_vmi, vnc_vpg):
        vnc_vpg.del_virtual_machine_interface(vnc_vmi)
        logger.info("Detached VMI %s from VPG %s", vnc_vmi.name, vnc_vpg.name)
        self.update_vpg(vnc_vpg)
        self.vnc_lib.virtual_machine_interface_delete(id=vnc_vmi.uuid)
        logger.info("Deleted VMI %s from VNC", vnc_vmi.name)

    def _create_new_vmi(self, new_vnc_vmi, vnc_vpg):
        self.create_vmi(new_vnc_vmi)
        vnc_vpg.add_virtual_machine_interface(new_vnc_vmi)
        logger.info(
            "Attached VMI %s from VPG %s", new_vnc_vmi.name, vnc_vpg.name
        )
        self.update_vpg(vnc_vpg)
