#Help on class FortiManager in module pyFortiManagerAPI
python

# Inside the interpreter, type these lines one by one:
import pyFortiManagerAPI
help(pyFortiManagerAPI.FortiManager)

class FortiManager(builtins.object)
 |  FortiManager(host, username='admin', password='admin', adom='root', protocol='https', verify=True, proxies={})
 |
 |  This class will include all the methods used for executing the api calls on FortiManager.
 |
 |  Methods defined here:
 |
 |  __init__(self, host, username='admin', password='admin', adom='root', protocol='https', verify=True, proxies={})
 |      Initialize self.  See help(type(self)) for accurate signature.
 |
 |  add_address_group(self, name, members=<class 'list'>)
 |      Create your own group with just 2 parameters
 |      :param name: Enter the name of the address group                eg."Test_Group"
 |      :param members: pass your object names as members in a list     eg. ["LAN_10.1.1.0_24, "INTERNET"]
 |      :return: Response of status code with data in JSON Format
 |
 |  add_address_v6_group(self, name, members=<class 'list'>)
 |      Create your own group with just 2 parameters
 |      :param name: Enter the name of the address group                eg."Test_Group"
 |      :param members: pass your object names as members in a list     eg. ["LAN_10.1.1.0_24, "INTERNET"]
 |      :return: Response of status code with data in JSON Format
 |
 |  add_device(self, ip_address, username, password, name, description=False)
 |
 |  add_device_to_group(self, group, device, vdom)
 |
 |  add_dynamic_group(self, name, device, vdom, members: list, comment=None)
 |      Add per device mapping in address object.
 |      :param name: name of the address object.
 |      :param device: name of the device which is to be mapped in this object
 |      :param comment: comment
 |      :return: returns response of the request from FortiManager.
 |
 |  add_dynamic_object(self, name, device, subnet=<class 'list'>, comment=None)
 |      Add per device mapping in address object.
 |      :param name: name of the address object.
 |      :param device: name of the device which is to be mapped in this object
 |      :param subnet: subnet for device that is to be mapped in this object
 |      :param comment: comment
 |      :return: returns response of the request from FortiManager.
 |
 |  add_firewall_address_object(self, name, subnet: list, associated_interface='any', object_type=0, allow_routing=0)
 |      Create an address object using provided info
 |      :param name: Enter object name that is to be created
 |      :param associated_interface: Provide interface to which this object belongs if any. {Default is kept any}
 |      :param subnet: Enter the subnet in a list format eg.["1.1.1.1", "255.255.255.255"]
 |      :param object_type:
 |      :param allow_routing: Set routing if needed
 |      :return: Response of status code with data in JSON Format
 |
 |  add_firewall_address_v6_object(self, name, subnet6: str, object_type=0)
 |      Create an address object using provided info
 |      :param name: Enter object name that is to be created
 |      :param subnet: Enter the subnet in a string format "200x:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx/"128"
 |      :param object_type:
 |      :return: Response of status code with data in JSON Format
 |
 |  add_firewall_policy(self, policy_package_name: str, name: str, source_interface: str, source_address: str, destination_interface: str, destination_address: str, service: str, nat='disable', schedule='always', action=1, logtraffic=2)
 |      Create your own policy in FortiManager using the instance parameters.
 |      :param policy_package_name: Enter the name of the policy package                eg. "default"
 |      :param name: Enter the policy name in a string format                           eg. "Test Policy"
 |      :param source_interface: Enter the source interface in a string format          eg. "port1"
 |      :param source_address: Enter the src. address object name in string format      eg. "LAN_10.1.1.0_24"
 |      :param destination_interface: Enter the source interface in a string format     eg. "port2"
 |      :param destination_address: Enter the dst. address object name                  eg. "WAN_100.25.1.63_32"
 |      :param service: Enter the service you want to permit or deny in string          eg. "ALL_TCP"
 |      :param nat: Enter enable or disable for nat in a string format                  eg. 'disable'
 |      :param schedule: Schedule time is kept 'always' as default.
 |      :param action: Permit(1) or Deny(0) the traffic. Default is set to Permit.
 |      :param logtraffic: Specify if you need to log all traffic or specific in int format.
 |                          logtraffic=0: Means No Log
 |                          logtraffic=1 Means Log Security Events
 |                          logtraffic=2 Means Log All Sessions
 |      :return: Response of status code with data in JSON Format
 |
 |  add_firewall_policy_with_v6(self, policy_package_name: str, name: str, source_interface: str, source_address: Any, source_address6: Any, destination_interface: str, destination_address: Any, destination_address6: Any, service: str, nat='disable', schedule='always', action=1, logtraffic=2)
 |      Create your own policy in FortiManager using the instance parameters.
 |      :param policy_package_name: Enter the name of the policy package                eg. "default"
 |      :param name: Enter the policy name in a string format                           eg. "Test Policy"
 |      :param source_interface: Enter the source interface in a string format          eg. "port1"
 |      :param source_address: Enter the src. address object name in string format or in a list Format      eg. "LAN_10.1.1.0_24" or ["LAN_10.1.1.0_24", "LAN_10.2.2.0_24"]
 |      :param source_address6: Enter the src. address v6 object name in string format or in a list Format      eg. "LAN_200x-000-" or ["LAN_2001-000", "LAN_2002-1000"]
 |      :param destination_interface: Enter the source interface in a string format     eg. "port2"
 |      :param destination_address: Enter the dst. address object name in string or list format                  eg. "WAN_100.25.1.63_32" or ["WAN1", "WAN2"]
 |      :param destination_address6: Enter the dst. address object name in string or list format                  eg. "WANv6_200a-200a-" or or ["WAN1v6", "WAN2v6"]
 |      :param service: Enter the service you want to permit or deny in string          eg. "ALL_TCP"
 |      :param nat: Enter enable or disable for nat in a string format                  eg. 'disable'
 |      :param schedule: Schedule time is kept 'always' as default.
 |      :param action: Permit(1) or Deny(0) the traffic. Default is set to Permit.
 |      :param logtraffic: Specify if you need to log all traffic or specific in int format.
 |                          logtraffic=0: Means No Log
 |                          logtraffic=1 Means Log Security Events
 |                          logtraffic=2 Means Log All Sessions
 |      :return: Response of status code with data in JSON Format
 |
 |  add_install_target(self, device_name, pkg_name, vdom: str = 'root')
 |      Add a device to installation target list of the policy package
 |      :param device_name: name of the device
 |      :param pkg_name: name of the policy package
 |      :param vdom: name of the vdom (default=root)
 |      :return: returns response from FortiManager api whether is was a success or failure.
 |
 |  add_meta_data(self, name, importance=0, status=1)
 |      Add a meta tag in the FortiManager.
 |      :param name: name of the meta tag
 |      :param importance: importance of meta tag
 |      :param status: status of meta tag whether it should be active(1) or disabled(0)
 |      :return: returns response from FortiManager API whether the request was successful or not.!
 |
 |  add_model_device(self, name, serial_no, username='admin', password='', os_ver=6, mr=4, os_type='fos', platform='')
 |
 |  add_policy_package(self, name)
 |      Can add your own policy package in FortiManager
 |      :param name: Specific the Package Name
 |      :return: Response of status code with data in JSON Format
 |
 |  assign_interfaces_to_zone(self, device_name, zone, interfaces_list: list, vdom)
 |
 |  assign_meta_to_device(self, device, meta_name, meta_value)
 |      Assign a meta tag to the device
 |      :param device: name of the device
 |      :param meta_name: name of the meta tag
 |      :param meta_value: value of the meta tag
 |      :return: returns response from FortiManager API whether the request was successful or not.!
 |
 |  assign_meta_to_device_vdom(self, device, vdom, meta_name, meta_value)
 |      Assign a meta tag to the device
 |      :param device: name of the device
 |      :param vdom: Specify the Vdom
 |      :param meta_name: name of the meta tag
 |      :param meta_value: value of the meta tag
 |      :return: returns response from FortiManager API whether the request was successful or not.!
 |
 |  backup_config_of_fortiGate_to_tftp(self, tftp_ip, path, script_name, filename, device_name, vdom='root')
 |      A small function to backup configuration on FortiGates from FortiManager and store it in TFTP Server.
 |      :param tftp_ip: Specify TFTP Server IP
 |      :param path: Specify the path to store the config
 |      :param script_name: Specify the Script name
 |      :param filename: Specify the name of the backup file
 |      :param device_name: Specify the name of the device
 |      :param vdom: Specify the Vdom
 |
 |  create_device_group(self, name, description='')
 |
 |  create_interface(self, device, name, interface, role, vdom, vlan, ip, mask, alias)
 |
 |  create_script(self, name: str, script_content: str, target: int = 0)
 |      Create a script template and store it on FortiManager
 |      :param name: Specify a name for the script
 |      :param script_content: write the cli commands
 |      :param target:
 |              If Target = 0 than script runs on Device database
 |              If Target = 1 than script runs on Remote FortiGate CLI
 |              If Target = 2 than script runs on Policy package or Adom Database
 |      Default value is set to 0
 |
 |  create_script_group(self, name: str, target: int = 0)
 |      Create a script template and store it on FortiManager
 |      :param name: Specify a name for the script
 |      :param script_content: write the cli commands
 |      :param target:
 |              If Target = 0 than script runs on Device database
 |              If Target = 1 than script runs on Remote FortiGate CLI
 |              If Target = 2 than script runs on Policy package or Adom Database
 |      Default value is set to 0
 |
 |  create_zone(self, device_name, zone, vdom)
 |
 |  custom_api(self, payload)
 |      Execute an API call manually by defining the payload
 |      :param payload: specify the valid payload in a dict.
 |      :return: returns response of the API call from FortiManager
 |
 |  delete_address_group(self, name)
 |      Delete the Address group if no longer needed
 |      :param name: Specify the name of the address you wish to delete
 |      :return: Response of status code with data in JSON Format
 |
 |  delete_address_v6_group(self, name)
 |      Delete the Address group if no longer needed
 |      :param name: Specify the name of the address you wish to delete
 |      :return: Response of status code with data in JSON Format
 |
 |  delete_device_to_group(self, group, device, vdom)
 |
 |  delete_firewall_address_object(self, object_name)
 |      Delete the address object if no longer needed using object name
 |      :param object_name: Enter the Object name you want to delete
 |      :return: Response of status code with data in JSON Format
 |
 |  delete_firewall_address_v6_object(self, object_name)
 |      Delete the address object if no longer needed using object name
 |      :param object_name: Enter the Object name you want to delete
 |      :return: Response of status code with data in JSON Format
 |
 |  delete_firewall_policy(self, policy_package_name, policyid)
 |      Delete the policy if not is use with the policyID
 |      :param policy_package_name: Enter the policy package name in which you policy belongs
 |      :param policyid: Enter the policy ID of the policy you want to delete
 |      :return: Response of status code with data in JSON Format
 |
 |  delete_script(self, name: str)
 |      Create a script template and store it on FortiManager
 |      :param name: Specify the script name which needs to be deleted
 |
 |  get_address_groups(self, name=False)
 |      Get the address groups created in your FortiManager
 |      :param name: You can filter out the specific address group which you want to see
 |      :return: Response of status code with data in JSON Format
 |
 |  get_address_v6_groups(self, name=False)
 |      Get the address groups created in your FortiManager
 |      :param name: You can filter out the specific address group which you want to see
 |      :return: Response of status code with data in JSON Format
 |
 |  get_adoms(self, name=False)
 |      Get all adoms from the FortiManager
 |      :param name: Can get specific adom using name as a filter
 |      :return: Response of status code with data in JSON Format
 |
 |  get_all_scripts(self)
 |      Get all script templates from FortiManager
 |
 |  get_device(self, device)
 |      :return: returns list of devices added in FortiManager
 |
 |  get_devices(self)
 |      :return: returns list of devices added in FortiManager
 |
 |  get_dhcp(self, device)
 |      Get dhcp details from the devices.
 |      :param device: Specify name of the device.
 |
 |  get_dhcp_servers(self, device, vdom)
 |
 |  get_firewall_address_objects(self, name=False)
 |      Get all the address objects data stored in FortiManager
 |      :return: Response of status code with data in JSON Format
 |
 |  get_firewall_address_v6_objects(self, name=False)
 |      Get all the address v6 objects data stored in FortiManager
 |      :return: Response of status code with data in JSON Format
 |
 |  get_firewall_footer_policies(self, policy_package_name='default', policyid=False)
 |      Get adom footer policies
 |
 |  get_firewall_header_policies(self, policy_package_name='default', policyid=False)
 |      Get adom header policies
 |
 |  get_firewall_policies(self, policy_package_name='default', policyid=False)
 |      Get the firewall policies present in the policy package
 |      :param policy_package_name: Enter the policy package name
 |      :param policyid: Can filter and get the policy you want using policyID
 |      :return: Response of status code with data in JSON Format
 |
 |  get_firewall_vip_objects(self, name=False)
 |      Get all the vip objects data stored in FortiManager
 |      :return: Response of status code with data in JSON Format
 |
 |  get_global_footer_policies(self, policy_package_name='default', policyid=False)
 |      Get global footer policies
 |
 |  get_global_header_policies(self, policy_package_name='default', policyid=False)
 |      Get global header policies
 |
 |  get_interface(self, device, interface)
 |
 |  get_interfaces(self, device)
 |      # Firewall Interfaces
 |
 |  get_meta_data(self)
 |      Get all the meta tags present in the FortiManager
 |      :return: returns meta tags present in FortiManager
 |
 |  get_policies_assigned_to_device(self, device, vdom)
 |
 |  get_policy_packages(self, name=False)
 |      Get all the policy packages configured on FortiManager
 |      :param name: Can get specific package using name as a filter
 |      :return: Response of status code with data in JSON Format
 |
 |  get_script_output(self, device_name: str, vdom: str)
 |      Get all scripts output from [device] on FortiManager
 |      :param device_name: Specify device name.
 |      :param vdom: Specify the Vdom
 |
 |  get_service(self, name)
 |      Get interface details from the devices.
 |      :param name: Specify name of the device.
 |
 |  get_services(self)
 |      Get interface details from the devices.
 |      :param device: Specify name of the device.
 |
 |  get_zone(self, device_name, zone, vdom)
 |
 |  get_zones(self, device_name, vdom)
 |
 |  install_policy_package(self, package_name)
 |      Install the policy package on your Forti-gate Firewalls
 |      :param package_name: Enter the package name you wish to install
 |      :return: Response of status code with data in JSON Format
 |
 |  install_policy_package_to_device(self, package_name, device, vdom)
 |      Install the policy package on your Forti-gate Firewalls
 |      :param vdom: Sepcify the VDOM
 |      :param device: Sepcify the target device name
 |      :param package_name: Enter the package name you wish to install
 |      :return: Response of status code with data in JSON Format
 |
 |  lock_adom(self, name=False)
 |
 |  login(self)
 |      Log in to FortiManager with the details provided during object creation of this class
 |      :return: Session
 |
 |  logout(self)
 |      Logout from FortiManager
 |      :return: Response of status code with data in JSON Format
 |
 |  move_firewall_policy(self, policy_package_name, move_policyid=<class 'int'>, option='before', policyid=<class 'int'>)
 |      Move the policy as per your needs
 |      :param policy_package_name: Enter the policy package name in which you policy belongs
 |      :param move_policyid: Enter the policy ID of the policy you want to move
 |      :param option: Specify if you want to move above("before") the target policy or below("after") {default: before}
 |      :param policyid: Specify the target policy
 |      :return: Response of status code with data in JSON Format
 |
 |  policy_lookup(self, device, source_interface, source_ip, destination_ip, protocol, port, vdom='root')
 |      # Policy Lookup
 |
 |  quick_db_install(self, device_name: str, vdom: str)
 |
 |  run_script_on_multiple_devices(self, script_name: str, devices: List[dict])
 |      Create a script template and store it on FortiManager
 |      :param devices: Specify devices in a list of dictionaries.
 |              eg. devices=[{"name": "FortiGateVM64-1", "vdom": "root"},
 |                           {"name": "FortiGateVM64-2", "vdom": "test"}
 |                           {"name": "FortiGateVM64-3", "vdom": "root"}]
 |      :param script_name: Specify the script name that should be executed on the specified devices
 |
 |  run_script_on_single_device(self, script_name: str, device_name: str, vdom: str)
 |      Create a script template and store it on FortiManager
 |      :param device_name: Specify device name.
 |      :param vdom: Specify the Vdom
 |      :param script_name: Specify the script name that should be executed on the specified devices
 |
 |  set_adom(self, adom=None)
 |
 |  track_quick_db_install(self, taskid)
 |
 |  unlock_adom(self, name=False)
 |
 |  update_address_group(self, name, object_name, do='add')
 |      Update Members of the Address group
 |      :param name: Specify the name of the Address group you want to update
 |      :param object_name: Specify name of the object you wish to update(add/remove) in Members List
 |      :param do: Specify if you want to add or remove the object from the members list
 |                  do="add"    will add the object in the address group
 |                  do="remove" will remove the object from address group
 |      :return: Response of status code with data in JSON Format
 |
 |  update_address_v6_group(self, name, object_name, do='add')
 |      Update Members of the Address group
 |      :param name: Specify the name of the Address group you want to update
 |      :param object_name: Specify name of the object you wish to update(add/remove) in Members List
 |      :param do: Specify if you want to add or remove the object from the members list
 |                  do="add"    will add the object in the address group
 |                  do="remove" will remove the object from address group
 |      :return: Response of status code with data in JSON Format
 |
 |  update_dynamic_object(self, name, device, subnet: list, do='add', comment=None)
 |      Update the per mapping settings of the address object.
 |      :param name: name of the object that needs to be updated.
 |      :param device: name of the device that needs to be added/updated
 |      :param subnet: updated subnet of the device that needs to be mapped
 |      :param do: if parameter do is set to "add" it will update it. If it is set to "remove" it will be deleted.
 |      :param comment: add comment if you want.
 |      :return: return result of the request from FortiManager.
 |
 |  update_firewall_address_object(self, name, **data)
 |      Get the name of the address object and update it with your data
 |      :param name: Enter the name of the object that needs to be updated
 |      :param data: You can get the **kwargs parameters with "show_params_for_object_update()" method
 |      :return: Response of status code with data in JSON Format
 |
 |  update_firewall_address_v6_object(self, name, **data)
 |      Get the name of the address object and update it with your data
 |      :param name: Enter the name of the object that needs to be updated
 |      :param data: You can get the **kwargs parameters with "show_params_for_object_v6_update()" method
 |      :return: Response of status code with data in JSON Format
 |
 |  update_firewall_policy(self, policy_package_name, policyid, **data)
 |      Update your policy with your specific needs
 |      :param policy_package_name: Enter the policy package name in which you policy belongs
 |      :param policyid: Enter the Policy ID you want to edit
 |      :param data: You can get the **kwargs parameters with "show_params_for_policy_update()" method
 |      :return: Response of status code with data in JSON Format
 |
 |  update_script(self, oid: int, name: str, script_content: str, target: int = 0)
 |      Create a script template and store it on FortiManager
 |      :param oid: Specify the script OID which needs to be updated
 |      :param name: Specify a name for the script
 |      :param script_content: write the cli commands
 |      :param target:
 |              If Target = 0 than script runs on Device database
 |              If Target = 1 than script runs on Remote FortiGate CLI
 |              If Target = 2 than script runs on Policy package or Adom Database
 |      Default value is set to 0
 |
 |  ----------------------------------------------------------------------
 |  Static methods defined here:
 |
 |  make_data(_for='policy', **kwargs)
 |
 |  show_params_for_object_update()
 |
 |  show_params_for_object_v6_update()
 |
 |  show_params_for_policy_update()
 |
 |  show_params_for_policy_v6_update()
 |
 |  ----------------------------------------------------------------------
 |  Data descriptors defined here:
 |
 |  __dict__
 |      dictionary for instance variables
 |
 |  __weakref__
 |      list of weak references to the object