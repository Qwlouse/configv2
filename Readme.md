# Playground for configuration System V2

This is a prototype that I have been playing with for reworking the Sacred configuration system.
None of this is meant to be final in any way, just a playground to explore ideas.
The code is not documented, but I'll describe the main idea here, and the tests should also give a good idea of how it behaves.

The general idea is to have the configuration collect all updates by recording entries `(path, value, priority)` instead of directly assigning them.
Evaluating the configuration then resolves all these assignments and turns them into a nested dict structure of config values.

This has several advantages:
  * Unified mechanism for resolving priorities
  * Easy tracking of metadata and the source of a particular value
  * Support for complex assignments that target more than one value like `layers.*.size=10` (not implemented yet)
  * Config scopes can be implemented py partial evaluation of of config values on demand (see below)
   
 
### Config Scopes
Supporting config-scopes is the most tricky part, because it has to resolve some config-updates during the execution of other updates.
The general idea I am exploring here is to collect all assignments similar to commits to a database, but not evaluate them directly.
Instead they are collected starting from high-priority and proceeding to lower priorities.
That means first all the commandline updates, then named configs and finally the default config.
At every level each config value can be evaluated on demand, so that other that depend on it can use it.

Take for example the config updates `batch_size=32` and `layers.*.size=100`.
This will lead to two entries in the configuration.
  * `('batch_size', 32, CLI)`
  * `('layers.*.size', 100, CLI)`
  
Lets say we have the following default config scope:
```python
@config
def default_config(cfg):
    cfg.batch_size = 128
    cfg.learn_rate = 0.01 * cfg.batch_size
    layers = {
        'hidden1': {'size': 200, 'act': 'elu'},
        'hidden2': {'size': 300, 'act': 'elu'},
    }
    total_units = cfg.layers.hidden1.size + cfg.layers.layers.hidden2.size
```
* The first line would yield another entry `('batch_size', 128, DEFAULT)`.
* For the second line we need to evaluate the `batch_size` entry which resolves to 32 because CLI has higher priority.
  The entry for `learn_rate` then becomes `('learn_rate', 0.32, DEFAULT)`.
* The next assignment yields an entry for `layers` which contains the dictionary.
* And for the final assignment we evaluate `layers.hidden1.size` and `layers.hidden2.size`.
  Both are overridden by the matching entry `('layers.*.size', 100, CLI)`.
  The final entry thus becomes `('total_units', 200, DEFAULT)`
  

### Priorities
Each entry has a priority. ATM, I can think of the following priorities:

1. Implicit
    * implicit values
    * information about usage in captured functions etc.
2. Config Defaults
    * config dicts
    * config files
    * config scopes
3. Internal
    * `seed`
    * `_id`
    * run directory?
4. Named Configs
    * @named_config
    * with config.file
5. Run Args
    * passed to run()
6. Commandline
    * from the commandline

The entries are collected starting from the highest priority first. 
That means named configs have access to CLI updates but not to default values, while the defaults have access to everything. 
The "Implicit" priority is just a means for collecting some meta-information like usage, and for resolving ambiguities (`layers[1]` could target a list or a dict with int keys).

