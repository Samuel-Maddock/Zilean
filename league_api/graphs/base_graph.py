class Graph:
    def __init__(self, api_watcher, region):
        self.api_watcher = api_watcher
        self.region = region

    def render(self):
        pass

    def set_region(self, region):
        self.region = region