# BeaconAPI/ExecutionRPC

Both use threading for concurrent exectuion. They have their own respective managers that use the ETBConfig object to create the internal data structutes.

When using either API you can set the timeouts, and if you want to retry on an error. The structure for both is as follows:

RequestObject():
    object that wraps a request, it only contains the request information. It is agnostic of the target.
        APIRequest/RPCMethod

ClientChannelManager():
    an object that wraps a single connection, this object is the one that handles the error handeling and retries. You can set them on init, or use the ETBManager for this task.
    implements _is_valid_response and get_xxx_response.
        BeaconAPI/ExecutionJSONRPC

ETBManager():
    the manager that takes the etb_config and creates the associated ClientChannelManagers. You can init with timeout and retries. You should use this object for modules as the ETBConfig will be the only object needing an update when adding features. 
