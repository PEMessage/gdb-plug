import os
import traceback
import subprocess
import re
try:
    import gdb as gdb
    RUNING_IN_GDB = True
except ImportError:
    import mockgdb as gdb
    RUNING_IN_GDB = False


class PlugInitConfig(dict):
    """Store init config, and infer plug config based on init config"""

    def __init__(self, home=None, autoload=None, uri_format=None):
        self['home'] = self.first_not_none(
            os.getenv('GDB_PLUG_HOME'),
            home,
            os.path.expanduser('~/.config/gdb/plug')
        )

        self['autoload'] = self.first_not_none(
            os.getenv('GDB_PLUG_AUTOLOAD'),
            autoload,
            True
        )

        self['uri_format'] = self.first_not_none(
            uri_format,
            'https://git::@github.com/{}.git'
        )

    @staticmethod
    def is_local_plug(repo):
        # 1. start with windows drive name E.g: 'C:' 'D:'
        # 2. start with uinx path name E.g: '%' '/home' '~/.config'
        return bool(re.match(r'^[a-zA-Z]:|^[%~/]', repo))

    @staticmethod
    def first_not_none(*args):
        return next((x for x in args if x is not None), None)

    def infer_name(self, repo):
        bn = repo.split('/')[-1]  # basename
        # remove tail .git
        bn = bn[:-4] if bn.endswith('.git') else bn
        return bn

    def infer_directory_uri(self, name, repo):
        # 1. Local dir(only directory)
        if self.is_local_plug(repo):
            return {
                'uri': None,
                'directory': repo.rstrip('/')
            }
        # 2. Remote repo(directort, uri)
        if ':' in repo:
            uri = repo
        else:
            if '/' not in repo:
                raise ValueError(f"Invalid argument: {repo}")
            uri = self["uri_format"].format(repo)
        return {
            'uri': uri,
            'directory': os.path.join(self["home"], name)
        }

    @staticmethod
    def infer_bool_bygroup(value, groups):
        if isinstance(value, bool):
            return value
        elif isinstance(value, int):
            return bool(value)
        elif isinstance(value, str):
            value = value.split(',')
            ret = False
            for x in value:
                if x.lower() in ["all", "true", "1"] + groups:
                    ret = True
                if x.lower() in ["none", "false", "0"] + ["-"+group for group in groups]:
                    ret = False
            return ret
        else:
            return False

    def infer_kv(self, key, value):
        return value if value is not None else self[key]

    def infer_config(self, repo, name=None, autoload=None, groups=None):
        groups = groups or []
        name = name or self.infer_name(repo)
        config = {
            'name': name,
            'repo': repo,
            'autoload': self.infer_bool_bygroup(autoload or self["autoload"], [name] + groups)
        }
        config_segment = self.infer_directory_uri(name, repo)
        config.update(config_segment)
        return config


class PlugManager:
    """Non-singleton plugin manager implementation"""

    def __init__(self, **kargs):
        self.init = PlugInitConfig(**kargs)

        self.plug_infos = {}
        os.makedirs(self.init["home"], exist_ok=True)

    def plug(self, repo, **kargs):
        """Register a plugin repository"""
        config = self.init.infer_config(repo, **kargs)
        self.plug_infos[config['name']] = config
        return self

    def update(self, names=None):
        """Update specified plugins or all plugins"""
        names = names or list(self.plug_infos.keys())

        for name in names:
            if name not in self.plug_infos:
                print(f"Plugin not registered: {name}")
                continue

            plugin = self.plug_infos[name]
            repo_dir = plugin['directory']
            repo_uri = plugin['uri']

            if repo_uri is None:
                print("Not a remote repo, do nothing...")
                return

            if not os.path.exists(repo_dir):
                print(f"Installing {name}...")
                result = subprocess.run(
                    ['git', 'clone', repo_uri, repo_dir],
                    # capture_output=True,
                    # text=True
                )
                if result.returncode != 0:
                    print(f"Failed to install {name}: {result.stderr}")
                    continue
                print(f"Installed {name}")
            else:
                print(f"Updating {name}...")
                result = subprocess.run(
                    ['git', '-C', repo_dir, 'pull'],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    print(f"Failed to update {name}: {result.stderr}")
                    continue
                print(f"Updated {name}")

    def end(self):
        """Load specified plugins or all autoload plugins"""
        # Load all autoload plugins, or define in GDB_PLUG_AUTOLOAD
        names_to_load = [
            name
            for name, plugin in self.plug_infos.items()
            if
            plugin.get('autoload')
        ]
        print(names_to_load)

        for name in names_to_load:
            self.load(name)

    def load(self, name):
        """Load a plugin by name"""

        plugin = self.plug_infos.get(name)
        if not plugin:
            print(f"Plugin not registered: {name}")
            return False

        plugin_dir = plugin['directory']
        if not os.path.exists(plugin_dir):
            print(f"Plugin not installed: {name}. Run 'Plug update' to install.")
            return False

        # Look for initialization files
        init_files = [
            os.path.join(plugin_dir, f"{name}.py"),
            os.path.join(plugin_dir, f"{name}.gdb"),
            os.path.join(plugin_dir, "main.py"),
            os.path.join(plugin_dir, "main.gdb"),
            os.path.join(plugin_dir, ".gdbinit"),
            os.path.join(plugin_dir, f"gdbinit-{name.lower()}.py"),  # for example gdbinit-gep.py # noqa: E501
        ]

        loaded = False
        for init_file in init_files:
            if os.path.exists(init_file):
                try:
                    gdb.execute(f"source {init_file}")
                    print(f"Loaded plugin: {name} from {init_file}")
                    loaded = True
                    break
                except Exception as e:
                    print(f"Failed to load {init_file}: {str(e)}")
                    traceback.print_exc()

        if not loaded:
            print(f"No valid initialization file found for plugin: {name}")
            return False

        return True

    def list(self):
        """Return information about registered plugins"""
        return [
            {
                'name': name,
                'repo': plugin['repo'],
                'directory': plugin['directory'],
                'autoload': plugin.get('autoload', True),
                'installed': os.path.exists(plugin['directory'])
            }
            for name, plugin in self.plug_infos.items()
        ]


class Plug:
    """Singleton wrapper for PlugManager with clean API"""
    _instance = None

    @classmethod
    def begin(cls, *args, **kwargs):
        """Initialize the plugin manager with configuration"""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._manager = PlugManager(*args, **kwargs)
        return cls._instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._manager = PlugManager()
        return cls._instance

    @classmethod
    def end(cls, *args, **kwargs):
        """Alias for load() to maintain compatibility"""
        return cls()._manager.end(*args, **kwargs)

    @classmethod
    def plug(cls, *args, **kwargs):
        """Register a plugin repository"""
        return cls()._manager.plug(*args, **kwargs)

    @classmethod
    def update(cls, *args, **kwargs):
        """Update specified plugins or all plugins"""
        return cls()._manager.update(*args, **kwargs)

    @classmethod
    def load(cls, *args, **kwargs):
        """Load specified plugins or all auto-load plugins"""
        return cls()._manager.load(*args, **kwargs)

    @classmethod
    def list(cls, *args, **kwargs):
        """List all registered plugins"""
        return cls()._manager.list(*args, **kwargs)


if RUNING_IN_GDB is True:
    class PlugCommand(gdb.Command):
        """GDB command interface for plugin management"""

        def __init__(self):
            super(PlugCommand, self).__init__(
                "Plug", gdb.COMMAND_USER, prefix=True)

        def invoke(self, arg, from_tty):
            args = gdb.string_to_argv(arg)
            if not args:
                print("Usage: Plug <subcommand> [args...]")
                print("Available subcommands: install, update, list, load")
                return

            subcommand = args[0].lower()

            if subcommand == "update":
                self._update(*args[1:])
            elif subcommand == "list":
                self._list(*args[1:])
            elif subcommand == "load":
                self._load(*args[1:])
            else:
                print(f"Unknown subcommand: {subcommand}")

        def _update(self, *args, **kargs):
            """Update specified plugins or all plugins"""
            Plug.update(*args, **kargs)

        def _list(self, *args, **kargs):
            """List registered plugins"""
            print(Plug.list(*args, **kargs))

        def _load(self, *args, **kargs):
            """Load specific plugins"""
            Plug.load(*args, **kargs)

        def complete(self, text, word):
            """Provide tab completion for subcommands and plugin names"""
            # print(f"\ntext is '{text}'")
            # print(f"\nword is '{word}'")
            parts = gdb.string_to_argv(text)
            # extra = 1 if word is None else 0
            pword = word or ''

            subcmd = ['update', 'list', 'load']
            if parts[0] in subcmd:
                return [plug['name'] for plug in Plug.list() if plug['name'].startswith(pword)]
            else:
                return [cmd for cmd in ['update', 'list', 'load'] if cmd.startswith(pword)]


if __name__ == '__main__':
    if RUNING_IN_GDB is True:
        # Register the command
        PlugCommand()
    else:
        pass

# Example usage in .gdbinit:
# Plug.plug("hugsy/gef")  # Autoload-load by default
# Plug.plug("cyrus-and/gdb-dashboard", autoload=False)  # Manual load
# Plug.load()  # Load all autoload-load plugins
