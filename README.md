# GDBPlug

A minimalist plugin manager for GDB, inspired by vim-plug.

## Features

- Simple plugin declaration syntax
- Automatic installation and updating of plugins from GitHub
- Support for both Python (.py) and GDB script (.gdb) plugins
- Autoload functionality

## Installation

1. Copy the code into your `~/.gdbinit` file

2. Alternatively, you can source it directly:

```bash
echo "source /path/to/gdb_plug.py" >> ~/.gdbinit
```

## Usage

### Basic Configuration

Add plugin declarations to your `.gdbinit`:

```python
# Initialize plugin manager
Plug.begin(autoload=true)

# Register plugins
Plug.plug("hugsy/gef")  # Autoload by default
Plug.plug("cyrus-and/gdb-dashboard", autoload=True)  # Manual load

# Load all autoload plugins
Plug.end()
```

### Commands

- `Plug update [name...]` - Update all or specified plugins
- `Plug list` - List registered plugins
- `Plug load <name>` - Load a specific plugin

### Plugin Configuration Options

When registering a plugin with `Plug.plug()`:

- `repo`: GitHub repository (required, format: "user/repo")
- `name`: Plugin name (defaults to repository name)
- `directory`: Installation directory (defaults to `~/.config/gdb/plug/<name>`)
- `autoload`: Whether to load automatically (default: True)

## Environment Variables

- `GDB_PLUG_HOME`: Custom plugin installation directory (default: `~/.config/gdb/plug`)

## Example Workflow

1. Register plugins in your `.gdbinit`:

```python
Plug.begin()
Plug.plug("hugsy/gef")
Plug.plug("cyrus-and/gdb-dashboard", autoload=False)
Plug.end()
```

2. Install the plugins:

```
(gdb) Plug update
```

3. Manually load a plugin (if not autoloaded):

```
(gdb) Plug load gdb-dashboard
```

4. List installed plugins:

```
(gdb) Plug list
```

## Supported Initialization Files

When loading a plugin, the manager looks for these files in order:

1. `<plugin-name>.py`
2. `<plugin-name>.gdb`
3. `main.py`
4. `main.gdb`
5. `.gdbinit`
6. `gdbinit-<plugin-name>.py` (e.g., `gdbinit-gep.py`)


## License

GPL

## Inspiration

This project was inspired by vim-plug's simplicity and effectiveness for managing Vim plugins.

## Contributing

Contributions are welcome! Please open issues or pull requests for any improvements, especially to the `PlugCommand.complete` function as noted in the source.
