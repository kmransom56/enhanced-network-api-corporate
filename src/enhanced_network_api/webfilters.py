
class WebFiltersModule:
    """Module for managing web and URL filters in FortiManager."""

    def __init__(self, session):
        self.session = session

    def get_webfilter_profiles(self, adom="root"):
        """Retrieves all web filter profiles."""
        params = [{
            "url": f"/pm/config/adom/{adom}/webfilter/profile"
        }]
        return self.session.post("get", params)

    def get_urlfilter_lists(self, adom="root"):
        """Retrieves all URL filter lists."""
        params = [{
            "url": f"/pm/config/adom/{adom}/webfilter/urlfilter"
        }]
        return self.session.post("get", params)
