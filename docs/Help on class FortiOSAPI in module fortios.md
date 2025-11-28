Help on class FortiOSAPI in module fortiosapi.fortiosapi:
python
# Inside the interpreter, type these lines one by one:
import fortiosapi
help(fortiosapi.FortiOSAPI)

class FortiOSAPI(builtins.object)
 |  Global class / example for FortiOSAPI
 |
 |  Methods defined here:
 |
 |  __init__(self)
 |      Initialize self.  See help(type(self)) for accurate signature.
 |
 |  check_session(self)
 |      Helper fonction to check if the session on the FortiOSAPI object is valid
 |      :return:
 |          True or raise NotLogged or InvalidLicense
 |
 |  cmdb_url(self, path, name, vdom=None, mkey=None)
 |
 |  delete(self, path, name, vdom=None, mkey=None, parameters=None, data=None)
 |      Delete a pointed object in the cmdb.
 |
 |      :param path: first part of the Fortios API URL like
 |      :param name: https://myfgt:8040/api/v2/cmdb/<path>/<name>
 |      :param data: json containing the param/values of the object to be set
 |      :param mkey: when the cmdb object have a subtable mkey represent the subobject.
 |                   It is optionnal at creation the code will find the mkey name for you.
 |      :param vdom: the vdom on which you want to apply config or global for global settings
 |      :param parameters: Add on parameters understood by the API call can be "&select=" for example
 |      :return:
 |          A formatted json with the last response from the API
 |
 |  download(self, path, name, vdom=None, mkey=None, parameters=None)
 |      Use the download call on the monitoring part of the API.
 |      Can get the config, logs etc..
 |
 |      :param path: first part of the Fortios API URL like
 |      :param name: https://myfgt:8040/api/v2/cmdb/<path>/<name>
 |      :param mkey: when the cmdb object have a subtable mkey represent the subobject.
 |                   It is optionnal at creation the code will find the mkey name for you.
 |      :param vdom: the vdom on which you want to apply config or global for global settings
 |      :param parameters: Add parameters understood by the API call in json. Must set "destination": "file" and scope
 |      :return:
 |          The file is part of the returned json
 |
 |  execute(self, path, name, data, vdom=None, mkey=None, parameters=None)
 |      Execute is an action done on a running fortigate
 |      it is actually doing a post to the monitor part of the API
 |      we choose this name for clarity
 |
 |      :param path: first part of the Fortios API URL like
 |      :param name: https://myfgt:8040/api/v2/monitor/<path>/<name>
 |      :param data: json containing the param/values of the object to be set
 |      :param mkey: when the cmdb object have a subtable mkey represent the subobject.
 |                   It is optionnal at creation the code will find the mkey name for you.
 |      :param vdom: the vdom on which you want to apply config or global for global settings
 |      :param parameters: Add on parameters understood by the API call can be "&select=" for example
 |      :return:
 |          A formatted json with the last response from the API
 |
 |  formatresponse(self, res, vdom=None)
 |
 |  get(self, path, name, vdom=None, mkey=None, parameters=None)
 |      Execute a GET on the cmdb (i.e. configuration part) of the Fortios API
 |
 |      :param path: first part of the Fortios API URL like
 |      :param name: https://myfgt:8040/api/v2/cmdb/<path>/<name>
 |      :param mkey: when the cmdb object have a subtable mkey represent the subobject.
 |                   It is optionnal at creation the code will find the mkey name for you.
 |      :param vdom: the vdom on which you want to apply config or global for global settings
 |      :param parameters: Add on parameters understood by the API call can be "&select=" for example
 |      :return:
 |          A formatted json with the last response from the API, values are in return['results']
 |
 |  get_mkey(self, path, name, data, vdom=None)
 |      :param path:
 |      :param name:
 |      :param data:
 |      :param vdom:
 |      :return:
 |
 |  get_mkeyname(self, path, name, vdom=None)
 |      :param path:
 |      :param name:
 |      :param vdom:
 |      :return:
 |
 |  get_name_path_dict(self, vdom=None)
 |
 |  get_version(self)
 |      :return:
 |
 |  https(self, status)
 |      Allow to use http or https (default).
 |      HTTP is necessary to use the API on unlicensed/trial Fortigates
 |
 |      :param status: 'on' to use https to connect to API, anything else will http
 |      :return:
 |
 |  license(self, vdom='root')
 |      license check and update:
 |       - GET /api/v2/monitor/license/status
 |       - If pending (exec update-now) with FortiGuard if invalid
 |         POST api/v2/monitor/system/fortiguard/update and do the GET again
 |        Convinient when Fortigate starts and license validity takes time.
 |
 |      :param vdom: root by default, can be global to do a global check
 |      :return:
 |          True if license is valid at the end of the process
 |
 |  login(self, host, username, password, verify=True, cert=None, timeout=12, vdom='global')
 |      :param host:
 |      :param username:
 |      :param password:
 |      :param verify:
 |      :param cert:
 |      :param timeout:
 |      :param vdom:
 |      :return:
 |
 |  logout(self)
 |      :return:
 |
 |  mon_url(self, path, name, vdom=None, mkey=None)
 |
 |  monitor(self, path, name, vdom=None, mkey=None, parameters=None)
 |      Execute a GET on the montioring part of the Fortios API
 |      :param path: first part of the Fortios API URL like
 |      :param name: https://myfgt:8040/api/v2/monitor/<path>/<name>
 |      :param mkey: when the cmdb object have a subtable mkey represent the subobject.
 |                   It is optionnal at creation the code will find the mkey name for you.
 |      :param vdom: the vdom on which you want to apply config or global for global settings
 |      :param parameters: Add on parameters understood by the API call can be "&select=" for example
 |      :return:
 |          A formatted json with the last response from the API, values are in return['results']
 |
 |  move(self, path, name, vdom=None, mkey=None, where=None, reference_key=None, parameters={})
 |      Move an object in a cmdb table (firewall/policies for example).
 |      Usefull for reordering too
 |      :param path: first part of the Fortios API URL like
 |      :param name: https://myfgt:8040/api/v2/cmdb/<path>/<name>
 |      :param data: json containing the param/values of the object to be set
 |      :param mkey: when the cmdb object have a subtable mkey represent the subobject.
 |                   It is optionnal at creation the code will find the mkey name for you.
 |      :param vdom: the vdom on which you want to apply config or global for global settings
 |      :param parameters: Add on parameters understood by the API call can be "&select=" for example
 |      :param where: the destination mkey in the table
 |      :param reference_key: the origin mkey in the table
 |      :return:
 |          A formatted json with the last response from the API
 |
 |  post(self, path, name, data, vdom=None, mkey=None, parameters=None)
 |       Execute a REST POST on the API. It will fail if the targeted object already exist.
 |       When post to the upper name/path the mkey is in the data.
 |       So we can ensure the data set is correctly filled in case mkey is passed.
 |
 |      :param path: first part of the Fortios API URL like
 |      :param name: https://myfgt:8040/api/v2/cmdb/<path>/<name>
 |      :param data: json containing the param/values of the object to be set
 |      :param mkey: when the cmdb object have a subtable mkey represent the subobject.
 |                   It is optionnal at creation the code will find the mkey name for you.
 |      :param vdom: the vdom on which you want to apply config or global for global settings
 |      :param parameters: Add on parameters understood by the API call can be "&select=" for example
 |      :return:
 |          A formatted json with the last response from the API
 |
 |  put(self, path, name, vdom=None, mkey=None, parameters=None, data=None)
 |      Execute a REST PUT on the specified object with parameters in the data field as
 |      a json formatted field
 |
 |      :param path: first part of the Fortios API URL like
 |      :param name: https://myfgt:8040/api/v2/cmdb/<path>/<name>
 |      :param data: json containing the param/values of the object to be set
 |      :param mkey: when the cmdb object have a subtable mkey represent the subobject.
 |                   It is optionnal at creation the code will find the mkey name for you.
 |      :param vdom: the vdom on which you want to apply config or global for global settings
 |      :param parameters: Add on parameters understood by the API call can be "&select=" for example
 |      :return:
 |          A formatted json with the last response from the API
 |
 |  schema(self, path, name, vdom=None)
 |
 |  set(self, path, name, data, mkey=None, vdom=None, parameters=None)
 |      Fortios API definition is at https://fndn.fortinet.net
 |      Function targeting config management. You pass the data of the part of cmdb you want to be set and the function
 |      will try POST and PUT to ensure your modification go through.
 |
 |      :param path: first part of the Fortios API URL like
 |      :param name: https://myfgt:8040/api/v2/cmdb/<path>/<name>
 |      :param data: json containing the param/values of the object to be set
 |      :param mkey: when the cmdb object have a subtable mkey represent the subobject.
 |                   It is optionnal at creation the code will find the mkey name for you.
 |      :param vdom: the vdom on which you want to apply config or global for global settings
 |      :param parameters: Add on parameters understood by the API call can be "&select=" for example
 |      :return:
 |          A formatted json with the last response from the API
 |
 |  setoverlayconfig(self, yamltree, vdom=None)
 |      take a yaml tree with
 |      name:
 |          path:
 |              mkey:
 |      structure and recursively set the values.
 |      create a copy to only keep the leaf as node (table firewall rules etc
 |      Split the tree in 2 yaml objects and iterates)
 |      Update the higher level, up to tables as those config parameters may influence which param are allowed
 |      in the level 3 table
 |      :param yamltree: a yaml formatted string of the differents part of CMDB to be changed
 |      :param vdom: (optionnal) default is root, can use vdom=global to swtich to global settings.
 |      :return:
 |
 |  tokenlogin(self, host, apitoken, verify=True, cert=None, timeout=12, vdom='global')
 |      if using apitoken method then login/passwd will be disabled
 |
 |      :param host:
 |      :param apitoken:
 |      :param verify:
 |      :param cert:
 |      :param timeout:
 |      :param vdom:
 |      :return:
 |
 |  update_cookie(self)
 |
 |  upload(self, path, name, vdom=None, mkey=None, parameters=None, data=None, files=None)
 |      Upload a file (refer to the monitoring part), used for license, config, certificates etc.. uploads.
 |
 |      :param path: first part of the Fortios API URL like
 |      :param name: https://myfgt:8040/api/v2/cmdb/<path>/<name>
 |      :param data: json containing the param/values of the object to be set
 |      :param mkey: when the cmdb object have a subtable mkey represent the subobject.
 |                   It is optionnal at creation the code will find the mkey name for you.
 |      :param vdom: the vdom on which you want to apply config or global for global settings
 |      :param parameters: Add on parameters understood by the API call can be "&select=" for example
 |      :param files: the file to be uploaded
 |      :return:
 |          A formatted json with the last response from the API
 |
 |  ----------------------------------------------------------------------
 |  Static methods defined here:
 |
 |  debug(status)
 |      Set the debug to on to have all the debug information from the library
 |      You should add logging.getLogger('fortiosapi') to your log handler
 |
 |      :param status: on to set the log level to DEBUG
 |      :return:
 |          None
 |
 |  logging(response)
 |
 |  ssh(cmds, host, user, password=None, port=22)
 |      DEPRECATED use paramiko directly.
 |      Send a multi line string via ssh to the fortigate
 |
 |      :param cmds: multi line string with the Fortigate config cli
 |      :param host: ip/hostname of the fortigate interface
 |      :param user/password: fortigate admin user and password
 |      :param port: port 22 if not set or a port on which fortigate listen for ssh commands.
 |      :return:
 |          The output of the console commands and raise exception if failed
 |
 |  ----------------------------------------------------------------------
 |  Data descriptors defined here:
 |
 |  __dict__
 |      dictionary for instance variables
 |
 |  __weakref__
 |      list of weak references to the object